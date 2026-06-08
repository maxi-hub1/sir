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
        tuple[list, int]:
            - history (list): Liste von Tupeln (states_dict, calendar_day), ein Tupel
              pro Simulationstag. states_dict = {Knoten-ID: Zustandsstring}.
              Index 0 = Anfangszustand (Patient Zero infiziert, Kalendertag = start_day).
            - start_day (int): Der Kalendertag, an dem die Infektion begann (1–365).
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

    return history, start_day


# =============================================================================
# ABSCHNITT 4: UI UND ANIMATION
# =============================================================================


# ── Globaler Simulationszustand ───────────────────────────────────────────────
# Dieses Dictionary speichert den gesamten Laufzeitzustand der Anwendung.
# Alle Callback-Funktionen lesen und schreiben auf dieses gemeinsame Objekt.
# (Es ersetzt den Einsatz einer Klasse und ist für Anfänger leichter lesbar.)
sim_state = {
    "playing":       False,             # Ob die Animation gerade läuft
    "extended_mode": False,             # Ob der Extended Mode aktiv ist
    "current_frame": 0,                 # Aktuell angezeigter Frame-Index
    "histories":     [None, None, None],  # Vorberechnete Simulationsverläufe
    "start_days":    [None, None, None],  # Startdaten der drei Simulationen
    "graphs":        [None, None, None],  # Die drei Netzwerkgraphen
    "layouts":       [None, None, None],  # Knotenpositionierungen (Spring-Layout)
    "max_frames":    0,                 # Kleinste Simulationslänge (Sync-Grenze)
}


# ── Figure und Subplots ───────────────────────────────────────────────────────
# Drei Netzwerk-Subplots nebeneinander; breites Format für übersichtliche Darstellung
fig, (ax_er, ax_ws, ax_ba) = plt.subplots(1, 3, figsize=(18, 9))
axes = [ax_er, ax_ws, ax_ba]   # Als Liste für einfache Iteration

# Platz am unteren Rand für Slider und Buttons freihalten
plt.subplots_adjust(left=0.04, right=0.98, top=0.93, bottom=0.40)
fig.suptitle("SIR-Netzwerksimulation  –  Topologievergleich", fontsize=12, y=0.98)


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

