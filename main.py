# =============================================================================
# Network-based SIR simulation - single procedural script
# =============================================================================
# This script simulates the spread of an epidemic with the SIR model
# (Susceptible-Infected-Recovered) on three different network topologies.
# All three simulations run in parallel and can be controlled interactively
# with sliders, buttons, and a checkbox.
# =============================================================================


# =============================================================================
# SECTION 1: IMPORTS AND CONFIGURATION
# =============================================================================

# random: Simple pseudo-random number generator support.
# It is used through local Random(seed) instances so that the full simulation
# stays reproducible and does not depend on uncontrolled global random calls.
import random

# networkx: Library for graph creation, graph algorithms, and graph drawing.
# It provides built-in generators for Erdős-Rényi, Watts-Strogatz, and
# Barabási-Albert networks.
import networkx as nx

# matplotlib.pyplot: Main plotting interface used to create the window,
# figure, axes, and all plotted visual elements.
import matplotlib.pyplot as plt

# matplotlib.patches: Used to create colored legend entries for the S, I, R
# state colors shown in the visualization.
import matplotlib.patches as mpatches

# matplotlib.widgets: Provides the interactive UI controls such as sliders,
# buttons, and checkboxes.
import matplotlib.widgets as mwidgets

# FuncAnimation: Calls an update function repeatedly after a fixed interval,
# which is used here to advance the animation frame by frame.
from matplotlib.animation import FuncAnimation

# GridSpec: Provides a flexible subplot layout with multiple rows and columns.
# It is used here to place network views in the first row and epidemic curves
# in the second row.
from matplotlib.gridspec import GridSpec


# -- State constants -----------------------------------------------------------
STATE_S = "S"  # Susceptible: healthy and able to become infected
STATE_I = "I"  # Infected: currently infectious
STATE_R = "R"  # Recovered: immune and no longer infectious

# -- Color constants for node and curve visualization --------------------------
COLOR_S = "#1f77b4"  # Blue for susceptible
COLOR_I = "#d62728"  # Red for infected
COLOR_R = "#2ca02c"  # Green for recovered

# -- Holiday days in the year (1 = Jan 1, 365 = Dec 31) -----------------------
# These dates are used in extended mode to temporarily increase beta because
# contact frequency is assumed to be higher around holidays.
HOLIDAYS = [1, 52, 105, 155, 358, 359]

# Number of extra days around each holiday during which the holiday effect
# remains active.
HOLIDAY_BUFFER = 3

# -- Display names for the three network topologies ----------------------------
TOPOLOGY_NAMES = ["Erdos-Renyi", "Watts-Strogatz", "Barabasi-Albert"]

# -- English month abbreviations for the epidemic curve x-axis -----------------
MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# -- First calendar day of each month in a 365-day year -----------------------
MONTH_START_DAYS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]

# -- Global font size ----------------------------------------------------------
plt.rcParams["font.size"] = 9


# =============================================================================
# SECTION 2: GRAPH GENERATION
# =============================================================================


def create_erdos_renyi(n, avg_degree, seed):
    """
    Create an Erdős-Rényi random graph.

    Internally, this function computes the edge probability p from the desired
    average degree. In an Erdős-Rényi graph, every possible edge between two
    different nodes is included independently with the same probability p.

    The probability is derived from the target average degree with:

        p = avg_degree / (n - 1)

    This means that if a node has n - 1 possible neighbors, the expected number
    of actual neighbors becomes approximately avg_degree.

    Parameters:
        n (int):
            Total number of nodes in the graph.
        avg_degree (float):
            Desired average number of edges per node.
        seed (int):
            Seed forwarded to the NetworkX graph generator so that the graph
            structure is reproducible for the same input seed.

    Returns:
        nx.Graph:
            A generated Erdős-Rényi graph with n nodes and probability p.
    """
    # Compute the connection probability from the requested average degree.
    p = avg_degree / max(1, n - 1)

    # Clamp the probability to the valid interval [0, 1].
    p = max(0.0, min(1.0, p))

    return nx.erdos_renyi_graph(n, p, seed=seed)


