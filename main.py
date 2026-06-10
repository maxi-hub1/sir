# =============================================================================
# SIR-Netzwerksimulation – einzelnes prozedurales Skript
# =============================================================================
# Dieses Skript simuliert die Ausbreitung einer Epidemie nach dem SIR-Modell
# (Susceptible–Infected–Recovered) auf drei verschiedenen Netzwerktopologien.
# Alle drei Simulationen laufen parallel und können interaktiv über Slider
# und Schaltflächen gesteuert werden.
# =============================================================================


# =============================================================================
# ABSCHNITT 1: IMPORTS UND KONFIGURATION
# =============================================================================

# random: Einfacher Zufallszahlengenerator – ermöglicht reproduzierbare
# Simulationen über den Seed-Parameter.  Kein numpy nötig, da nur einzelne
# Zufallsziehungen (randint, choice, random) durchgeführt werden.
import random

# numpy: Bibliothek für numerische Berechnungen. Hier vor allem für eventuelle
# Array-Operationen und Erweiterbarkeit; wird bei Zähler-Operationen genutzt.
import numpy as np

# networkx: Bibliothek zur Erstellung, Analyse und Visualisierung von Graphen.
# Stellt Generatoren für Erdős-Rényi, Watts-Strogatz und Barabási-Albert bereit
# und kann Netzwerke direkt in matplotlib-Achsen zeichnen.
import networkx as nx

# matplotlib.pyplot: Haupt-Zeichenbibliothek – erstellt Fenster, Subplots
# und alle grafischen Elemente.
import matplotlib.pyplot as plt

# matplotlib.patches: Ermöglicht das Zeichnen farbiger Rechtecke für die Legende.
import matplotlib.patches as mpatches

# matplotlib.widgets: Stellt interaktive UI-Elemente bereit:
# Slider (schiebbare Regler), Button (Schaltflächen), CheckButtons (Checkboxen).
import matplotlib.widgets as mwidgets

# FuncAnimation: Ruft eine Callback-Funktion wiederholt in festem Zeitabstand auf.
# Damit wird die Frame-für-Frame-Animation realisiert.
from matplotlib.animation import FuncAnimation

# GridSpec: Ermöglicht ein flexibles Rasterlayout für Subplots mit unterschiedlichen
# Höhenverhältnissen – hier 2 Zeilen (Netzwerke groß oben, Kurven kompakt unten)
# und 3 Spalten, eine Spalte pro Topologie.
from matplotlib.gridspec import GridSpec


# ── Zustandskonstanten ───────────────────────────────────────────────────────
STATE_S = "S"   # Anfällig  (Susceptible):  gesund, kann infiziert werden
STATE_I = "I"   # Infiziert (Infected):     krank, kann andere anstecken
STATE_R = "R"   # Genesen   (Recovered):    immun, kann nicht mehr erkranken

# ── Farbkonstanten für die Knotenvisualisierung ──────────────────────────────
COLOR_S = "#1f77b4"   # Blau  – anfällige Knoten
COLOR_I = "#d62728"   # Rot   – infizierte Knoten
COLOR_R = "#2ca02c"   # Grün  – genesene Knoten

# ── Feiertage als Tages-Nummern im Jahr (1 = 1. Januar, 365 = 31. Dezember) ─
# Neujahr (1), Karneval (~52), Ostermontag (~105), Pfingstmontag (~155),
# Heiligabend (358), 1. Weihnachtstag (359)
HOLIDAYS = [1, 52, 105, 155, 358, 359]

# Anzahl der Puffer-Tage rund um jeden Feiertag (erhöhtes Kontaktrisiko)
HOLIDAY_BUFFER = 3

# ── Namen der drei Topologien für Achsentitel ────────────────────────────────
TOPOLOGY_NAMES = ["Erdős-Rényi", "Watts-Strogatz", "Barabási-Albert"]

# ── Deutsche Monatsabkürzungen (für die X-Achse der Verlaufskurven) ──────────
# Die Reihenfolge entspricht den Monaten Januar bis Dezember.
MONTH_NAMES = [
    "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]

# ── Erster Kalendertag jedes Monats (1 = 1. Jan, 335 = 1. Dez) ───────────────
# Wird genutzt, um aus einem Kalendertag den zugehörigen Monatsnamen zu bestimmen
# und Tick-Positionen auf der X-Achse der Verlaufskurven zu platzieren.
MONTH_START_DAYS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]

# ── Schriftgröße global setzen ───────────────────────────────────────────────
plt.rcParams["font.size"] = 9


# =============================================================================
# ABSCHNITT 2: GRAPHEN-GENERIERUNG
# =============================================================================


def create_erdos_renyi(n, avg_degree, seed):
    """
    Erstellt einen Erdős-Rényi-Zufallsgraphen.

    Bei diesem Modell wird jede mögliche Kante zwischen zwei Knoten unabhängig
    mit derselben Wahrscheinlichkeit p gezogen. Die Wahrscheinlichkeit p wird
    so aus dem gewünschten Durchschnittsgrad berechnet:

        p = avg_degree / (n - 1)

    Das bedeutet: Hat ein Knoten n-1 potenzielle Nachbarn, verbindet ihn p mit
    jedem davon, was im Erwartungswert avg_degree Kanten ergibt.

    Parameter:
        n          (int)  : Anzahl der Knoten im Graphen.
        avg_degree (float): Gewünschter durchschnittlicher Grad (Kanten pro Knoten).
        seed       (int)  : Zufallsinitialisierung für Reproduzierbarkeit.

    Rückgabe:
        nx.Graph: Fertig erstellter Erdős-Rényi-Graph.
    """
    # Verbindungswahrscheinlichkeit aus dem gewünschten Durchschnittsgrad berechnen
    p = avg_degree / max(1, n - 1)
    # Auf gültigen Bereich [0, 1] begrenzen (kann bei sehr kleinem n > 1 werden)
    p = max(0.0, min(1.0, p))
    return nx.erdos_renyi_graph(n, p, seed=seed)