# Seed: Zufallsinitialisierung; bestimmt Startdatum + Patient Zero (0 bis 9999)
slider_seed = mwidgets.Slider(
    ax=ax_slider_seed,
    label="Seed",
    valmin=0, valmax=9999, valinit=42, valstep=1,
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


# ── Hilfsfunktionen für die Visualisierung ───────────────────────────────────

def get_season_label(day):
    """
    Gibt die deutsche Jahreszeiten-Bezeichnung für einen Kalendertag zurück.

    Verwendet eine vereinfachte astronomische Einteilung:
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


def draw_frame(frame_idx):
    """
    Zeichnet den Simulationszustand aller drei Netzwerke für einen bestimmten Frame.

    Für jeden der drei Subplots wird folgendes dargestellt:
        - Kanten als dünne, halbtransparente graue Linien (Kontaktverbindungen)
        - Knoten als Punkte, farblich nach SIR-Zustand kodiert:
          Blau = anfällig (S), Rot = infiziert (I), Grün = genesen (R)
        - Titel mit: Topologiename, Sim-Tag, Kalendertag, Jahreszeit,
          Feiertags-Hinweis (nur im Extended Mode) und S/I/R-Zählerstand

    Alle drei Achsen werden vor dem Zeichnen geleert (clear-and-redraw-Ansatz).
    Anschließend wird der Canvas ohne blockierendes plt.show() aktualisiert.

    Parameter:
        frame_idx (int): Index in den Simulationsverläufen (0 = Anfangszustand).
                         Wird automatisch auf den letzten gültigen Frame begrenzt,
                         falls der Index die Länge der Simulation überschreitet.

    Rückgabe:
        None. Die Funktion verändert die globalen Achsen-Objekte direkt.
    """
    # Alle drei Achsen leeren
    for ax in axes:
        ax.clear()
        ax.set_axis_off()

    # Jeden Subplot einzeln zeichnen
    for idx, ax in enumerate(axes):
        # Simulation muss bereits berechnet worden sein
        if sim_state["histories"][idx] is None:
            ax.set_title(f"{TOPOLOGY_NAMES[idx]}\n(Noch keine Simulation)", fontsize=9)
            continue

        history = sim_state["histories"][idx]
        graph   = sim_state["graphs"][idx]
        pos     = sim_state["layouts"][idx]

        # frame_idx auf gültigen Bereich begrenzen
        safe_idx = min(frame_idx, len(history) - 1)
        states_snapshot, calendar_day = history[safe_idx]

        # Knotenfarben anhand des SIR-Zustands bestimmen
        color_map   = {STATE_S: COLOR_S, STATE_I: COLOR_I, STATE_R: COLOR_R}
        node_colors = [color_map[states_snapshot[node]] for node in graph.nodes()]

        # Knotengröße: bei mehr Knoten kleinere Punkte (damit sie nicht überlappen)
        n_nodes   = graph.number_of_nodes()
        node_size = max(15, int(500 / max(1, n_nodes)))

        # Kanten zeichnen (grau, dünn, halbtransparent)
        nx.draw_networkx_edges(
            graph, pos, ax=ax,
            alpha=0.12, width=0.5, edge_color="#888888",
        )
        # Knoten zeichnen (farbig nach Zustand)
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
        ext_tag = "  [Extended Mode]" if sim_state["extended_mode"] else ""

        # Titel des Subplots setzen
        ax.set_title(
            f"{TOPOLOGY_NAMES[idx]}{ext_tag}\n"
            f"Sim-Tag {safe_idx}  |  Kal.-Tag ~{calendar_day}  |  {season}{holiday_note}\n"
            f"S = {s_count}    I = {i_count}    R = {r_count}",
            fontsize=9, pad=5,
        )

    # Canvas ohne blockierendes plt.show() neu zeichnen
    fig.canvas.draw_idle()


# ── Haupt-Callbacks ───────────────────────────────────────────────────────────

def build_all_simulations():
    """
    Liest alle Slider-Werte aus, erstellt drei Netzwerkgraphen und berechnet
    die vollständige Simulation für alle drei Topologien im Voraus.

    Dieser Ansatz (Vorberechnung aller Frames) ermöglicht eine verzögerungsfreie
    Animation, da während der Wiedergabe keine Rechenoperationen mehr nötig sind.

    Ablauf:
        1. Slider-Werte N, avg_degree, beta, gamma_base, seed auslesen.
        2. Drei Graphen (Erdős-Rényi, Watts-Strogatz, Barabási-Albert) mit
           denselben Parametern und demselben Seed erstellen.
        3. Spring-Layout für jeden Graphen berechnen (Knotenpositionen).
        4. run_simulation() für jeden Graphen vollständig durchführen.
        5. Alle Ergebnisse in sim_state speichern.
        6. max_frames = kürzeste Simulation − 1, damit alle synchron enden.
        7. Frame-Zähler auf 0 setzen und ersten Frame zeichnen.

    Parameter:
        Keine. Alle Parameter werden aus den globalen Slider-Widgets gelesen.

    Rückgabe:
        None. Verändert sim_state und die Achsen direkt.
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

    # ── Spring-Layout für jeden Graphen berechnen (Knotenpositionen im Plot) ──
    # spring_layout positioniert eng verbundene Knoten räumlich näher beieinander
    layouts = [
        nx.spring_layout(g, seed=seed)
        for g in graphs
    ]

    # ── Vollständige Simulation für alle drei Topologien vorberechnen ─────────
    histories  = []
    start_days = []
    for g in graphs:
        hist, sday = run_simulation(g, beta, gamma_base, seed, extended)
        histories.append(hist)
        start_days.append(sday)

    # ── Ergebnisse in sim_state speichern ─────────────────────────────────────
    sim_state["graphs"]     = graphs
    sim_state["layouts"]    = layouts
    sim_state["histories"]  = histories
    sim_state["start_days"] = start_days
    # max_frames = kürzeste Simulation − 1 (für synchronen Gleichlauf aller drei)
    sim_state["max_frames"] = min(len(h) for h in histories) - 1

    # Animation zurücksetzen und ersten Frame zeichnen
    sim_state["current_frame"] = 0
    sim_state["playing"]       = False
    btn_play.label.set_text("▶  Play")
    draw_frame(0)


def toggle_play(event):
    """
    Schaltet die Animation zwischen Play und Pause um.

    Wenn die Animation läuft, wird sie durch diesen Aufruf pausiert.
    Wenn sie pausiert ist, wird sie gestartet.
    Wurde das Ende der Simulation erreicht (letzter Frame), springt ein
    erneuter Play-Klick automatisch zu Frame 0 zurück.

    Wurde noch keine Simulation berechnet, passiert nichts (Sicherheitscheck).

    Parameter:
        event: Matplotlib-Button-Klick-Event (wird nicht weiter ausgewertet).

    Rückgabe:
        None.
    """
    # Keine Simulation vorhanden? Dann nichts tun
    if sim_state["histories"][0] is None:
        return

    if sim_state["playing"]:
        # Animation pausieren
        sim_state["playing"] = False
        btn_play.label.set_text("▶  Play")
    else:
        # Am Ende der Simulation? Dann von vorne beginnen
        if sim_state["current_frame"] >= sim_state["max_frames"]:
            sim_state["current_frame"] = 0
        # Animation starten
        sim_state["playing"] = True
        btn_play.label.set_text("⏸  Pause")

    # Canvas neu zeichnen (aktualisiert Beschriftung des Buttons)
    fig.canvas.draw_idle()


def on_reset(event):
    """
    Stoppt die laufende Animation und berechnet alle drei Simulationen neu.

    Diese Funktion sollte nach einer Slider-Änderung aufgerufen werden.
    Sie liest die neuen Parameterwerte aus, erstellt neue Graphen und führt
    alle Simulationen vollständig durch. Anschließend wird Frame 0 angezeigt.

    Parameter:
        event: Matplotlib-Button-Klick-Event (wird nicht weiter ausgewertet).

    Rückgabe:
        None.
    """
    # Laufende Animation zuerst stoppen
    sim_state["playing"] = False
    btn_play.label.set_text("▶  Play")
    # Alle drei Simulationen neu aufbauen und zeichnen
    build_all_simulations()


def on_extended_toggle(label):
    """
    Callback für die Extended-Mode-Checkbox – schaltet den Modus ein oder aus
    und berechnet die Simulationen sofort neu.

    Im Extended Mode werden zwei saisonale Umweltfaktoren aktiviert:
        Wintereffekt (Tage 1–90 und 350–365):
            Genesungsrate gamma wird um 20 % gesenkt (gamma × 0.8).
        Feiertagseffekt (±3 Tage um die Feiertage in HOLIDAYS):
            Infektionsrate beta wird um 30 % erhöht (beta × 1.3).

    Parameter:
        label (str): Bezeichnung der angeklickten Checkbox. Da nur eine
                     Checkbox vorhanden ist, wird der Parameter nicht
                     weiter ausgewertet.

    Rückgabe:
        None.
    """
    # Aktuellen Zustand der Checkbox auslesen (get_status gibt eine Liste zurück)
    sim_state["extended_mode"] = chk_extended.get_status()[0]
    # Simulation mit dem neuen Modus neu berechnen und zeichnen
    build_all_simulations()


def advance_animation(frame):
    """
    Animationsschritt-Callback – wird von FuncAnimation in jedem Zeitintervall
    aufgerufen und rückt die Animation um einen Frame vor.

    Wenn die Animation aktiv ist (sim_state["playing"] == True), wird
    current_frame um 1 erhöht und draw_frame() aufgerufen. Hat die Simulation
    ihr Ende erreicht, wird die Animation automatisch gestoppt und der
    Play-Button zurückgesetzt.

    Diese Funktion läuft kontinuierlich im Hintergrund (alle 150 ms), führt
    aber nur dann Aktionen aus, wenn playing == True ist.

    Parameter:
        frame (int): Von FuncAnimation automatisch übergebener interner Zähler.
                     Wird hier ignoriert – der eigene Zähler sim_state["current_frame"]
                     wird stattdessen verwendet.

    Rückgabe:
        None.
    """
    # Nur aktiv, wenn die Animation tatsächlich läuft
    if not sim_state["playing"]:
        return

    # Nächsten Frame anzeigen, solange noch Frames vorhanden sind
    if sim_state["current_frame"] < sim_state["max_frames"]:
        sim_state["current_frame"] += 1
        draw_frame(sim_state["current_frame"])
    else:
        # Letzten Frame erreicht: Animation automatisch stoppen
        sim_state["playing"] = False
        btn_play.label.set_text("▶  Play")
        fig.canvas.draw_idle()


# ── Callbacks an die Widgets verknüpfen ──────────────────────────────────────
btn_play.on_clicked(toggle_play)
btn_reset.on_clicked(on_reset)
chk_extended.on_clicked(on_extended_toggle)

# ── FuncAnimation einrichten ──────────────────────────────────────────────────
# interval=150: Jeder Frame wird 150 ms lang angezeigt (~6–7 Frames/Sekunde)
# cache_frame_data=False: Kein Caching, da der Zustand extern in sim_state verwaltet wird
# Die Variable muss global gehalten werden, sonst wird das Objekt vom
# Garbage Collector gelöscht und die Animation stoppt sofort.
anim = FuncAnimation(fig, advance_animation, interval=150, cache_frame_data=False)

# ── Farbkodierungs-Legende ────────────────────────────────────────────────────
# Erklärt die Bedeutung der Knotenfarben im unteren rechten Bereich
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
    "① Slider anpassen   ②  '↺ Reset' klicken   ③  '▶ Play' klicken",
    ha="center", va="bottom", fontsize=8, color="#666666",
)

# ── Initiale Simulation beim Programmstart ────────────────────────────────────
# Beim Start der Anwendung wird sofort eine Simulation mit den Standard-Sliderwerten
# berechnet und dargestellt, damit das Fenster nicht leer ist.
build_all_simulations()

# ── Matplotlib-Fenster öffnen und Ereignisschleife starten ───────────────────
plt.show()