def create_watts_strogatz(n, avg_degree, seed):
    """
    Create a Watts-Strogatz small-world graph.

    Internally, the function first converts the requested average degree into
    the parameter k of the Watts-Strogatz model. The model starts from a ring
    lattice in which each node is connected to its k nearest neighbors, then
    rewires edges with probability 0.1.

    The value k must be an even positive integer. This function therefore:
        1. Rounds avg_degree to the nearest integer.
        2. Enforces a minimum of 2.
        3. Adjusts k to be even.
        4. Clamps k so that it never exceeds n - 1.

    Parameters:
        n (int):
            Total number of nodes in the graph.
        avg_degree (float):
            Desired average degree. It is converted internally to the valid
            Watts-Strogatz parameter k.
        seed (int):
            Seed forwarded to the NetworkX graph generator so that the graph
            structure is reproducible for the same input seed.

    Returns:
        nx.Graph:
            A generated Watts-Strogatz graph with rewiring probability 0.1.
    """
    # Round to the nearest integer and enforce a minimum of 2.
    k = max(2, round(avg_degree))

    # k must be even in the Watts-Strogatz model.
    if k % 2 != 0:
        k += 1

    # k cannot exceed n - 1.
    k = min(k, n - 1)

    # Re-check evenness after clamping.
    if k % 2 != 0:
        k -= 1

    # Enforce the absolute minimum once more after all corrections.
    k = max(2, k)

    return nx.watts_strogatz_graph(n, k, 0.1, seed=seed)


def create_barabasi_albert(n, avg_degree, seed):
    """
    Create a Barabási-Albert scale-free graph.

    Internally, the function converts the requested average degree into the
    attachment parameter m. In the Barabási-Albert model, each new node is
    attached to m already existing nodes, with preference toward nodes that
    already have many connections.

    A common approximation is:
        m ≈ avg_degree / 2

    Therefore, this function:
        1. Computes m from avg_degree / 2.
        2. Rounds it to the nearest integer.
        3. Enforces a minimum of 1.
        4. Clamps it so that m never exceeds n - 1.

    Parameters:
        n (int):
            Total number of nodes in the graph.
        avg_degree (float):
            Desired average degree, internally converted into the attachment
            parameter m.
        seed (int):
            Seed forwarded to the NetworkX graph generator so that the graph
            structure is reproducible for the same input seed.

    Returns:
        nx.Graph:
            A generated Barabási-Albert graph.
    """
    # Use half the average degree as the attachment parameter.
    m = max(1, round(avg_degree / 2))

    # m cannot exceed n - 1.
    m = min(m, n - 1)

    return nx.barabasi_albert_graph(n, m, seed=seed)


# =============================================================================
# SECTION 3: EPIDEMIC LOGIC
# =============================================================================


def is_winter(day):
    """
    Check whether a calendar day belongs to the winter period.

    Internally, the function normalizes the input to the interval 1..365 so
    that it still works correctly if a larger day number is passed in.
    Winter is defined here as:
        - day 1 to day 90
        - day 350 to day 365

    This definition is later used in extended mode to reduce the daily recovery
    rate by 20 percent.

    Parameters:
        day (int):
            Calendar day of the year. Values outside 1..365 are wrapped into
            that interval with modular arithmetic.

    Returns:
        bool:
            True if the normalized day is treated as winter, otherwise False.
    """
    # Normalize the given day into the range 1..365.
    normalized_day = (day - 1) % 365 + 1

    # Winter is defined as the beginning and end of the year.
    return normalized_day <= 90 or normalized_day >= 350


def is_holiday_period(day):
    """
    Check whether a calendar day falls into a holiday effect window.

    Internally, the function normalizes the day to 1..365 and then checks
    whether that day is at most HOLIDAY_BUFFER days away from any holiday in
    HOLIDAYS. It also checks wrap-around distances across the end of the year,
    so days near New Year are handled correctly.

    This function is used in extended mode to increase beta by 30 percent
    during holiday periods.

    Parameters:
        day (int):
            Calendar day of the year. Values outside 1..365 are wrapped into
            that interval with modular arithmetic.

    Returns:
        bool:
            True if the day lies inside a holiday influence window,
            otherwise False.
    """
    # Normalize the given day into the range 1..365.
    normalized_day = (day - 1) % 365 + 1

    for holiday in HOLIDAYS:
        # Direct distance inside the same year.
        if abs(normalized_day - holiday) <= HOLIDAY_BUFFER:
            return True

        # Wrapped distances across the year boundary.
        if abs(normalized_day - holiday + 365) <= HOLIDAY_BUFFER:
            return True
        if abs(normalized_day - holiday - 365) <= HOLIDAY_BUFFER:
            return True

    return False