def create_watts_strogatz(n, avg_degree, seed):
    """
    Erstellt einen Watts-Strogatz-Kleinwelt-Graphen.

    Das Modell beginnt mit einem regulären Ring, in dem jeder Knoten mit seinen
    k nächsten Nachbarn verbunden ist (k/2 links, k/2 rechts). Anschließend
    wird jede Kante mit Wahrscheinlichkeit 0.1 zufällig umgeleitet.

    Das Ergebnis ist ein Netzwerk mit hohem Clusterkoeffizient (enge Gruppen)
    und kurzen Pfaden zwischen beliebigen Knoten – der sogenannte Kleinwelt-Effekt.

    Wichtig: Der Parameter k MUSS eine gerade positive Ganzzahl sein.
    Die Funktion rundet avg_degree entsprechend und stellt dies sicher.

    Parameter:
        n          (int)  : Anzahl der Knoten im Graphen.
        avg_degree (float): Gewünschter Durchschnittsgrad; wird intern auf die
                            nächste gerade Ganzzahl gerundet.
        seed       (int)  : Zufallsinitialisierung für Reproduzierbarkeit.

    Rückgabe:
        nx.Graph: Fertig erstellter Watts-Strogatz-Graph.
    """
    # Auf nächste Ganzzahl runden, mindestens 2
    k = max(2, round(avg_degree))
    # k muss gerade sein (Anforderung des Algorithmus: k/2 links, k/2 rechts)
    if k % 2 != 0:
        k += 1
    # k darf n-1 nicht überschreiten (sonst vollständiger Graph)
    k = min(k, n - 1)
    # Nach Begrenzung erneut auf Geradzahligkeit prüfen
    if k % 2 != 0:
        k -= 1
    # Absolutes Minimum sicherstellen
    k = max(2, k)
    return nx.watts_strogatz_graph(n, k, 0.1, seed=seed)


def create_barabasi_albert(n, avg_degree, seed):
    """
    Erstellt einen Barabási-Albert-Skalierungsfreien-Graphen.

    Dieses Wachstumsmodell fügt Knoten iterativ hinzu. Jeder neue Knoten
    verbindet sich mit m bestehenden Knoten, wobei Knoten mit vielen Kanten
    bevorzugt gewählt werden (Preferential Attachment / "die Reichen werden
    reicher"). Das Ergebnis ist eine Power-Law-Gradverteilung mit wenigen
    hochvernetzten Hubs – typisch für das Internet oder soziale Netzwerke.

    Der Parameter m entspricht in etwa der Hälfte des gewünschten
    Durchschnittsgrades.

    Parameter:
        n          (int)  : Anzahl der Knoten im Graphen.
        avg_degree (float): Gewünschter Durchschnittsgrad; wird intern als
                            m = round(avg_degree / 2) interpretiert.
        seed       (int)  : Zufallsinitialisierung für Reproduzierbarkeit.

    Rückgabe:
        nx.Graph: Fertig erstellter Barabási-Albert-Graph.
    """
    # Anzahl neuer Kanten pro hinzugefügtem Knoten: halber Durchschnittsgrad
    m = max(1, round(avg_degree / 2))
    # m darf n-1 nicht überschreiten
    m = min(m, n - 1)
    return nx.barabasi_albert_graph(n, m, seed=seed)


# =============================================================================
# ABSCHNITT 3: EPIDEMIE-LOGIK
# =============================================================================


def is_winter(day):
    """
    Prüft, ob ein gegebener Kalendertag in den Winter fällt.

    Winter ist definiert als die kalten Monate Dezember bis März, was grob
    den Tagen 1–90 (Januar bis Ende März) und 350–365 (Mitte Dezember bis
    Jahresende) entspricht. In dieser Jahreszeit ist das Immunsystem geschwächt,
    was im Extended Mode die Genesungsrate senkt.

    Der Eingabewert wird automatisch auf den Bereich 1–365 normiert, damit die
    Funktion auch mit Werten umgehen kann, die über 365 hinausgehen (zyklische
    Simulation über Jahresgrenzen hinweg).

    Parameter:
        day (int): Kalendertag des Jahres (wird auf 1–365 normiert, falls größer).

    Rückgabe:
        bool: True wenn der Tag im Winter liegt, sonst False.
    """
    # Normierung auf 1–365 (zyklisch)
    d = (day - 1) % 365 + 1
    # Winter: Anfang des Jahres (Jan–März) und Ende des Jahres (Dez)
    return d <= 90 or d >= 350


def is_holiday_period(day):
    """
    Prüft, ob ein Kalendertag in den Pufferzeitraum eines Feiertags fällt.

    Ein Tag gilt als „Feiertags-Puffertag", wenn er höchstens HOLIDAY_BUFFER
    Tage von einem der definierten Feiertage in der Liste HOLIDAYS entfernt ist.
    An solchen Tagen wird von erhöhten sozialen Kontakten ausgegangen
    (Familienfeiern, Reisen, Partys), was die Infektionswahrscheinlichkeit steigert.

    Jahreszyklische Überschneidungen werden berücksichtigt: Der 1. Januar liegt
    beispielsweise auch in der Nähe des 31. Dezembers (3 Tage Abstand).

    Parameter:
        day (int): Kalendertag des Jahres (wird auf 1–365 normiert).

    Rückgabe:
        bool: True wenn der Tag ein Feiertags-Puffertag ist, sonst False.
    """
    # Normierung auf 1–365
    d = (day - 1) % 365 + 1
    for holiday in HOLIDAYS:
        # Direkten Abstand zum Feiertag prüfen
        if abs(d - holiday) <= HOLIDAY_BUFFER:
            return True
        # Jahreszyklus berücksichtigen (z.B. Tag 363 → 3 Tage vor Tag 1)
        if abs(d - holiday + 365) <= HOLIDAY_BUFFER:
            return True
        if abs(d - holiday - 365) <= HOLIDAY_BUFFER:
            return True
    return False


def get_effective_params(beta, gamma_base, day, extended_mode):
    """
    Berechnet die effektiven Epidemieparameter für einen bestimmten Kalendertag.

    Im Basismodus werden beta und gamma_base unverändert zurückgegeben.
    Im Extended Mode werden zwei saisonale Umweltfaktoren angewandt:

        Wintereffekt (Tage 1–90 und 350–365):
            Die Genesungsrate gamma wird um 20 % gesenkt (× 0.8).
            Begründung: Kältestress und Lichtmangel schwächen das Immunsystem.

        Feiertagseffekt (±HOLIDAY_BUFFER Tage um einen Feiertag):
            Die Infektionswahrscheinlichkeit beta wird um 30 % erhöht (× 1.3).
            Begründung: Familienfeiern und Reisen erhöhen die Kontaktzahl.

    Beide Ergebniswerte werden abschließend auf den gültigen Bereich [0.0, 1.0]
    begrenzt, damit keine ungültigen Wahrscheinlichkeiten entstehen.

    Parameter:
        beta         (float): Basis-Infektionswahrscheinlichkeit pro Kontakt (0–1).
        gamma_base   (float): Basis-Genesungsrate pro Tag (0–1).
        day          (int)  : Aktueller Kalendertag (1–365) für Saisonberechnung.
        extended_mode (bool): Wenn True, werden saisonale Effekte angewandt.

    Rückgabe:
        tuple[float, float]: (beta_eff, gamma_eff) – die effektiven Parameterwerte
                              für diesen Simulationstag.
    """
    # Im Basismodus: Parameter unverändert zurückgeben
    if not extended_mode:
        return beta, gamma_base

    # Arbeitskopien anlegen, damit die Eingabewerte nicht verändert werden
    beta_eff  = beta
    gamma_eff = gamma_base

    # Wintereffekt: Genesungsrate um 20 % senken
    if is_winter(day):
        gamma_eff *= 0.8

    # Feiertagseffekt: Infektionsrate um 30 % erhöhen
    if is_holiday_period(day):
        beta_eff *= 1.3

    # Auf gültigen Wertebereich [0, 1] begrenzen
    beta_eff  = max(0.0, min(1.0, beta_eff))
    gamma_eff = max(0.0, min(1.0, gamma_eff))

    return beta_eff, gamma_eff


