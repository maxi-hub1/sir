import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider

from src.network_factory import SUPPORTED_TOPOLOGIES, create_network
from src.simulation_engine import INFECTED, RECOVERED, SUSCEPTIBLE, SIRSimulation


def plot_epidemic_curves(history: dict, title: str, save_path: str | None = None) -> None:
	fig, ax = plt.subplots(figsize=(10, 5))
	ax.plot(history["time"], history["S"], label="Susceptible", color="#1f77b4")
	ax.plot(history["time"], history["I"], label="Infected", color="#d62728")
	ax.plot(history["time"], history["R"], label="Recovered", color="#2ca02c")

	ax.set_title(title)
	ax.set_xlabel("Day")
	ax.set_ylabel("Agents")
	ax.legend()
	ax.grid(alpha=0.2)
	fig.tight_layout()

	if save_path:
		fig.savefig(save_path, dpi=150)
	plt.close(fig)


def compare_topologies(results: dict, save_path: str | None = None) -> None:
	fig, axes = plt.subplots(1, len(results), figsize=(6 * len(results), 5), sharey=True)

	if len(results) == 1:
		axes = [axes]

	for ax, (topology, payload) in zip(axes, results.items()):
		history = payload["history"]
		ax.plot(history["time"], history["S"], label="S", color="#1f77b4")
		ax.plot(history["time"], history["I"], label="I", color="#d62728")
		ax.plot(history["time"], history["R"], label="R", color="#2ca02c")
		ax.set_title(topology)
		ax.set_xlabel("Day")
		ax.grid(alpha=0.2)

	axes[0].set_ylabel("Agents")
	axes[0].legend(loc="upper right")
	fig.tight_layout()

	if save_path:
		fig.savefig(save_path, dpi=150)
	plt.close(fig)