def get_effective_params(beta, gamma_base, day, extended_mode):
    """
    Compute the effective epidemic parameters for one calendar day.

    Internally, the function starts from the base parameters beta and
    gamma_base. If extended_mode is disabled, the values are returned
    unchanged.

    If extended_mode is enabled, two environmental effects are applied:
        1. Winter effect:
           If the day is considered winter, gamma is reduced by 20 percent.
        2. Holiday effect:
           If the day is inside a holiday period, beta is increased by
           30 percent.

    Both values are clamped to the valid probability range [0.0, 1.0]
    before they are returned.

    Parameters:
        beta (float):
            Base infection probability per contact in the interval 0..1.
        gamma_base (float):
            Base recovery probability per day in the interval 0..1.
        day (int):
            Calendar day used to determine winter and holiday effects.
        extended_mode (bool):
            If True, winter and holiday effects are applied. If False,
            the base parameters are returned unchanged.

    Returns:
        tuple[float, float]:
            A tuple (beta_eff, gamma_eff) containing the effective infection
            and recovery probabilities for the given day.
    """
    # In basic mode, return the parameters unchanged.
    if not extended_mode:
        return beta, gamma_base

    # Work on local copies so the input values stay unchanged.
    beta_eff = beta
    gamma_eff = gamma_base

    # Winter decreases the recovery probability.
    if is_winter(day):
        gamma_eff *= 0.8

    # Holiday periods increase the infection probability.
    if is_holiday_period(day):
        beta_eff *= 1.3

    # Clamp both probabilities to the valid range [0, 1].
    beta_eff = max(0.0, min(1.0, beta_eff))
    gamma_eff = max(0.0, min(1.0, gamma_eff))

    return beta_eff, gamma_eff


def simulate_step(states, graph, beta_eff, gamma_eff, rng):
    """
    Execute one synchronous SIR simulation step.

    Internally, the function performs a two-phase update:

        Phase 1 - Evaluation:
            A copy of the current state dictionary is created as next_states.
            For every infected node:
                - each susceptible neighbor can become infected with
                  probability beta_eff
                - the infected node itself can recover with probability
                  gamma_eff

            During this phase, only the original states dictionary is read,
            while all changes are written into next_states.

        Phase 2 - Commit:
            The function returns next_states as the complete updated state
            snapshot for the next simulation day.

    This approach guarantees synchronous behavior. It prevents the update order
    of nodes from changing the result within the same day.

    Parameters:
        states (dict):
            Dictionary of the current node states in the form
            {node_id: state_string}.
        graph (nx.Graph):
            Network graph defining which nodes are connected.
        beta_eff (float):
            Effective infection probability for the current day.
        gamma_eff (float):
            Effective recovery probability for the current day.
        rng (random.Random):
            Local pseudo-random generator used for all stochastic decisions
            inside this simulation run. Using this local generator is essential
            for strict reproducibility.

    Returns:
        dict:
            A new dictionary with the updated node states after one synchronous
            simulation step.
    """
    # Start from a copy so all updates stay synchronous.
    next_states = dict(states)

    for node in graph.nodes():
        # Only infected nodes can infect neighbors or recover.
        if states[node] != STATE_I:
            continue

        # Try to infect susceptible neighbors.
        for neighbor in graph.neighbors(node):
            if states[neighbor] == STATE_S:
                if rng.random() <= beta_eff:
                    next_states[neighbor] = STATE_I

        # Try to recover the infected node.
        if rng.random() <= gamma_eff:
            next_states[node] = STATE_R

    return next_states


def run_simulation(graph, beta, gamma_base, seed, extended_mode):
    """
    Run a complete SIR simulation on one graph and return its full history.

    Internally, this function guarantees deterministic stochastic behavior by
    creating exactly one local pseudo-random generator from the given seed:

        rng = random.Random(seed)

    This local generator is created before the outbreak start day and patient
    zero are chosen. Therefore, for the same graph structure and the same seed:
        - start_day is always identical
        - patient_zero is always identical
        - all later random infection and recovery decisions are also identical

    No uncontrolled global random calls are used inside this function.

    The procedure is:
        1. Create a local random generator from the seed.
        2. Draw the outbreak start day from 1..365.
        3. Draw patient zero from the graph nodes.
        4. Initialize all nodes as susceptible.
        5. Infect patient zero.
        6. Store the initial state as history entry 0.
        7. Simulate up to 365 daily steps.
        8. Stop early if no infected nodes remain.

    Parameters:
        graph (nx.Graph):
            Network graph on which the epidemic runs.
        beta (float):
            Base infection probability in the interval 0..1.
        gamma_base (float):
            Base recovery probability in the interval 0..1.
        seed (int):
            The single central seed for this simulation run. It determines the
            local RNG, the outbreak start day, the choice of patient zero, and
            all later stochastic epidemic events.
        extended_mode (bool):
            If True, winter and holiday effects modify beta and gamma during
            the run. If False, the base parameters are used throughout.

    Returns:
        tuple[list, int, int]:
            - history (list):
              List of tuples (states_dict, calendar_day), one tuple per stored
              simulation state.
            - start_day (int):
              Calendar day on which the outbreak starts.
            - patient_zero (int):
              Node id of the first infected node.
    """
    # Create the one and only local random generator for this simulation run.
    # This generator is used for start_day, patient_zero, and all later
    # infection/recovery decisions, which makes the run reproducible.
    rng = random.Random(seed)

    # Determine outbreak start day and patient zero from the same seeded RNG.
    start_day = rng.randint(1, 365)
    patient_zero = rng.choice(list(graph.nodes()))

    # Initialize all nodes as susceptible, then infect patient zero.
    states = {node: STATE_S for node in graph.nodes()}
    states[patient_zero] = STATE_I

    # Store the initial condition as frame 0.
    history = [(dict(states), start_day)]

    # Run at most 365 daily steps.
    for step in range(1, 366):
        # Compute the calendar day corresponding to this simulation step.
        calendar_day = (start_day - 1 + step) % 365 + 1

        # Get the effective parameters for the current day.
        beta_eff, gamma_eff = get_effective_params(
            beta, gamma_base, calendar_day, extended_mode
        )

        # Advance the epidemic by one synchronous step.
        states = simulate_step(states, graph, beta_eff, gamma_eff, rng)

        # Store the updated state snapshot.
        history.append((dict(states), calendar_day))

        # Stop early if no infected nodes remain.
        infected_count = sum(1 for state in states.values() if state == STATE_I)
        if infected_count == 0:
            break

    return history, start_day, patient_zero