def simulate_step(states, graph, beta_eff, gamma_eff, rng):
    """
    Führt einen einzelnen synchronen SIR-Simulationsschritt durch.

    Das Verfahren verwendet ein synchrones Zwei-Phasen-Update, das sicherstellt,
    dass alle Zustandsänderungen gleichzeitig in Kraft treten und die Reihenfolge
    der Knotenverarbeitung keinen Einfluss auf das Ergebnis hat:

        Phase 1 – Evaluation:
            Für jeden infizierten Knoten (STATE_I) wird geprüft:
            a) Jeder anfällige Nachbar (STATE_S) wird mit Wahrscheinlichkeit
               beta_eff in next_states auf STATE_I gesetzt.
            b) Der infizierte Knoten selbst genest mit Wahrscheinlichkeit
               gamma_eff (next_states[node] = STATE_R).
            Wichtig: Während dieser Phase wird nur `states` gelesen (unveränderlich)
            und nur `next_states` geschrieben. So „sehen" alle Knoten noch den
            Zustand vom Anfang des Tages.

        Phase 2 – Commit:
            `next_states` wird als neues Zustands-Dictionary zurückgegeben.
            Alle Änderungen treten gleichzeitig in Kraft.

    Parameter:
        states     (dict)        : Aktuelles Zustands-Dict {Knoten-ID (int): Zustand (str)}.
                                   Wird nicht verändert (read-only in Phase 1).
        graph      (nx.Graph)    : Netzwerkgraph; seine Kanten definieren, wer wen
                                   kontaktieren kann.
        beta_eff   (float)       : Effektive Infektionswahrscheinlichkeit für heute.
        gamma_eff  (float)       : Effektive Genesungsrate für heute.
        rng        (random.Random): Initialisierter Zufallsgenerator für reproduzierbare
                                   Ergebnisse.

    Rückgabe:
        dict: Neues Zustands-Dictionary {Knoten-ID: Zustand} nach diesem Schritt.
    """
    # Phase 1: next_states als Kopie des aktuellen Zustands initialisieren
    # Alle Knoten behalten zunächst ihren alten Zustand
    next_states = dict(states)

    for node in graph.nodes():
        # Nur infizierte Knoten können andere anstecken oder selber genesen
        if states[node] != STATE_I:
            continue

        # Alle Nachbarn dieses infizierten Knotens prüfen
        for neighbor in graph.neighbors(node):
            # Nur anfällige Nachbarn können neu infiziert werden
            # Wichtig: states[neighbor] lesen, NICHT next_states[neighbor]!
            if states[neighbor] == STATE_S:
                # Zufallszahl ziehen: liegt sie unter beta_eff, wird infiziert
                if rng.random() <= beta_eff:
                    next_states[neighbor] = STATE_I

        # Genesungsversuch: mit Wahrscheinlichkeit gamma_eff genest der Knoten
        if rng.random() <= gamma_eff:
            next_states[node] = STATE_R

    # Phase 2: neuen Zustand zurückgeben (synchrones Commit)
    return next_states


def run_simulation(graph, beta, gamma_base, seed, extended_mode):
    """
    Führt eine vollständige SIR-Simulation auf einem Netzwerkgraphen durch
    und gibt den kompletten Verlauf aller Tageszustände zurück.

    Ablauf:
        1.  Den Zufallsgenerator mit dem Seed initialisieren.
        2.  Startdatum (Kalendertag 1–365) zufällig ziehen.
        3.  Patient Zero (erster Infizierter) zufällig aus allen Knoten wählen.
        4.  Alle anderen Knoten auf STATE_S (anfällig) setzen.
        5.  Anfangszustand als ersten History-Eintrag speichern (Frame 0).
        6.  Schleife über maximal 365 Tage:
            a) Aktuellen Kalendertag berechnen (zyklisch 1–365).
            b) Effektive Parameter (beta_eff, gamma_eff) bestimmen.
            c) simulate_step() aufrufen → neuen Zustand berechnen.
            d) Zustand in der History speichern.
            e) Frühzeitig abbrechen, wenn keine Infizierten mehr vorhanden sind.

    Parameter:
        graph         (nx.Graph): Netzwerkgraph, auf dem die Simulation läuft.
        beta          (float)   : Basis-Infektionswahrscheinlichkeit (0–1).
        gamma_base    (float)   : Basis-Genesungsrate (0–1).
        seed          (int)     : Seed für Zufallsgenerator, Startdatum und Patient Zero.
                                  Gleicher Seed → identische Simulation.
        extended_mode (bool)    : True = Saisonale Effekte aktiv (Jahreszeit, Feiertage).

    Rückgabe:
        tuple[list, int, int]:
            - history (list)      : Liste von Tupeln (states_dict, calendar_day), ein Tupel
              pro Simulationstag. states_dict = {Knoten-ID: Zustandsstring}.
              Index 0 = Anfangszustand (Patient Zero infiziert, Kalendertag = start_day).
            - start_day (int)    : Der Kalendertag, an dem die Infektion begann (1–365).
            - patient_zero (int) : Knoten-ID des ersten Infizierten (vom Seed bestimmt).
    """
    # Zufallsgenerator mit dem Seed initialisieren (für Reproduzierbarkeit)
    rng = random.Random(seed)

    # Startdatum und Patient Zero per Seed festlegen
    start_day    = rng.randint(1, 365)
    patient_zero = rng.choice(list(graph.nodes()))

    # Alle Knoten auf "anfällig" setzen, dann Patient Zero infizieren
    states = {node: STATE_S for node in graph.nodes()}
    states[patient_zero] = STATE_I

    # Anfangszustand als Frame 0 in der History ablegen
    history = [(dict(states), start_day)]

    # Simulationsschleife: maximal 365 Tage
    for step in range(1, 366):
        # Aktuellen Kalendertag berechnen (zyklisch zwischen 1 und 365)
        calendar_day = (start_day - 1 + step) % 365 + 1

        # Effektive Parameter für diesen Kalendertag ermitteln
        beta_eff, gamma_eff = get_effective_params(
            beta, gamma_base, calendar_day, extended_mode
        )

        # Einen Simulationsschritt durchführen (synchrones Zwei-Phasen-Update)
        states = simulate_step(states, graph, beta_eff, gamma_eff, rng)

        # Aktuellen Zustand in der History festhalten
        history.append((dict(states), calendar_day))

        # Frühzeitiger Abbruch, wenn keine Infizierten mehr vorhanden sind
        infected_count = sum(1 for s in states.values() if s == STATE_I)
        if infected_count == 0:
            break

    # patient_zero zusätzlich zurückgeben, damit die UI ihn anzeigen kann
    return history, start_day, patient_zero


