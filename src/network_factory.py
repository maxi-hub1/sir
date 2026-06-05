import random

import networkx as nx


SUPPORTED_TOPOLOGIES = ("erdos_renyi", "watts_strogatz", "barabasi_albert")


def _clamp(value: float, lower: float, upper: float) -> float:
	return max(lower, min(value, upper))


def _coerce_ws_degree(target_avg_degree: float, n: int) -> int:
	k = int(round(target_avg_degree))
	k = max(2, min(k, n - 1))
	if k % 2 != 0:
		k -= 1
	if k < 2:
		k = 2
	return k


def _coerce_ba_m(target_avg_degree: float, n: int) -> int:
	m = int(round(target_avg_degree / 2.0))
	return max(1, min(m, n - 1))


def create_erdos_renyi_network(n: int, target_avg_degree: float, seed: int) -> nx.Graph:
	p = _clamp(target_avg_degree / max(1, n - 1), 0.0, 1.0)
	return nx.erdos_renyi_graph(n=n, p=p, seed=seed)


def create_watts_strogatz_network(
	n: int, target_avg_degree: float, seed: int, rewire_probability: float = 0.1
) -> nx.Graph:
	k = _coerce_ws_degree(target_avg_degree=target_avg_degree, n=n)
	return nx.watts_strogatz_graph(n=n, k=k, p=rewire_probability, seed=seed)


def create_barabasi_albert_network(n: int, target_avg_degree: float, seed: int) -> nx.Graph:
	m = _coerce_ba_m(target_avg_degree=target_avg_degree, n=n)
	return nx.barabasi_albert_graph(n=n, m=m, seed=seed)


def assign_edge_weights(graph: nx.Graph, weighted_mode: bool, rng: random.Random) -> None:
	for source, target in graph.edges:
		if weighted_mode:
			encounter_days = rng.randint(1, 365)
			weight = encounter_days / 365.0
		else:
			weight = 1.0
		graph[source][target]["weight"] = weight


def create_network(
	topology_type: str,
	n: int,
	target_avg_degree: float,
	seed: int,
	weighted_mode: bool,
) -> nx.Graph:
	if topology_type not in SUPPORTED_TOPOLOGIES:
		raise ValueError(
			f"Unsupported topology '{topology_type}'. Expected one of {SUPPORTED_TOPOLOGIES}."
		)

	if topology_type == "erdos_renyi":
		graph = create_erdos_renyi_network(n=n, target_avg_degree=target_avg_degree, seed=seed)
	elif topology_type == "watts_strogatz":
		graph = create_watts_strogatz_network(n=n, target_avg_degree=target_avg_degree, seed=seed)
	else:
		graph = create_barabasi_albert_network(n=n, target_avg_degree=target_avg_degree, seed=seed)

	rng = random.Random(seed + 17)
	assign_edge_weights(graph=graph, weighted_mode=weighted_mode, rng=rng)
	return graph