# =============================================================================
# SECTION 4: INTERACTIVE UI AND ANIMATION
# =============================================================================


# -- Global simulation state ---------------------------------------------------
# This dictionary stores the shared runtime state of the application.
# All callbacks read from and write to this object, which keeps the design
# procedural and avoids class-based architecture.
sim_state = {
    "playing": False,             # Whether the animation is currently running
    "extended_mode": False,       # Whether seasonal effects are enabled
    "current_frame": 0,           # Currently displayed frame index
    "histories": [None, None, None],       # Precomputed simulation histories
    "start_days": [None, None, None],      # Start day for each topology
    "patient_zeros": [None, None, None],   # Patient zero id for each topology
    "graphs": [None, None, None],          # The three network graphs
    "layouts": [None, None, None],         # Spring layouts for plotting
    "max_frames": 0,              # Longest simulation length across topologies
}


# -- Figure and GridSpec layout ------------------------------------------------
# Row 0 contains the three network visualizations.
# Row 1 contains the corresponding epidemic curves.
fig = plt.figure(figsize=(20, 11))

gs = GridSpec(
    2,
    3,
    figure=fig,
    top=0.88,
    bottom=0.40,
    left=0.05,
    right=0.98,
    height_ratios=[3, 2],
    hspace=0.55,
    wspace=0.28,
)

# Top row: network plots.
ax_nets = [fig.add_subplot(gs[0, i]) for i in range(3)]

# Bottom row: epidemic curves.
ax_curves = [fig.add_subplot(gs[1, i]) for i in range(3)]

# Place the main title safely above the subplot area.
fig.suptitle("Network-based SIR Simulation - Topology Comparison", fontsize=13, y=0.96)


# -- Slider axes ---------------------------------------------------------------
# Each slider gets its own small axis in figure coordinates.
ax_slider_n = plt.axes([0.18, 0.31, 0.18, 0.025])
ax_slider_degree = plt.axes([0.18, 0.26, 0.18, 0.025])
ax_slider_beta = plt.axes([0.18, 0.21, 0.18, 0.025])
ax_slider_gamma = plt.axes([0.18, 0.16, 0.18, 0.025])
ax_slider_seed = plt.axes([0.18, 0.11, 0.18, 0.025])


# -- Sliders -------------------------------------------------------------------
slider_n = mwidgets.Slider(
    ax=ax_slider_n,
    label="N (nodes)",
    valmin=10,
    valmax=200,
    valinit=50,
    valstep=1,
)

slider_degree = mwidgets.Slider(
    ax=ax_slider_degree,
    label="Avg. Degree",
    valmin=1,
    valmax=10,
    valinit=4,
    valstep=1,
)

slider_beta = mwidgets.Slider(
    ax=ax_slider_beta,
    label="Beta",
    valmin=0.0,
    valmax=1.0,
    valinit=0.3,
)

slider_gamma = mwidgets.Slider(
    ax=ax_slider_gamma,
    label="Gamma Base",
    valmin=0.0,
    valmax=1.0,
    valinit=0.1,
)

slider_seed = mwidgets.Slider(
    ax=ax_slider_seed,
    label="Seed",
    valmin=0,
    valmax=999,
    valinit=42,
    valstep=1,
)


# -- Buttons -------------------------------------------------------------------
ax_btn_play = plt.axes([0.62, 0.27, 0.13, 0.05])
ax_btn_reset = plt.axes([0.78, 0.27, 0.13, 0.05])