# =============================================================================
# ABSCHNITT 4: UI UND ANIMATION
# =============================================================================


# ── Globaler Simulationszustand ───────────────────────────────────────────────
# Dieses Dictionary speichert den gesamten Laufzeitzustand der Anwendung.
# Alle Callback-Funktionen lesen und schreiben auf dieses gemeinsame Objekt.
# (Es ersetzt den Einsatz einer Klasse und ist für Anfänger leichter lesbar.)
sim_state = {
    "playing":        False,               # Ob die Animation gerade läuft
    "extended_mode":  False,               # Ob der Extended Mode aktiv ist
    "current_frame":  0,                   # Aktuell angezeigter Frame-Index
    "histories":      [None, None, None],  # Vorberechnete Simulationsverläufe
    "start_days":     [None, None, None],  # Startdaten der drei Simulationen
    "patient_zeros":  [None, None, None],  # Patient-Zero-Knoten-ID je Simulation
    "graphs":         [None, None, None],  # Die drei Netzwerkgraphen
    "layouts":        [None, None, None],  # Knotenpositionierungen (Spring-Layout)
    "max_frames":     0,                   # Längste Simulationslänge (individueller Abbruch)
}


# ── Figure mit GridSpec (2 Zeilen × 3 Spalten) ───────────────────────────────
# Zeile 0 (height_ratio 3): Netzwerk-Visualisierungen – größer dargestellt.
# Zeile 1 (height_ratio 2): SIR-Verlaufskurven – kompakter, aber gut lesbar.
# top=0.88, bottom=0.40 → 48 % der Figurhöhe für die Plots;
# die restlichen 40 % unten sind für die Slider-Kontrollleiste reserviert.
fig = plt.figure(figsize=(20, 11))

gs = GridSpec(
    2, 3,
    figure=fig,
    top=0.88, bottom=0.40,
    left=0.05, right=0.98,
    height_ratios=[3, 2],
    hspace=0.55, wspace=0.28,
)

# Netzwerk-Achsen (obere Zeile): zeigen Knoten und Kanten farblich nach S/I/R
ax_nets   = [fig.add_subplot(gs[0, i]) for i in range(3)]
# Verlaufskurven-Achsen (untere Zeile): zeigen S/I/R-Zeitreihen mit Monatsbeschriftung
ax_curves = [fig.add_subplot(gs[1, i]) for i in range(3)]

# Haupttitel: y=0.96 liegt sicher oberhalb des GridSpec-Bereichs (top=0.88),
# damit er keinen Subplot-Titel überlappt.
fig.suptitle("SIR-Netzwerksimulation  –  Topologievergleich", fontsize=13, y=0.96)


# ── Slider-Achsen (linke Hälfte der Kontrollleiste) ───────────────────────────
# Jeder Slider erhält eine eigene kleine Achse. Format: [links, unten, breite, höhe]
# in Figure-Koordinaten (0 = linker/unterer Rand, 1 = rechter/oberer Rand).
# x=0.18 lässt links genug Platz für die Slider-Beschriftungen.
ax_slider_n      = plt.axes([0.18, 0.31, 0.18, 0.025])
ax_slider_degree = plt.axes([0.18, 0.26, 0.18, 0.025])
ax_slider_beta   = plt.axes([0.18, 0.21, 0.18, 0.025])
ax_slider_gamma  = plt.axes([0.18, 0.16, 0.18, 0.025])
ax_slider_seed   = plt.axes([0.18, 0.11, 0.18, 0.025])


# ── Slider erstellen ──────────────────────────────────────────────────────────
# Jeder Slider hat ein Label (links), einen Minimal-/Maximalwert und einen
# Startwert (valinit). valstep=1 erzwingt ganzzahlige Schritte.

# N: Anzahl der Knoten (ganzzahlig, 10 bis 200)
slider_n = mwidgets.Slider(
    ax=ax_slider_n,
    label="N (Knoten)",
    valmin=10, valmax=200, valinit=50, valstep=1,
)

# Avg. Degree: Durchschnittliche Kanten pro Knoten (ganzzahlig, 1 bis 10)
slider_degree = mwidgets.Slider(
    ax=ax_slider_degree,
    label="Avg. Degree",
    valmin=1, valmax=10, valinit=4, valstep=1,
)

# Beta: Infektionswahrscheinlichkeit pro Kontakt (kontinuierlich, 0.0 bis 1.0)
slider_beta = mwidgets.Slider(
    ax=ax_slider_beta,
    label="Beta",
    valmin=0.0, valmax=1.0, valinit=0.3,
)

# Gamma Base: Grund-Genesungsrate pro Tag (kontinuierlich, 0.0 bis 1.0)
slider_gamma = mwidgets.Slider(
    ax=ax_slider_gamma,
    label="Gamma Base",
    valmin=0.0, valmax=1.0, valinit=0.1,
)

# Seed: Zufallsinitialisierung; bestimmt Startdatum + Patient Zero (0 bis 999)
slider_seed = mwidgets.Slider(
    ax=ax_slider_seed,
    label="Seed",
    valmin=0, valmax=999, valinit=42, valstep=1,
)


# ── Buttons (rechte Hälfte der Kontrollleiste) ────────────────────────────────
ax_btn_play  = plt.axes([0.62, 0.27, 0.13, 0.05])
ax_btn_reset = plt.axes([0.78, 0.27, 0.13, 0.05])