def launch_interactive_simulation(default_config: dict | None = None) -> None:
	config = {
		"topology": "erdos_renyi",
		"n": 200,
		"beta": 0.05,
		"gamma": 0.01,
		"time_steps": 180,
		"degree": 8,
		"seed": 42,
		"weighted": False,
		"start_day_mode": "random",
		"start_day": 30,
	}
	if default_config:
		config.update(default_config)

	fig = plt.figure(figsize=(16, 9))
	ax_net = fig.add_axes([0.05, 0.12, 0.50, 0.80])
	ax_curve = fig.add_axes([0.58, 0.55, 0.40, 0.35])

	ax_topology = fig.add_axes([0.58, 0.42, 0.16, 0.10])
	ax_weighted = fig.add_axes([0.76, 0.42, 0.16, 0.10])
	ax_play = fig.add_axes([0.58, 0.36, 0.12, 0.05])
	ax_rerun = fig.add_axes([0.72, 0.36, 0.12, 0.05])

	ax_day = fig.add_axes([0.58, 0.30, 0.40, 0.03])
	ax_n = fig.add_axes([0.58, 0.24, 0.40, 0.03])
	ax_beta = fig.add_axes([0.58, 0.20, 0.40, 0.03])
	ax_gamma = fig.add_axes([0.58, 0.16, 0.40, 0.03])
	ax_steps = fig.add_axes([0.58, 0.12, 0.40, 0.03])
	ax_degree = fig.add_axes([0.58, 0.08, 0.40, 0.03])
	ax_seed = fig.add_axes([0.58, 0.04, 0.40, 0.03])

	topology_buttons = RadioButtons(ax_topology, SUPPORTED_TOPOLOGIES)
	weighted_check = CheckButtons(ax_weighted, ["Weighted edges"], [config["weighted"]])
	play_button = Button(ax_play, "Play/Pause")
	rerun_button = Button(ax_rerun, "Run")

	day_slider = Slider(ax_day, "Day", 0, max(1, config["time_steps"] - 1), valinit=0, valstep=1)
	n_slider = Slider(ax_n, "N", 30, 600, valinit=config["n"], valstep=1)
	beta_slider = Slider(ax_beta, "Beta", 0.001, 1.0, valinit=config["beta"])
	gamma_slider = Slider(ax_gamma, "Gamma", 0.001, 1.0, valinit=config["gamma"])
	steps_slider = Slider(ax_steps, "Days", 30, 365, valinit=config["time_steps"], valstep=1)
	degree_slider = Slider(ax_degree, "Avg degree", 2, 30, valinit=config["degree"], valstep=1)
	seed_slider = Slider(ax_seed, "Seed", 0, 9999, valinit=config["seed"], valstep=1)

	state = {
		"graph": None,
		"history": None,
		"positions": None,
		"node_order": None,
		"topology": config["topology"],
		"playing": False,
		"anim": None,
	}

	color_map = {
		SUSCEPTIBLE: "#1f77b4",
		INFECTED: "#d62728",
		RECOVERED: "#2ca02c",
	}

	def _build_simulation() -> None:
		n = int(n_slider.val)
		beta = float(beta_slider.val)
		gamma = float(gamma_slider.val)
		time_steps = int(steps_slider.val)
		degree = float(degree_slider.val)
		seed = int(seed_slider.val)
		weighted = weighted_check.get_status()[0]

		graph = create_network(
			topology_type=state["topology"],
			n=n,
			target_avg_degree=degree,
			seed=seed,
			weighted_mode=weighted,
		)

		sim = SIRSimulation(
			graph=graph,
			beta=beta,
			gamma_base=gamma,
			time_steps=time_steps,
			random_seed=seed,
			start_day_mode=config["start_day_mode"],
			start_day=config["start_day"],
			record_node_states=True,
		)
		history = sim.run()

		state["graph"] = graph
		state["history"] = history
		state["positions"] = nx.spring_layout(graph, seed=seed)
		state["node_order"] = list(graph.nodes)

		day_slider.valmax = max(1, len(history["time"]) - 1)
		day_slider.ax.set_xlim(day_slider.valmin, day_slider.valmax)
		day_slider.set_val(0)

	def _draw(day: int) -> None:
		if state["graph"] is None or state["history"] is None:
			return

		history = state["history"]
		node_states = history["node_states"][day]
		nodes = state["node_order"]
		colors = [color_map.get(node_states[node], "#7f7f7f") for node in nodes]

		ax_net.clear()
		nx.draw_networkx_edges(
			state["graph"],
			pos=state["positions"],
			ax=ax_net,
			alpha=0.12,
			width=0.4,
			edge_color="#666666",
		)
		nx.draw_networkx_nodes(
			state["graph"],
			pos=state["positions"],
			nodelist=nodes,
			node_color=colors,
			node_size=22,
			ax=ax_net,
		)
		ax_net.set_title(
			f"{state['topology']} | day={day} | S={history['S'][day]} I={history['I'][day]} R={history['R'][day]}"
		)
		ax_net.set_axis_off()

		ax_curve.clear()
		ax_curve.plot(history["time"], history["S"], color="#1f77b4", label="S")
		ax_curve.plot(history["time"], history["I"], color="#d62728", label="I")
		ax_curve.plot(history["time"], history["R"], color="#2ca02c", label="R")
		ax_curve.axvline(day, color="#111111", linestyle="--", linewidth=1)
		ax_curve.set_title("Compartment counts")
		ax_curve.set_xlabel("Day")
		ax_curve.set_ylabel("Agents")
		ax_curve.grid(alpha=0.2)
		ax_curve.legend(loc="upper right")

		fig.canvas.draw_idle()

	def _on_day_change(val: float) -> None:
		_draw(int(val))

	def _toggle_play(_event) -> None:
		state["playing"] = not state["playing"]

	def _on_rerun(_event) -> None:
		state["playing"] = False
		_build_simulation()
		_draw(0)

	def _on_topology_change(label: str) -> None:
		state["topology"] = label
		_on_rerun(None)

	def _advance_frame(_frame):
		if not state["playing"]:
			return
		current = int(day_slider.val)
		if current >= int(day_slider.valmax):
			state["playing"] = False
			return
		day_slider.set_val(current + 1)

	topology_buttons.on_clicked(_on_topology_change)
	weighted_check.on_clicked(lambda _: _on_rerun(None))
	play_button.on_clicked(_toggle_play)
	rerun_button.on_clicked(_on_rerun)
	day_slider.on_changed(_on_day_change)

	state["anim"] = FuncAnimation(fig, _advance_frame, interval=120, cache_frame_data=False)

	_build_simulation()
	_draw(0)
	plt.show()