btn_play = mwidgets.Button(ax_btn_play, "Play")
btn_reset = mwidgets.Button(ax_btn_reset, "Run")


# -- Extended mode checkbox ----------------------------------------------------
# In extended mode, winter reduces gamma and holiday periods increase beta.
ax_chk_extended = plt.axes([0.62, 0.08, 0.30, 0.12])
chk_extended = mwidgets.CheckButtons(
    ax_chk_extended,
    ["Extended Mode"],
    [False],
)


# -- Helper functions for season labels, month labels, and curve drawing ------

def get_season_label(day):
    """
    Convert a calendar day into an English season label.

    Internally, the function normalizes the input into 1..365 and uses a simple
    fixed mapping:
        - Winter: day 1..90 and 350..365
        - Spring: day 91..181
        - Summer: day 182..273
        - Autumn: day 274..349

    Parameters:
        day (int):
            Calendar day of the year. Values outside 1..365 are wrapped into
            that interval with modular arithmetic.

    Returns:
        str:
            One of the season labels "Winter", "Spring", "Summer", or "Autumn".
    """
    normalized_day = (day - 1) % 365 + 1

    if normalized_day <= 90 or normalized_day >= 350:
        return "Winter"
    if normalized_day <= 181:
        return "Spring"
    if normalized_day <= 273:
        return "Summer"
    return "Autumn"


def day_to_month_name(cal_day):
    """
    Convert a calendar day into an English month abbreviation.

    Internally, the function normalizes the input to 1..365 and then searches
    backward through MONTH_START_DAYS. The first month start that is less than
    or equal to the normalized day determines the month label.

    Parameters:
        cal_day (int):
            Calendar day of the year. Values outside 1..365 are wrapped into
            that interval with modular arithmetic.

    Returns:
        str:
            Three-letter English month abbreviation such as "Jan", "Mar", or "Dec".
    """
    normalized_day = (cal_day - 1) % 365 + 1

    for month_index in range(11, -1, -1):
        if normalized_day >= MONTH_START_DAYS[month_index]:
            return MONTH_NAMES[month_index]

    return "Jan"


def get_month_ticks(start_day, total_steps):
    """
    Compute x-axis tick positions and month labels for an epidemic curve.

    Internally, the x-axis is measured in simulation steps starting at 0, but
    the axis labels should show months. This function therefore:
        1. Places a tick at step 0 labeled with the outbreak month.
        2. Iterates through all later steps.
        3. Converts each step back into a calendar day.
        4. Adds a tick whenever that calendar day is the first day of a month.

    Parameters:
        start_day (int):
            Calendar day on which the outbreak starts.
        total_steps (int):
            Maximum number of simulation steps shown on the curve.

    Returns:
        tuple[list[int], list[str]]:
            - ticks: x positions where month labels should be shown
            - labels: corresponding month abbreviations
    """
    ticks = [0]
    labels = [day_to_month_name(start_day)]

    for step in range(1, total_steps + 1):
        cal_day = (start_day - 1 + step) % 365 + 1
        if cal_day in MONTH_START_DAYS:
            month_index = MONTH_START_DAYS.index(cal_day)
            ticks.append(step)
            labels.append(MONTH_NAMES[month_index])

    return ticks, labels