btn_play  = mwidgets.Button(ax_btn_play,  "▶  Play")
btn_reset = mwidgets.Button(ax_btn_reset, "↺  Reset")


# ── Extended-Mode-Checkbox ────────────────────────────────────────────────────
# CheckButtons erzeugt eine Checkbox; [False] = initial deaktiviert.
# Im Extended Mode werden Jahreszeiten- und Feiertagseffekte auf Beta und Gamma
# angewandt (Wintereffekt: Gamma × 0.8 / Feiertagseffekt: Beta × 1.3).
ax_chk_extended = plt.axes([0.62, 0.08, 0.30, 0.12])
chk_extended = mwidgets.CheckButtons(
    ax_chk_extended, ["Extended Mode"], [False]
)


# ── Hilfsfunktionen für Jahreszeiten, Monatsbeschriftung und Kurvenzeichnung ──

def get_season_label(day):
    """
    Gibt die deutsche Jahreszeiten-Bezeichnung für einen Kalendertag zurück.

    Verwendet eine vereinfachte meteorologische Einteilung:
        Winter  : Tage   1– 90 und 350–365 (Dez, Jan, Feb, Mär)
        Frühling: Tage  91–181             (Apr, Mai, Jun)
        Sommer  : Tage 182–273             (Jul, Aug, Sep)
        Herbst  : Tage 274–349             (Okt, Nov)

    Parameter:
        day (int): Kalendertag des Jahres (wird auf 1–365 normiert).

    Rückgabe:
        str: Deutschsprachige Jahreszeiten-Bezeichnung.
    """
    # Normierung auf 1–365
    d = (day - 1) % 365 + 1
    if d <= 90 or d >= 350:
        return "Winter"
    if d <= 181:
        return "Frühling"
    if d <= 273:
        return "Sommer"
    return "Herbst"


def day_to_month_name(cal_day):
    """
    Gibt die deutsche Monatsabkürzung für einen Kalendertag (1–365) zurück.

    Die Funktion durchsucht die Liste MONTH_START_DAYS rückwärts (Dezember zuerst)
    und gibt den Monatsnamen zurück, in dessen Zeitraum der Tag fällt.
    Zum Beispiel liefert cal_day=45 → "Feb" (Februar, Tage 32–59).

    Parameter:
        cal_day (int): Kalendertag des Jahres (wird zyklisch auf 1–365 normiert).

    Rückgabe:
        str: Dreistellige deutsche Monatsabkürzung aus MONTH_NAMES,
             z.B. "Jan", "Mär", "Dez".
    """
    # Normierung auf 1–365
    d = (cal_day - 1) % 365 + 1
    # Rückwärts durch die Monatsstarts suchen (Dezember bis Januar)
    for i in range(11, -1, -1):
        if d >= MONTH_START_DAYS[i]:
            return MONTH_NAMES[i]
    return "Jan"  # Fallback (sollte nie erreicht werden)


def get_month_ticks(start_day, total_steps):
    """
    Berechnet Tick-Positionen und Monatsnamen für die X-Achse einer Verlaufskurve.

    Die X-Achse einer Verlaufskurve zeigt Simulationsschritte (0, 1, 2, ...),
    soll aber mit deutschen Monatsnamen beschriftet werden. Diese Funktion
    berechnet dafür:
        1. Schritt 0 erhält immer einen Tick mit dem Monatsnamen des Startdatums.
        2. Für jeden weiteren Schritt: Wenn der entsprechende Kalendertag der
           erste Tag eines Monats ist (in MONTH_START_DAYS enthalten),
           wird ein Tick gesetzt.

    Beispiel: start_day=328 (November), total_steps=62:
        → Ticks bei [0, 7, 39] mit Labels ["Nov", "Dez", "Jan"]

    Parameter:
        start_day   (int): Kalendertag, an dem die Simulation beginnt (1–365).
                           Bestimmt den ersten Tick-Label.
        total_steps (int): Maximale Anzahl von Simulationsschritten
                           (= Länge der History − 1).

    Rückgabe:
        tuple[list[int], list[str]]:
            - ticks  (list[int]): Simulationsschritt-Indizes für die Tick-Markierungen.
            - labels (list[str]): Zugehörige deutsche Monatsabkürzungen.
    """
    # Erster Tick: Startschritt 0 bekommt den Monatsnamen des Startdatums
    ticks  = [0]
    labels = [day_to_month_name(start_day)]

    # Alle weiteren Schritte prüfen: liegt ein Monatserster vor?
    for step in range(1, total_steps + 1):
        cal_day = (start_day - 1 + step) % 365 + 1
        if cal_day in MONTH_START_DAYS:
            month_idx = MONTH_START_DAYS.index(cal_day)
            ticks.append(step)
            labels.append(MONTH_NAMES[month_idx])

    return ticks, labels


