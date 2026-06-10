# ODD-Protokoll: SIR-Netzwerksimulation

Dieses Dokument beschreibt das implementierte Modell nach ODD (Overview, Design Concepts, Details) und entspricht dem aktuellen Stand von main.py.

## I. Overview

### 1. Purpose

Ziel des Modells ist der Vergleich der Epidemiedynamik eines SIR-Prozesses auf drei unterschiedlichen Netzwerktopologien:

- Erdős-Rényi
- Watts-Strogatz
- Barabási-Albert

Untersucht werden insbesondere Unterschiede in Ausbreitungsgeschwindigkeit, Peak-Verhalten und Simulationsdauer bei gleichen Basisparametern.

### 2. Entities, State Variables, and Scales

#### 2.1 Entitäten

- Knoten: Individuen einer geschlossenen Population
- Kanten: Kontakte zwischen Individuen
- Graphen: je ein Netzwerk pro Topologie

#### 2.2 Zustandsvariablen

Knoten-Zustand:

- S: Susceptible (anfällig)
- I: Infected (infiziert)
- R: Recovered (genesen)

Globale Parameter:

- $N$: Anzahl der Knoten
- $\beta$: Basis-Infektionswahrscheinlichkeit pro Kontakt und Tag
- $\gamma$: Basis-Genesungswahrscheinlichkeit pro infiziertem Knoten und Tag
- avg_degree: Zielwert für mittleren Knotengrad
- seed: Zufallsstartwert
- extended_mode: Aktivierung saisonaler Effekte

Abgeleitete Tagesparameter:

- $\beta_{\text{eff}}$
- $\gamma_{\text{eff}}$

#### 2.3 Skalen

- Zeit: diskret, 1 Zeitschritt = 1 Tag
- Zeithorizont: maximal 365 Tage
- Kalenderdarstellung: zyklische Tageszählung 1 bis 365
- Raum: Netzwerkstruktur, keine explizite Geometrie

### 3. Process Overview and Scheduling

Die Dynamik erfolgt synchron pro Tag:

1. Aktuelle Zustände werden gelesen.
2. Für alle infizierten Knoten werden Infektion und Genesung stochastisch ausgewertet.
3. Alle Zustandsänderungen werden gleichzeitig übernommen.

Infektion (pro infiziertem Knoten und suszeptiblem Nachbarn):

$P_{\text{inf}} = \beta_{\text{eff}}$

Genesung (pro infiziertem Knoten):

$P_{\text{rec}} = \gamma_{\text{eff}}$

Simulationsende:

- entweder nach 365 Tagen
- oder früher bei $I(t)=0$

## II. Design Concepts

### 1. Basic Principles

Das Modell koppelt SIR-Übergänge mit expliziter Kontaktstruktur. Die Topologie bestimmt, welche Kontakte möglich sind und beeinflusst dadurch die globale Dynamik.

### 2. Emergence

Die Kurven $S(t)$, $I(t)$ und $R(t)$ entstehen aus lokalen Nachbarschaftsinteraktionen und stochastischen Übergängen.

### 3. Stochasticity

Zufall wird eingesetzt für:

- Netzwerkrealisierung (je Topologie)
- Starttag im Kalenderjahr
- Patient Zero
- tägliche Infektions- und Genesungsereignisse

### 4. Interaction

Interaktionen finden ausschließlich entlang existierender Kanten statt. Es gibt keine Fernkontakte außerhalb des Netzwerks.

### 5. Adaptation

Es gibt keine adaptive Verhaltensänderung von Agenten. Optional verändert extended_mode nur die effektiven Parameter über Kalenderlogik.

### 6. Observation

Pro Tag werden die globalen Zustandsgrößen gezählt:

- $S(t)$
- $I(t)$
- $R(t)$

Zusätzlich werden Kalenderinformationen für die Visualisierung genutzt (Monate, Jahreszeit, Feiertagsperioden).

## III. Details

### 1. Initialization

Für jede Topologie wird ein eigener Graph erzeugt, jeweils mit denselben Eingabeparametern.

Topologie-spezifische Erzeugung:

1. Erdős-Rényi
   $p = \frac{\text{avg\_degree}}{N-1}$, begrenzt auf $[0,1]$.

2. Watts-Strogatz
   Nachbarschaftsparameter $k$ aus avg_degree (gerade, mindestens 2, höchstens $N-1$), Rewiring-Wahrscheinlichkeit 0.1.

3. Barabási-Albert
   $m = \max(1, \text{round}(\text{avg\_degree}/2))$, begrenzt auf $N-1$.

Alle Knoten starten in Zustand S. Ein zufälliger Knoten wird als Patient Zero auf I gesetzt. Der Starttag wird zufällig in $\{1,\dots,365\}$ gewählt.

### 2. Submodels

#### 2.1 Seasonal and Holiday Modifier

Wenn extended_mode deaktiviert ist:

- $\beta_{\text{eff}}=\beta$
- $\gamma_{\text{eff}}=\gamma$

Wenn extended_mode aktiviert ist:

1. Wintertage: $d \le 90$ oder $d \ge 350$

$\gamma_{\text{eff}} = 0.8 \cdot \gamma$

2. Feiertagsperioden: Abstand zu definierten Feiertagen höchstens 3 Tage (zyklisch über Jahresgrenze)

$\beta_{\text{eff}} = 1.3 \cdot \beta$

Anschließend werden beide Werte auf $[0,1]$ begrenzt.

#### 2.2 Infection Submodel

Für jeden infizierten Knoten wird jeder Nachbar geprüft. Nur Nachbarn in Zustand S können infiziert werden. Die Bernoulli-Entscheidung nutzt $P_{\text{inf}}$.

#### 2.3 Recovery Submodel

Für jeden infizierten Knoten wird eine Bernoulli-Entscheidung mit $P_{\text{rec}}$ gezogen. Bei Erfolg wechselt der Zustand nach R.

#### 2.4 Observation and Visualization Submodel

Die Anwendung visualisiert parallel:

- oben: Netzwerkzustand je Topologie
- unten: Zeitreihen von $S(t)$, $I(t)$ und $R(t)$

Monatstexte auf der x-Achse werden aus dem Starttag und der Kalendertagsfortschreibung abgeleitet.