def draw_curve_for(ax_curve, topology_idx, frame_idx):
    """
    Draw the SIR time series for one topology into a curve axis.

    Internally, the function reads the precomputed history for the requested
    topology, truncates it at the currently visible frame, and counts how many
    nodes are in states S, I, and R for each stored step. It then draws:
        - a blue S curve
        - a red I curve
        - a green R curve

    It also:
        - adds a vertical dashed line at the current frame
        - sets the y-axis to 0..N
        - applies month labels on the x-axis based on the outbreak start day

    Parameters:
        ax_curve (matplotlib.axes.Axes):
            Target axis where the epidemic curves should be drawn.
        topology_idx (int):
            Index of the topology:
                0 = Erdős-Rényi
                1 = Watts-Strogatz
                2 = Barabási-Albert
        frame_idx (int):
            Current global animation frame. It is clamped to the valid range
            of the selected topology.

    Returns:
        None:
            The function updates the given axis directly.
    """
    # Always clear the curve axis before redrawing it.
    ax_curve.clear()

    # If no simulation is available yet, hide the axis content.
    if sim_state["histories"][topology_idx] is None:
        ax_curve.set_axis_off()
        return

    history = sim_state["histories"][topology_idx]
    node_count = sim_state["graphs"][topology_idx].number_of_nodes()
    start_day = sim_state["start_days"][topology_idx]
    max_steps = len(history) - 1

    # Clamp the requested frame index to the valid range for this topology.
    safe_idx = min(frame_idx, max_steps)

    # Build the S, I, R time series from history entry 0 to safe_idx.
    steps_x = list(range(safe_idx + 1))
    s_values = []
    i_values = []
    r_values = []

    for frame in range(safe_idx + 1):
        snapshot, _ = history[frame]
        s_values.append(sum(1 for value in snapshot.values() if value == STATE_S))
        i_values.append(sum(1 for value in snapshot.values() if value == STATE_I))
        r_values.append(sum(1 for value in snapshot.values() if value == STATE_R))

    # Draw the three compartment curves.
    ax_curve.plot(steps_x, s_values, color=COLOR_S, lw=1.2, label="S")
    ax_curve.plot(steps_x, i_values, color=COLOR_I, lw=1.2, label="I")
    ax_curve.plot(steps_x, r_values, color=COLOR_R, lw=1.2, label="R")

    # Mark the current visible simulation step.
    if steps_x:
        ax_curve.axvline(x=steps_x[-1], color="#aaaaaa", lw=0.8, ls="--")

    # Configure axis limits and style.
    ax_curve.set_xlim(0, max(max_steps, 1))
    ax_curve.set_ylim(0, node_count * 1.08)
    ax_curve.set_ylabel("People", fontsize=6)
    ax_curve.tick_params(labelsize=6)
    ax_curve.grid(True, alpha=0.25, lw=0.4)

    # Compute and apply month labels on the x-axis.
    ticks, labels = get_month_ticks(start_day, max_steps)
    ax_curve.set_xticks(ticks)
    ax_curve.set_xticklabels(labels, fontsize=5.5, rotation=35, ha="right")


def draw_frame(frame_idx):
    """
    Draw one animation frame for all three network views and all three curves.

    Internally, the function updates two visual layers per topology:

        Top row - network plot:
            - draw dark graph edges
            - draw colored nodes by S, I, R state
            - display a title with topology name, simulation day, calendar day,
              season, optional holiday note, and S/I/R counts

        Bottom row - epidemic curve:
            - delegate the actual drawing to draw_curve_for()

    Each topology uses its own clamped frame index so that shorter simulations
    remain visible in their final state while longer ones can continue.

    Parameters:
        frame_idx (int):
            Global animation frame index requested by the animation loop.

    Returns:
        None:
            The function redraws the corresponding matplotlib axes directly.
    """
    # Clear all network axes before redrawing them.
    for ax in ax_nets:
        ax.clear()
        ax.set_axis_off()

    # Draw network and curve for each topology.
    for idx in range(3):
        ax_net = ax_nets[idx]

        if sim_state["histories"][idx] is None:
            ax_net.set_title(f"{TOPOLOGY_NAMES[idx]}\n(No simulation yet)", fontsize=9)
            ax_curves[idx].clear()
            continue

        history = sim_state["histories"][idx]
        graph = sim_state["graphs"][idx]
        positions = sim_state["layouts"][idx]

        # Clamp the frame index to the valid history length of this topology.
        safe_idx = min(frame_idx, len(history) - 1)
        states_snapshot, calendar_day = history[safe_idx]

        # Determine node colors from the SIR state of each node.
        color_map = {
            STATE_S: COLOR_S,
            STATE_I: COLOR_I,
            STATE_R: COLOR_R,
        }
        node_colors = [color_map[states_snapshot[node]] for node in graph.nodes()]

        # Reduce node size for larger graphs to limit overlap.
        node_count = graph.number_of_nodes()
        node_size = max(15, int(500 / max(1, node_count)))

        # Draw edges in a dark neutral tone so the node states stay prominent.
        nx.draw_networkx_edges(
            graph,
            positions,
            ax=ax_net,
            alpha=0.15,
            width=0.5,
            edge_color="#262626",
        )

        # Draw nodes with state-based colors.
        nx.draw_networkx_nodes(
            graph,
            positions,
            ax=ax_net,
            node_color=node_colors,
            node_size=node_size,
            alpha=0.90,
        )

        # Count how many nodes are currently in S, I, and R.
        s_count = sum(1 for state in states_snapshot.values() if state == STATE_S)
        i_count = sum(1 for state in states_snapshot.values() if state == STATE_I)
        r_count = sum(1 for state in states_snapshot.values() if state == STATE_R)

        season = get_season_label(calendar_day)
        holiday_note = ""
        if sim_state["extended_mode"] and is_holiday_period(calendar_day):
            holiday_note = " | Holiday (+beta)"
        extended_tag = " [Extended]" if sim_state["extended_mode"] else ""

        # Set a compact descriptive title for the network panel.
        ax_net.set_title(
            f"{TOPOLOGY_NAMES[idx]}{extended_tag}\n"
            f"Sim day {safe_idx} | Calendar day {calendar_day} | {season}{holiday_note}\n"
            f"S={s_count}   I={i_count}   R={r_count}",
            fontsize=8,
            pad=4,
        )

        # Draw the corresponding epidemic curve underneath.
        draw_curve_for(ax_curves[idx], idx, frame_idx)

    # Request a non-blocking canvas redraw.
    fig.canvas.draw_idle()