def draw_curve_for(ax_curve, topology_idx, frame_idx):
    """
    Zeichnet die SIR-Verlaufskurven für eine Topologie in eine Kurven-Achse.

    Die Funktion baut die Zeitreihendaten aus dem vorberechneten Simulationsverlauf
    bis zum angegebenen Frame auf und zeichnet drei Linien in der Kurven-Achse:
        - Blau  (COLOR_S): Zeitreihe der anfälligen Personen (S)
        - Rot   (COLOR_I): Zeitreihe der infizierten Personen (I)
        - Grün  (COLOR_R): Zeitreihe der genesenen Personen (R)

    Die X-Achse zeigt Simulationsschritte (0, 1, ...) und wird mit deutschen
    Monatsnamen beschriftet, die auf das Startdatum der Infektion kalibriert sind
    (via get_month_ticks). Eine gestrichelte senkrechte Linie markiert den aktuell
    angezeigten Zeitpunkt in der Animation.

    Wenn die Simulation für diese Topologie noch nicht vorliegt (histories[idx] ist None),
    wird die Achse nur geleert und keine Daten gezeichnet.

    Parameter:
        ax_curve     (matplotlib.axes.Axes): Ziel-Achse für die Kurven.
                                              Entspricht einem Element aus ax_curves[].
        topology_idx (int)                 : Index der Topologie (0=ER, 1=WS, 2=BA).
                                              Bestimmt, welche Daten aus sim_state
                                              gelesen werden.
        frame_idx    (int)                 : Aktueller Animations-Frame-Index.
                                              Wird auf den letzten gültigen Frame
                                              der jeweiligen Topologie begrenzt.

    Rückgabe:
        None. Verändert ax_curve direkt (clear + neu zeichnen).
    """
    # Achse immer zuerst leeren (clear-and-redraw-Ansatz)
    ax_curve.clear()

    # Keine Simulation vorhanden → leere Achse zurückgeben
    if sim_state["histories"][topology_idx] is None:
        ax_curve.set_axis_off()
        return

    history   = sim_state["histories"][topology_idx]
    n         = sim_state["graphs"][topology_idx].number_of_nodes()
    start_day = sim_state["start_days"][topology_idx]
    max_steps = len(history) - 1

    # frame_idx auf gültigen Bereich dieser Topologie begrenzen
    safe_idx = min(frame_idx, max_steps)

    # Zeitreihen-Arrays bis zum aktuellen Frame aufbauen
    steps_x = list(range(safe_idx + 1))
    s_vals, i_vals, r_vals = [], [], []
    for f in range(safe_idx + 1):
        snap, _ = history[f]
        s_vals.append(sum(1 for v in snap.values() if v == STATE_S))
        i_vals.append(sum(1 for v in snap.values() if v == STATE_I))
        r_vals.append(sum(1 for v in snap.values() if v == STATE_R))

    # Drei Linien zeichnen (gleiche Farben wie die Knotenfarben)
    ax_curve.plot(steps_x, s_vals, color=COLOR_S, lw=1.2, label="S")
    ax_curve.plot(steps_x, i_vals, color=COLOR_I, lw=1.2, label="I")
    ax_curve.plot(steps_x, r_vals, color=COLOR_R, lw=1.2, label="R")

    # Gestrichelte senkrechte Linie am aktuellen Simulations-Tag
    if steps_x:
        ax_curve.axvline(x=steps_x[-1], color="#aaaaaa", lw=0.8, ls="--")

    # Achsenlimits: X von 0 bis Simulations-Ende; Y von 0 bis N (+ 8% Randpuffer)
    ax_curve.set_xlim(0, max(max_steps, 1))
    ax_curve.set_ylim(0, n * 1.08)
    ax_curve.set_ylabel("Personen", fontsize=6)
    ax_curve.tick_params(labelsize=6)
    ax_curve.grid(True, alpha=0.25, lw=0.4)

    # X-Achse mit deutschen Monatsnamen beschriften (via Hilfsfunktion)
    ticks, labels = get_month_ticks(start_day, max_steps)
    ax_curve.set_xticks(ticks)
    ax_curve.set_xticklabels(labels, fontsize=5.5, rotation=35, ha="right")


def draw_frame(frame_idx):
    """
    Zeichnet für einen Animations-Frame alle drei Netzwerke UND die dazugehörigen
    SIR-Verlaufskurven (obere Zeile: Netzwerke, untere Zeile: Kurven).

    Für jede der drei Topologien werden zwei Plots aktualisiert:

        Obere Zeile – Netzwerk (ax_nets[idx]):
            - Kanten: tiefes Dunkelgrau (#262626), dünn und halbtransparent
              (alpha=0.15), damit die farbigen Knoten optisch dominieren.
            - Knoten: farbig nach SIR-Zustand (Blau=S / Rot=I / Grün=R).
            - Titel: Topologiename, Sim-Tag, Kalendertag, Jahreszeit,
              Feiertags-Hinweis (nur im Extended Mode), S/I/R-Zählerstand.

        Untere Zeile – Verlaufskurven (ax_curves[idx]):
            - Delegiert an draw_curve_for(), welches S/I/R-Linien mit
              deutschen Monatsnamen auf der X-Achse zeichnet.

    Jede Topologie wird separat auf ihren eigenen letzten gültigen Frame begrenzt
    (safe_idx = min(frame_idx, len(history)−1)), sodass Topologien, die früher
    fertig sind, ihren Endzustand dauerhaft anzeigen.

    Alle Netzwerk-Achsen werden vor dem Zeichnen geleert (clear-and-redraw).
    Die Kurven-Achsen werden durch draw_curve_for() intern geleert.
    Abschließend wird der Canvas ohne blockierendes plt.show() aktualisiert.

    Parameter:
        frame_idx (int): Index in den Simulationsverläufen (0 = Infektionstag).
                         Wird je Topologie auf deren letzten gültigen Frame begrenzt.

    Rückgabe:
        None. Verändert ax_nets[] und ax_curves[] direkt.
    """
    # Alle Netzwerk-Achsen leeren
    for ax in ax_nets:
        ax.clear()
        ax.set_axis_off()

    # Jeden Subplot (Netzwerk + Kurve) einzeln zeichnen
    for idx in range(3):
        ax = ax_nets[idx]

        # Simulation muss bereits berechnet worden sein
        if sim_state["histories"][idx] is None:
            ax.set_title(f"{TOPOLOGY_NAMES[idx]}\n(Noch keine Simulation)", fontsize=9)
            ax_curves[idx].clear()
            continue

        history = sim_state["histories"][idx]
        graph   = sim_state["graphs"][idx]
        pos     = sim_state["layouts"][idx]

        # frame_idx auf gültigen Bereich dieser Topologie begrenzen
        safe_idx = min(frame_idx, len(history) - 1)
        states_snapshot, calendar_day = history[safe_idx]

        # Knotenfarben anhand des SIR-Zustands bestimmen
        color_map   = {STATE_S: COLOR_S, STATE_I: COLOR_I, STATE_R: COLOR_R}
        node_colors = [color_map[states_snapshot[node]] for node in graph.nodes()]

        # Knotengröße: bei mehr Knoten kleinere Punkte (keine Überlappung)
        n_nodes   = graph.number_of_nodes()
        node_size = max(15, int(500 / max(1, n_nodes)))

        # Kanten zeichnen: tiefes Dunkelgrau (#262626), damit farbige Knoten dominieren
        nx.draw_networkx_edges(
            graph, pos, ax=ax,
            alpha=0.15, width=0.5, edge_color="#262626",
        )
        # Knoten zeichnen (farbig nach SIR-Zustand)
        nx.draw_networkx_nodes(
            graph, pos, ax=ax,
            node_color=node_colors, node_size=node_size, alpha=0.90,
        )

        # S/I/R-Zähler für diesen Frame berechnen
        s_count = sum(1 for s in states_snapshot.values() if s == STATE_S)
        i_count = sum(1 for s in states_snapshot.values() if s == STATE_I)
        r_count = sum(1 for s in states_snapshot.values() if s == STATE_R)

        # Jahreszeit und optionale Feiertags-Hinweise ermitteln
        season       = get_season_label(calendar_day)
        holiday_note = ""
        if sim_state["extended_mode"] and is_holiday_period(calendar_day):
            holiday_note = "  | Feiertag (+Beta)"
        ext_tag = "  [Ext.]" if sim_state["extended_mode"] else ""

        # Titel des Netzwerk-Subplots setzen
        ax.set_title(
            f"{TOPOLOGY_NAMES[idx]}{ext_tag}\n"
            f"Sim-Tag {safe_idx}  |  Kal.-Tag {calendar_day}  |  {season}{holiday_note}\n"
            f"S={s_count}   I={i_count}   R={r_count}",
            fontsize=8, pad=4,
        )

        # Verlaufskurve in der unteren Zeile für diese Topologie zeichnen
        draw_curve_for(ax_curves[idx], idx, frame_idx)

    # Canvas ohne blockierendes plt.show() neu zeichnen
    fig.canvas.draw_idle()


