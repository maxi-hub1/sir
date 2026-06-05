import random
from dataclasses import dataclass

import networkx as nx


SUSCEPTIBLE = "S"
INFECTED = "I"
RECOVERED = "R"


@dataclass
class SimulationResult:
	history: dict
	metrics: dict


class SIRSimulation:
	def __init__(
		self,
		graph: nx.Graph,
		beta: float,
		gamma_base: float,
		time_steps: int,
		random_seed: int,
		start_day_mode: str = "random",
		start_day: int | None = None,
		record_node_states: bool = False,
	) -> None:
		self.graph = graph
		self.beta = beta
		self.gamma_base = gamma_base
		self.time_steps = time_steps
		self.rng = random.Random(random_seed)
		self.patient_zero_active = False
		self.record_node_states = record_node_states

		if start_day_mode not in {"random", "fixed"}:
			raise ValueError("start_day_mode must be 'random' or 'fixed'.")
		if start_day_mode == "fixed" and start_day is None:
			raise ValueError("start_day must be provided when start_day_mode is 'fixed'.")

		if start_day_mode == "random":
			self.start_day = self.rng.randint(0, max(0, time_steps - 1))
		else:
			self.start_day = max(0, min(start_day, max(0, time_steps - 1)))

		self.history = {"time": [], "season": [], "S": [], "I": [], "R": []}
		if self.record_node_states:
			self.history["node_states"] = []
		self._initialize_states()

	def _initialize_states(self) -> None:
		for node in self.graph.nodes:
			self.graph.nodes[node]["state"] = SUSCEPTIBLE
			self.graph.nodes[node]["next_state"] = SUSCEPTIBLE

	@staticmethod
	def _is_winter(day: int) -> bool:
		day_of_year = day % 366
		return 0 <= day_of_year <= 90 or 270 <= day_of_year <= 365

	def get_season(self, day: int) -> str:
		day_of_year = day % 366
		if 0 <= day_of_year <= 90 or 270 <= day_of_year <= 365:
			return "Winter"
		if 91 <= day_of_year <= 181:
			return "Spring"
		if 182 <= day_of_year <= 273:
			return "Summer"
		return "Autumn"

	def get_seasonal_gamma(self, day: int) -> float:
		gamma = self.gamma_base * (0.8 if self._is_winter(day) else 1.0)
		return max(0.0, min(gamma, 1.0))

	def _activate_patient_zero_if_needed(self, day: int) -> None:
		if self.patient_zero_active or day < self.start_day:
			return
		node = self.rng.choice(list(self.graph.nodes))
		self.graph.nodes[node]["state"] = INFECTED
		self.graph.nodes[node]["next_state"] = INFECTED
		self.patient_zero_active = True

	def _phase_1_evaluation(self, day: int) -> None:
		gamma_t = self.get_seasonal_gamma(day)

		for node in self.graph.nodes:
			state = self.graph.nodes[node]["state"]
			self.graph.nodes[node]["next_state"] = state

		for node in self.graph.nodes:
			if self.graph.nodes[node]["state"] != INFECTED:
				continue

			for neighbor in self.graph.neighbors(node):
				if self.graph.nodes[neighbor]["state"] != SUSCEPTIBLE:
					continue
				weight = float(self.graph[node][neighbor].get("weight", 1.0))
				p_inf = max(0.0, min(self.beta * weight, 1.0))
				if self.rng.random() <= p_inf:
					self.graph.nodes[neighbor]["next_state"] = INFECTED

			if self.rng.random() <= gamma_t:
				self.graph.nodes[node]["next_state"] = RECOVERED

	def _phase_2_commit(self) -> None:
		for node in self.graph.nodes:
			self.graph.nodes[node]["state"] = self.graph.nodes[node]["next_state"]

	def _record_history(self, day: int) -> None:
		s_count = 0
		i_count = 0
		r_count = 0

		for node in self.graph.nodes:
			state = self.graph.nodes[node]["state"]
			if state == SUSCEPTIBLE:
				s_count += 1
			elif state == INFECTED:
				i_count += 1
			else:
				r_count += 1

		self.history["time"].append(day)
		self.history["season"].append(self.get_season(day))
		self.history["S"].append(s_count)
		self.history["I"].append(i_count)
		self.history["R"].append(r_count)

		if self.record_node_states:
			node_snapshot = {
				node: self.graph.nodes[node]["state"] for node in self.graph.nodes
			}
			self.history["node_states"].append(node_snapshot)

	def step(self, day: int) -> None:
		self._activate_patient_zero_if_needed(day)
		self._phase_1_evaluation(day)
		self._phase_2_commit()
		self._record_history(day)

	def run(self) -> dict:
		for day in range(self.time_steps):
			self.step(day)
			if self.patient_zero_active and self.history["I"][-1] == 0:
				break
		return self.history


def compute_metrics(history: dict) -> dict:
	infected = history["I"]
	time = history["time"]

	peak_infected = max(infected) if infected else 0
	peak_index = infected.index(peak_infected) if infected else 0
	peak_day = time[peak_index] if time else 0
	final_recovered = history["R"][-1] if history["R"] else 0

	return {
		"peak_infected": peak_infected,
		"peak_day": peak_day,
		"final_recovered": final_recovered,
		"duration_days": len(time),
	}