# -- Main callbacks ------------------------------------------------------------

def build_all_simulations():
    """
    Read the current UI parameters, rebuild all graphs, and recompute everything.

    Internally, this function is the central reset point of the application.
    It performs these steps:

        1. Read N, average degree, beta, gamma, and seed from the sliders.
        2. Create the three graphs with the exact same central seed.
        3. Compute a seeded spring layout for each graph.
        4. Run a full SIR simulation for each graph with the same central seed.
        5. Store all generated objects in sim_state.
        6. Determine the longest history length across the three topologies.
        7. Update the seed information label.
        8. Reset the animation to frame 0 and redraw the UI.

    Determinism note:
        The slider seed is the only starting point for all stochastic behavior.
        It is passed to:
            - NetworkX graph generators
            - NetworkX spring_layout
            - run_simulation, where a local Random(seed) instance controls
              start_day, patient_zero, and all epidemic events

        This ensures that running the script again with the same parameters
        reproduces the same graphs, layouts, outbreak day, patient zero,
        and simulation trajectories.

    Parameters:
        None:
            The function reads all required input values directly from the UI widgets.

    Returns:
        None:
            The function updates sim_state, the seed label, and the plots directly.
    """
    # Read the current slider values.
    n = int(slider_n.val)
    avg_degree = float(slider_degree.val)
    beta = float(slider_beta.val)
    gamma_base = float(slider_gamma.val)
    seed = int(slider_seed.val)
    extended = sim_state["extended_mode"]

    # Create the three graphs with the same central seed.
    graphs = [
        create_erdos_renyi(n, avg_degree, seed),
        create_watts_strogatz(n, avg_degree, seed),
        create_barabasi_albert(n, avg_degree, seed),
    ]

    # Compute deterministic layouts from the same seed.
    layouts = [nx.spring_layout(graph, seed=seed) for graph in graphs]

    # Precompute the full epidemic histories for all three topologies.
    histories = []
    start_days = []
    patient_zeros = []

    for graph in graphs:
        history, start_day, patient_zero = run_simulation(
            graph,
            beta,
            gamma_base,
            seed,
            extended,
        )
        histories.append(history)
        start_days.append(start_day)
        patient_zeros.append(patient_zero)

    # Store all results in the shared application state.
    sim_state["graphs"] = graphs
    sim_state["layouts"] = layouts
    sim_state["histories"] = histories
    sim_state["start_days"] = start_days
    sim_state["patient_zeros"] = patient_zeros

    # Use the longest history so all topologies can animate until the last one ends.
    sim_state["max_frames"] = max(len(history) for history in histories) - 1

    # Update the label that explains what the current seed produced.
    durations = [len(history) - 1 for history in histories]
    seed_info_text.set_text(
        f"Seed {seed} -- deterministic values:\n"
        f"  Start day   : Day {start_days[0]} ({get_season_label(start_days[0])})\n"
        f"  Patient zero: Node #{patient_zeros[0]}\n"
        f"  Run length  : ER={durations[0]}d  WS={durations[1]}d  BA={durations[2]}d"
    )

    # Reset the animation to frame 0.
    sim_state["current_frame"] = 0
    sim_state["playing"] = False
    btn_play.label.set_text("Play")

    # Redraw the first frame immediately.
    draw_frame(0)


def toggle_play(event):
    """
    Toggle the animation between playing and paused.

    Internally, the function checks whether a simulation is already available.
    If not, it does nothing. Otherwise:
        - if the animation is running, it pauses it
        - if the animation is paused, it starts it
        - if the animation has already reached the final frame, it first resets
          the frame counter to 0 before starting again

    Parameters:
        event:
            Matplotlib button click event object. The function does not use its
            internal fields directly.

    Returns:
        None:
            The function updates sim_state and the play button label directly.
        """
    # Ignore clicks if no simulation has been computed yet.
    if sim_state["histories"][0] is None:
        return

    if sim_state["playing"]:
        # Pause the running animation.
        sim_state["playing"] = False
        btn_play.label.set_text("Play")
    else:
        # Restart from the beginning if the animation is already at the end.
        if sim_state["current_frame"] >= sim_state["max_frames"]:
            sim_state["current_frame"] = 0

        # Start the animation.
        sim_state["playing"] = True
        btn_play.label.set_text("Pause")

    fig.canvas.draw_idle()