# ── Haupt-Callbacks ───────────────────────────────────────────────────────────

def build_all_simulations():
    """
    Liest alle Slider-Werte aus, erstellt drei Netzwerkgraphen und berechnet
    die vollständigen Simulationen für alle drei Topologien im Voraus.

    Dieser Vorberechnungsansatz ermöglicht eine verzögerungsfreie Animation:
    Alle Frames sind bereits vor dem Start der Wiedergabe bekannt.
    Die Funktion wird aufgerufen bei:
        - Klick auf '↺ Reset'
        - Änderung eines beliebigen Sliders (Live-Reset)
        - Änderung der Extended-Mode-Checkbox
        - Beim Programmstart (initiale Berechnung)

    Ablauf:
        1. Slider-Werte N, avg_degree, beta, gamma_base, seed auslesen.
        2. Drei Graphen (Erdős-Rényi, Watts-Strogatz, Barabási-Albert) erstellen.
        3. Spring-Layout für jeden Graphen berechnen (Knotenpositionen).
        4. run_simulation() für jeden Graphen vollständig durchführen.
        5. Ergebnisse in sim_state speichern.
        6. max_frames = längste Simulation − 1 (individuelle Abbruchkriterien).
        7. seed_info_text mit Startdatum, Patient-Zero und Sim-Dauern aktualisieren.
        8. Frame-Zähler auf 0 setzen und Frame 0 zeichnen.

    Parameter:
        Keine. Alle Parameter werden aus den globalen Slider-Widgets gelesen.

    Rückgabe:
        None. Verändert sim_state, ax_nets[] und ax_curves[] direkt.
    """
    # ── Slider-Werte auslesen ─────────────────────────────────────────────────
    n          = int(slider_n.val)
    avg_degree = float(slider_degree.val)
    beta       = float(slider_beta.val)
    gamma_base = float(slider_gamma.val)
    seed       = int(slider_seed.val)
    extended   = sim_state["extended_mode"]

    # ── Drei Graphen mit denselben Parametern erstellen ───────────────────────
    graphs = [
        create_erdos_renyi(n, avg_degree, seed),
        create_watts_strogatz(n, avg_degree, seed),
        create_barabasi_albert(n, avg_degree, seed),
    ]

    # ── Spring-Layout berechnen (räumliche Knotenpositionierung) ─────────────
    # spring_layout platziert stark vernetzte Knoten räumlich näher beieinander
    layouts = [nx.spring_layout(g, seed=seed) for g in graphs]

    # ── Vollständige Simulation für alle drei Topologien vorberechnen ─────────
    # Jedes Modell läuft individuell bis I==0 oder max. 365 Tage.
    # Kein Modell wird vorzeitig gestoppt, weil ein anderes bereits fertig ist.
    histories, start_days, patient_zeros = [], [], []
    for g in graphs:
        hist, sday, pzero = run_simulation(g, beta, gamma_base, seed, extended)
        histories.append(hist)
        start_days.append(sday)
        patient_zeros.append(pzero)

    # ── Ergebnisse in sim_state speichern ─────────────────────────────────────
    sim_state["graphs"]        = graphs
    sim_state["layouts"]       = layouts
    sim_state["histories"]     = histories
    sim_state["start_days"]    = start_days
    sim_state["patient_zeros"] = patient_zeros
    # max_frames = LÄNGSTE Simulation − 1: alle drei laufen bis zum letzten Ende.
    # Kurz beendete Topologien frieren auf ihrem Endzustand ein (via safe_idx).
    sim_state["max_frames"] = max(len(h) for h in histories) - 1

    # ── Seed-Info-Label mit den festgelegten Startparametern aktualisieren ────
    # Da alle drei Topologien denselben Seed verwenden, sind start_day und
    # patient_zero für alle drei identisch.
    durations = [len(h) - 1 for h in histories]
    seed_info_text.set_text(
        f"Seed {seed}  ──  festgelegte Parameter:\n"
        f"  Startdatum :  Tag {start_days[0]}  ({get_season_label(start_days[0])})\n"
        f"  Patient Zero:  Knoten #{patient_zeros[0]}\n"
        f"  Sim-Dauer  :  ER={durations[0]}d  WS={durations[1]}d  BA={durations[2]}d"
    )

    # Animation auf Frame 0 zurücksetzen und neu zeichnen
    sim_state["current_frame"] = 0
    sim_state["playing"]       = False
    btn_play.label.set_text("▶  Play")
    draw_frame(0)


def toggle_play(event):
    """
    Schaltet die Animation zwischen Play und Pause um.

    Läuft die Animation, wird sie pausiert. Ist sie pausiert, wird sie gestartet.
    Hat die Animation ihren letzten Frame erreicht, springt ein erneuter
    Play-Klick automatisch zu Frame 0 zurück und startet von vorne.

    Wurde noch keine Simulation berechnet (histories[0] ist None), passiert nichts.

    Parameter:
        event: Matplotlib-Button-Klick-Event (Inhalt wird nicht ausgewertet).

    Rückgabe:
        None.
    """
    # Sicherheitscheck: Noch keine Simulation vorhanden
    if sim_state["histories"][0] is None:
        return

    if sim_state["playing"]:
        # Animation anhalten
        sim_state["playing"] = False
        btn_play.label.set_text("▶  Play")
    else:
        # Am Ende angelangt → von vorne starten
        if sim_state["current_frame"] >= sim_state["max_frames"]:
            sim_state["current_frame"] = 0
        sim_state["playing"] = True
        btn_play.label.set_text("⏸  Pause")

    # Button-Beschriftung sofort aktualisieren
    fig.canvas.draw_idle()


