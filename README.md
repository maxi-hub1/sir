# SIR-Netzwerksimulation

Interaktive Simulation einer SIR-Epidemie auf drei Netzwerktopologien mit direktem visuellen Vergleich:

- Erdős-Rényi
- Watts-Strogatz
- Barabási-Albert

Die Anwendung zeigt parallel die Netzwerkzustände und die zeitlichen SIR-Kurven. Parameter können während der Laufzeit per UI angepasst werden.

## Features

- Drei Topologien im Parallelvergleich
- Diskrete, synchrone SIR-Dynamik
- Reproduzierbare Läufe über Seed
- Erweiterter Modus (Extended Mode) mit saisonalen Effekten
- Live-Recompute bei Parameteränderungen

## Voraussetzungen

- Python 3.13 oder neuer
- Abhängigkeiten:
  - matplotlib
  - networkx
  - numpy

## Installation

### Option A: mit uv (empfohlen)

1. Umgebung erstellen und aktivieren:

   uv venv
   source .venv/bin/activate

2. Abhängigkeiten installieren:

   uv sync

### Option B: mit pip

1. Virtuelle Umgebung erstellen und aktivieren:

   python3 -m venv .venv
   source .venv/bin/activate

2. Abhängigkeiten installieren:

   pip install -e .

## Start

Im Projektordner ausführen:

python3 main.py

Danach öffnet sich ein Matplotlib-Fenster mit der interaktiven Oberfläche.

## UI und Bedienung

### Slider

- N (Knoten): Anzahl der Knoten
- Avg. Degree: mittlerer Vernetzungsgrad
- Beta: Basis-Infektionswahrscheinlichkeit
- Gamma Base: Basis-Genesungswahrscheinlichkeit
- Seed: Zufallsstartwert

Jede Slider-Änderung startet eine vollständige Neuberechnung aller drei Topologien.

### Buttons

- Play/Pause: startet oder pausiert die Animation
- Reset: berechnet mit aktuellen Parametern neu und springt auf Frame 0

### Checkbox

- Extended Mode:
  - Wintereffekt (Tag 1-90 und 350-365): gamma wird mit 0.8 skaliert
  - Feiertagseffekt (±3 Tage um definierte Feiertage): beta wird mit 1.3 skaliert

## Simulationslogik

### Zustände

- S: Susceptible
- I: Infected
- R: Recovered

### Tagesupdate (synchron)

1. Infizierte Knoten prüfen suszeptible Nachbarn und infizieren mit Wahrscheinlichkeit beta_eff.
2. Infizierte Knoten genesen mit Wahrscheinlichkeit gamma_eff.
3. Zustandswechsel werden gleichzeitig übernommen.

Die Simulation stoppt, wenn keine infizierten Knoten mehr vorhanden sind oder spätestens nach 365 Tagen.

## Visualisierung verstehen

- Obere Reihe: Netzwerke je Topologie (Knotenfarben nach S/I/R)
- Untere Reihe: S(t), I(t), R(t)-Kurven derselben Topologie
- Titel je Netzwerk zeigt:
  - Simulations-Tag
  - Kalendertag
  - Jahreszeit
  - optional Feiertagshinweis im Extended Mode

## Typischer Workflow

1. Seed setzen
2. N und Avg. Degree einstellen
3. Beta/Gamma variieren
4. Optional Extended Mode aktivieren
5. Mit Play den Verlauf beobachten
6. Mit Reset neue Läufe starten

## Hinweise

- Bei großen N kann die Neuberechnung kurz dauern.
- Gleicher Seed und gleiche Parameter erzeugen reproduzierbare Läufe.
- Unterschiede zwischen Topologien sind erwarteter Kern des Experiments.

## Projektdateien

- sir_simulation.py: Simulation und UI
- report.md: klassischer Projektbericht
- odd-protocol.md: ODD-Dokumentation
- pyproject.toml: Projekt- und Abhängigkeitsdefinition