def on_reset(event):
    """
    Stop the current animation and rebuild all simulations immediately.

    Internally, this callback is connected to the Run button. It stops playback,
    restores the play button label, and then calls build_all_simulations() so
    that graphs, curves, and deterministic seed-derived values are regenerated
    from the current UI parameters.

    Parameters:
        event:
            Matplotlib button click event object. The function does not use its
            internal fields directly.

    Returns:
        None:
            The function updates the application state and redraws the plots.
    """
    # Stop the animation before rebuilding the simulation state.
    sim_state["playing"] = False
    btn_play.label.set_text("Play")

    # Recompute everything from the current sliders and checkbox.
    build_all_simulations()


def on_extended_toggle(label):
    """
    Toggle extended mode and immediately recompute all simulations.

    Internally, this callback reads the checkbox state, stores it in sim_state,
    and rebuilds the full simulation set so that winter and holiday effects
    become visible immediately in both the network views and the curves.

    Parameters:
        label (str):
            Label text of the clicked checkbox entry. It is not used because
            there is only one checkbox.

    Returns:
        None:
            The function updates sim_state and redraws the plots indirectly
            through build_all_simulations().
    """
    # Read the checkbox state and store it in the shared application state.
    sim_state["extended_mode"] = chk_extended.get_status()[0]

    # Recompute all simulations with the new mode.
    build_all_simulations()


def advance_animation(frame):
    """
    Advance the global animation by one frame.

    Internally, this function is called by FuncAnimation every 450 ms.
    If playback is disabled, it returns immediately. If playback is enabled:
        - it increments the global frame index while frames remain
        - it redraws the new frame
        - it automatically stops the animation once the last global frame is reached

    Parameters:
        frame (int):
            Internal frame counter supplied by FuncAnimation. The function does
            not use this value because it manages the animation state through
            sim_state["current_frame"].

    Returns:
        None:
            The function updates the global frame index and the visible plots.
    """
    # Do nothing while the animation is paused.
    if not sim_state["playing"]:
        return

    if sim_state["current_frame"] < sim_state["max_frames"]:
        # Advance to the next frame and redraw.
        sim_state["current_frame"] += 1
        draw_frame(sim_state["current_frame"])
    else:
        # Stop automatically when the last frame has been reached.
        sim_state["playing"] = False
        btn_play.label.set_text("Play")
        fig.canvas.draw_idle()


# -- Connect callbacks to widgets ----------------------------------------------
btn_play.on_clicked(toggle_play)
btn_reset.on_clicked(on_reset)
chk_extended.on_clicked(on_extended_toggle)

# Every slider change triggers an immediate full rebuild so the UI stays live.
slider_n.on_changed(lambda value: build_all_simulations())
slider_degree.on_changed(lambda value: build_all_simulations())
slider_beta.on_changed(lambda value: build_all_simulations())
slider_gamma.on_changed(lambda value: build_all_simulations())
slider_seed.on_changed(lambda value: build_all_simulations())


# -- Configure animation -------------------------------------------------------
# A slower interval makes epidemic waves easier to observe visually.
anim = FuncAnimation(fig, advance_animation, interval=450, cache_frame_data=False)


# -- Legend --------------------------------------------------------------------
legend_patches = [
    mpatches.Patch(color=COLOR_S, label="S - Susceptible"),
    mpatches.Patch(color=COLOR_I, label="I - Infected"),
    mpatches.Patch(color=COLOR_R, label="R - Recovered"),
]
fig.legend(
    handles=legend_patches,
    loc="lower right",
    bbox_to_anchor=(0.99, 0.01),
    fontsize=8,
    framealpha=0.85,
)


# -- Bottom usage hint ---------------------------------------------------------
fig.text(
    0.50,
    0.005,
    "1. Move sliders = live update   2. Click 'Run' = rebuild   3. Click 'Play' = animate",
    ha="center",
    va="bottom",
    fontsize=8,
    color="#555555",
)


# -- Seed information text box -------------------------------------------------
# This label shows which deterministic values are produced by the current seed.
seed_info_text = fig.text(
    0.40,
    0.37,
    "Seed-derived values will appear here after initialization.",
    ha="left",
    va="top",
    fontsize=7.5,
    family="monospace",
    color="#333333",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f8", alpha=0.88),
)


# -- Initial computation on program start --------------------------------------
# Build everything immediately so the window is populated from the start.
build_all_simulations()


# -- Start the matplotlib event loop -------------------------------------------
plt.show()