def on_reset(event):
    """
    Stoppt die laufende Animation und berechnet alle drei Simulationen sofort neu.

    Liest die aktuellen Slider-Werte aus, erstellt neue Netzwerke und führt
    vollständige Simulationen durch. Danach wird Frame 0 angezeigt.
    Wird durch den '↺ Reset'-Button ausgelöst.

    Parameter:
        event: Matplotlib-Button-Klick-Event (Inhalt wird nicht ausgewertet).

    Rückgabe:
        None.
    """
    # Laufende Animation stoppen
    sim_state["playing"] = False
    btn_play.label.set_text("▶  Play")
    # Simulationen mit aktuellen Parameterwerten neu aufbauen
    build_all_simulations()


def on_extended_toggle(label):
    """
    Callback für die Extended-Mode-Checkbox.

    Schaltet den Extended Mode ein oder aus und löst sofort eine Neuberechnung
    aller drei Simulationen aus, damit die saisonalen Effekte (Wintereffekt und
    Feiertagseffekt) sofort im Ergebnis sichtbar werden.

    Extended Mode ein:
        Wintereffekt (Tage 1–90 und 350–365): gamma × 0.8
        Feiertagseffekt (±3 Tage um HOLIDAYS): beta × 1.3
    Extended Mode aus: beta und gamma unverändert.

    Parameter:
        label (str): Bezeichnung der angeklickten Checkbox (wird nicht ausgewertet,
                     da nur eine Checkbox existiert).

    Rückgabe:
        None.
    """
    # Aktuellen Checkbox-Status auslesen (get_status gibt Liste zurück)
    sim_state["extended_mode"] = chk_extended.get_status()[0]
    # Simulation mit neuem Modus sofort neu berechnen
    build_all_simulations()


def advance_animation(frame):
    """
    Animations-Callback – wird von FuncAnimation alle 450 ms aufgerufen.

    Wenn die Animation läuft (playing == True), wird current_frame um 1
    erhöht und draw_frame() für den neuen Frame aufgerufen. Beim Erreichen
    des letzten Frames stoppt die Animation automatisch.

    Die Funktion läuft auch dann weiter, wenn playing == False ist, tut aber
    in diesem Fall nichts (passiver Bereitschaftsmodus).

    Parameter:
        frame (int): Von FuncAnimation übergebener interner Zähler.
                     Wird nicht verwendet – sim_state["current_frame"] ist maßgeblich.

    Rückgabe:
        None.
    """
    # Passiver Modus: nichts tun
    if not sim_state["playing"]:
        return

    if sim_state["current_frame"] < sim_state["max_frames"]:
        # Nächsten Frame anzeigen
        sim_state["current_frame"] += 1
        draw_frame(sim_state["current_frame"])
    else:
        # Letzten Frame erreicht: Animation automatisch stoppen
        sim_state["playing"] = False
        btn_play.label.set_text("▶  Play")
        fig.canvas.draw_idle()


# ── Callbacks an Buttons und Checkbox verknüpfen ──────────────────────────────
btn_play.on_clicked(toggle_play)
btn_reset.on_clicked(on_reset)
chk_extended.on_clicked(on_extended_toggle)

# ── Live-Update: Jede Slider-Änderung löst sofortigen Neustart der Simulation aus ─
# Die Lambda-Funktionen empfangen den neuen Slider-Wert (val), ignorieren ihn aber,
# da build_all_simulations() selbst alle Slider direkt ausliest.
# Hinweis: Bei großem N kann die Neuberechnung kurz (~0.5–1 s) dauern.
slider_n.on_changed(lambda val: build_all_simulations())
slider_degree.on_changed(lambda val: build_all_simulations())
slider_beta.on_changed(lambda val: build_all_simulations())
slider_gamma.on_changed(lambda val: build_all_simulations())
slider_seed.on_changed(lambda val: build_all_simulations())

# ── FuncAnimation einrichten ──────────────────────────────────────────────────
# interval=450: Jeder Frame wird 450 ms lang angezeigt (~2 Frames/Sekunde).
# Langsam genug, um Ausbreitungswellen in Netzwerk und Kurve visuell zu verfolgen.
# cache_frame_data=False: kein Caching, Zustand wird in sim_state verwaltet.
# Die Variable muss einer globalen Referenz zugewiesen werden, sonst löscht
# der Garbage Collector das Objekt und die Animation stoppt sofort.
anim = FuncAnimation(fig, advance_animation, interval=450, cache_frame_data=False)

# ── Farbkodierungs-Legende ────────────────────────────────────────────────────
# Erklärt die Knotenfarben und Kurvenfarben unten rechts im Fenster
legend_patches = [
    mpatches.Patch(color=COLOR_S, label="S – Anfällig (Susceptible)"),
    mpatches.Patch(color=COLOR_I, label="I – Infiziert (Infected)"),
    mpatches.Patch(color=COLOR_R, label="R – Genesen (Recovered)"),
]
fig.legend(
    handles=legend_patches,
    loc="lower right",
    bbox_to_anchor=(0.99, 0.01),
    fontsize=8,
    framealpha=0.85,
)

# ── Bedienungshinweis am unteren Rand ────────────────────────────────────────
fig.text(
    0.50, 0.005,
    "① Slider ziehen = Live-Update   ②  '↺ Reset' = Neustart   ③  '▶ Play' = Animation",
    ha="center", va="bottom", fontsize=8, color="#555555",
)

# ── Seed-Info-Textfeld ────────────────────────────────────────────────────────
# Zeigt dynamisch die vom Seed festgelegten Startparameter an:
#   - Startdatum der Infektion (Kalendertag + Jahreszeit)
#   - Knoten-ID des Patient Zero
#   - Individuelle Simulationsdauer jeder Topologie
# Positioniert in der Mitte zwischen Sliders (enden bei x≈0.36) und
# Buttons (beginnen bei x=0.62) – kein Überlapp mit anderen Elementen.
# Wird durch build_all_simulations() bei jedem Reset mit set_text() aktualisiert.
seed_info_text = fig.text(
    0.40, 0.37,
    "Seed-Parameter werden nach erstem Reset angezeigt.",
    ha="left", va="top",
    fontsize=7.5, family="monospace",
    color="#333333",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f8", alpha=0.88),
)

# ── Initiale Simulation beim Programmstart ────────────────────────────────────
# Sofort beim Start mit den Standard-Sliderwerten berechnen und anzeigen,
# damit das Fenster nicht leer erscheint und seed_info_text befüllt wird.
build_all_simulations()

# ── Matplotlib-Fenster öffnen und Ereignisschleife starten ───────────────────
plt.show()
