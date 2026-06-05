from src.network_factory import SUPPORTED_TOPOLOGIES, create_network
from src.simulation_engine import SIRSimulation, compute_metrics
from src.visualization import compare_topologies, launch_interactive_simulation


RANDOM_SEED = 42
N = 500
INFECTION_BETA = 0.05
RECOVERY_GAMMA = 0.01
TIME_STEPS = 365
TARGET_AVG_DEGREE = 8
WEIGHTED_MODE = False
START_DAY_MODE = "random"
START_DAY = 300


def run_topology(topology_type: str) -> dict:
    graph = create_network(
        topology_type=topology_type,
        n=N,
        target_avg_degree=TARGET_AVG_DEGREE,
        seed=RANDOM_SEED,
        weighted_mode=WEIGHTED_MODE,
    )

    simulation = SIRSimulation(
        graph=graph,
        beta=INFECTION_BETA,
        gamma_base=RECOVERY_GAMMA,
        time_steps=TIME_STEPS,
        random_seed=RANDOM_SEED,
        start_day_mode=START_DAY_MODE,
        start_day=START_DAY,
    )

    history = simulation.run()
    return {"history": history, "metrics": compute_metrics(history)}


def main() -> None:
    launch_interactive_simulation(
        {
            "topology": "erdos_renyi",
            "n": N,
            "beta": INFECTION_BETA,
            "gamma": RECOVERY_GAMMA,
            "time_steps": TIME_STEPS,
            "degree": TARGET_AVG_DEGREE,
            "seed": RANDOM_SEED,
            "weighted": WEIGHTED_MODE,
            "start_day_mode": START_DAY_MODE,
            "start_day": START_DAY,
        }
    )


def run_batch() -> None:
    results = {}
    for topology in SUPPORTED_TOPOLOGIES:
        results[topology] = run_topology(topology)

    compare_topologies(results, save_path="sir_topology_comparison.png")

    print("Simulation completed. Summary metrics:")
    for topology, payload in results.items():
        metrics = payload["metrics"]
        print(
            f"- {topology}: peak_infected={metrics['peak_infected']}, "
            f"peak_day={metrics['peak_day']}, "
            f"final_recovered={metrics['final_recovered']}, "
            f"duration_days={metrics['duration_days']}"
        )
    print("Saved plot: sir_topology_comparison.png")


if __name__ == "__main__":
    main()
