# SIR-Epidemie auf Netzwerken
Gruppe 2        Maximilian HUBMANN, Ivan JURIC, Jacob MENN, Filip SARCEVIC, Florian SCHWAB
## Abstrakt

Dieses Projekt untersucht, wie sich eine SIR-Epidemie auf drei unterschiedlichen Netzwerktopologien ausbreitet: Erdős-Rényi, Watts-Strogatz und Barabási-Albert. Die Simulation ist als interaktive Matplotlib-Anwendung umgesetzt und berechnet alle drei Topologien parallel mit identischen Basisparametern. Die Zustandsübergänge erfolgen diskret und synchron in den Zuständen Susceptible (S), Infected (I) und Recovered (R). Zusätzlich kann ein Extended Mode aktiviert werden, der saisonale Effekte modelliert: reduzierte Genesungsrate im Winter und erhöhte Infektionsrate in Feiertagsperioden. Die Ergebnisse zeigen, dass die Netzwerkstruktur einen deutlichen Einfluss auf Ausbreitungsdynamik, Peak-Verhalten und Gesamtdauer hat.

## 1. Einleitung

Die Ausbreitung infektiöser Krankheiten lässt sich als dynamischer Prozess auf einem Kontaktnetzwerk beschreiben. Im Gegensatz zu homogen gemischten Modellen, die klassische Differentialgleichungen nutzen, berücksichtigt ein Netzwerkmodell explizit, welche Individuen tatsächlich Kontakt haben. Damit wird die Topologie selbst zu einem zentralen Einflussfaktor und ermöglicht eine realistischere Abbildung von Kontaktmustern.

Reale Kontaktstrukturen sind nie zufällig verteilt. Sie entstehen durch Familie, Arbeitsplatz, Freizeit und räumliche Nähe, wodurch manche Personen viele Kontakte und andere wenige haben. Manche Kontakte liegen in engen Gruppen, andere verbinden weit entfernte Teile eines sozialen Netzwerks. Ein klassisches homogenes Mischungsmodell ignoriert diese Heterogenität vollständig.

Das hier verwendete SIR-Modell beschreibt jede Person durch genau einen epidemiologischen Zustand:

- S: suszeptibel (anfällig, kann infiziert werden)
- I: infiziert und infektiös (kann andere anstecken)
- R: genesen (im Modell nicht erneut infizierbar, gilt als immun)

Untersucht wird die zentrale Frage: Wie stark unterscheiden sich Epidemieverläufe, wenn die Kontaktstruktur variiert, aber die epidemiologischen Basisparameter gleich bleiben?

## 2. Methoden

### 2.1 Modellstruktur

Die Simulation arbeitet in diskreten Zeitschritten (1 Schritt = 1 Tag). Zu Beginn sind alle Knoten im Zustand S. Ein zufällig gewählter Knoten wird als Patient Zero im Zustand I initialisiert. Zusätzlich wird ein zufälliger Starttag im Kalenderjahr (1–365) gewählt, um kalendarische Effekte zu ermöglichen.

Für die Reproduzierbarkeit wird ein lokaler Zufallsgenerator mit dem zentralen Slider-Seed initialisiert. Dieser Seed ist die einzige Quelle aller stochastischen Prozesse (Netzwerkerzeugung, Layout, Starttag, Patient Zero, tägliche Übergänge). Damit gilt: identischer Seed + identische Parameter erzeugen identische Ergebnisse.

Für jeden Tag gilt eine synchrone Aktualisierung in zwei Phasen:

1. **Auswertungsphase**: Auf Basis des Zustands zu Tagesbeginn werden Infektionen und Genesungen stochastisch ausgewertet.
2. **Commit-Phase**: Alle Zustandsänderungen werden gleichzeitig übernommen.

Diese Synchronität verhindert künstliche Reihenfolgeabhängigkeiten, die entstehen würden, wenn ein bereits infizierter Knoten im selben Tag weitere Knoten ansteckt.

### 2.2 Netzwerktopologien

Die drei Netzwerke werden mit NetworkX erzeugt und sind strukturell völlig unterschiedlich:

**1. Erdős-Rényi-Modell**

Kontaktkanten entstehen mit Wahrscheinlichkeit

$$p = \frac{\text{avg\_degree}}{N-1}$$

wobei $N$ die Knotenzahl ist. Das Ergebnis ist ein homogenes, zufälliges Netzwerk ohne besondere Cluster oder Hubs. Der durchschnittliche Knotengrad ist über die Population relativ gleichmäßig verteilt.

**2. Watts-Strogatz-Modell**

Beginnt als regulärer Ringgitter mit Nachbarschaftsparameter $k$ (gerade, mindestens 2, maximal $N-1$). Jede Kante wird dann mit Wahrscheinlichkeit 0.1 „umverdrahtet". Das Ergebnis ist ein Small-World-Netzwerk mit hohem Clusterkoeffizient (enge lokale Gruppen) und dennoch kurzen durchschnittlichen Pfadlängen zwischen beliebigen Knoten.

**3. Barabási-Albert-Modell**

Wachstumsmodell mit bevorzugter Anbindung. Neue Knoten verbinden sich mit Wahrscheinlichkeit proportional zum bestehenden Knotengrad. Dadurch entstehen wenige hochvernetzte „Hubs" und viele schwach vernetzte Knoten. Die Gradverteilung folgt einem Power-Law. Hubs sind strukturell kritisch für die Netzwerkverbindung.

### 2.3 Zustandsübergänge und Infektionsmechanismus

In jedem Zeitschritt werden folgende Regeln durchgeführt:

**Infektion**: Für jeden infizierten Knoten wird jeder suszeptible Nachbar mit Wahrscheinlichkeit

$$P_{\text{inf}} = \beta_{\text{eff}}$$

infiziert. Ein neu infizierter Knoten wird erst im nächsten Schritt als infektiös wirksam.

**Genesung**: Für jeden infizierten Knoten wird mit Wahrscheinlichkeit

$$P_{\text{rec}} = \gamma_{\text{eff}}$$

entschieden, ob er in den Zustand R übergeht. Dies ist eine unabhängige Entscheidung pro Knoten.

Alle Wahrscheinlichkeitswerte werden auf den Bereich $[0,1]$ begrenzt, um numerische Ungültigkeiten zu vermeiden.

### 2.4 Extended Mode mit saisonalen Effekten

Im Basismodus gelten die konstanten Parameter:

$$\beta_{\text{eff}} = \beta, \quad \gamma_{\text{eff}} = \gamma$$

Im Extended Mode werden zusätzliche Modulationen angewendet:

**Wintereffekt** (Kalendertage 1–90 und 350–365):

$$\gamma_{\text{eff}} = 0.8 \cdot \gamma$$

Die Interpretation ist, dass in Wintermonaten (Dezember bis März) das Immunsystem durch Kältestress und Lichtmangel geschwächt wird, wodurch Infizierte länger infektiös bleiben.

**Feiertagseffekt** (innerhalb von ±3 Tagen um definierte Feiertage):

$$\beta_{\text{eff}} = 1.3 \cdot \beta$$

Die Interpretation ist, dass an Feiertagen und in den Puffertagen (Familienfeiern, Reisen, erhöhte Kontaktzahl) die Infektionswahrscheinlichkeit ansteigt.

Die Feiertagsperioden werden zyklisch über Jahresgrenzen behandelt.

### 2.5 Benutzeroberfläche und Parameter

Die interaktive Oberfläche zeigt alle drei Topologien nebeneinander oben (Netzwerkvisualisierung) und darunter (SIR-Kurven). Steuerelemente sind:

**Slider:**
- N: Knotenzahl (10–200, ganzzahlig)
- Avg. Degree: mittlerer Vernetzungsgrad (1–10, ganzzahlig)
- Beta: Basis-Infektionswahrscheinlichkeit (0.0–1.0)
- Gamma Base: Basis-Genesungswahrscheinlichkeit (0.0–1.0)
- Seed: Zufallsstartwert (0–999, ganzzahlig)

**Buttons:**
- Play/Pause: startet oder pausiert die Frame-Animation
- Reset: berechnet Simulationen mit aktuellen Parametern neu

**Checkbox:**
- Extended Mode: aktiviert/deaktiviert saisonale Effekte

Jede Slider-Änderung oder Checkbox-Änderung triggert eine vollständige Neuberechnung aller drei Topologien.

Der Seed-Slider (0–999) steuert dabei deterministisch alle Zufallsentscheidungen. Die Anwendung zeigt die seed-abhängigen Werte (Starttag, Patient Zero, Lauflänge je Topologie) zusätzlich im UI an.

### 2.6 Stop-Kriterium und Beobachtung

Ein Simulationslauf endet unter zwei Bedingungen:

1. **Naturales Aussterben**: Keine infizierten Knoten mehr vorhanden ($I(t)=0$)
2. **Zeitlimit**: Nach maximal 365 Tagen

Pro Tag werden folgende Größen beobachtet und gespeichert:

- $S(t)$: Anzahl suszeptibler Knoten
- $I(t)$: Anzahl infizierter Knoten
- $R(t)$: Anzahl genesener Knoten

Diese werden als Zeitreihen visualisiert mit Monatsbeschriftung auf der x-Achse für Kalendarreferenz.

## 3. Ergebnisse

Die Simulation zeigt konsistent unterschiedliche Dynamiken je nach Topologie, auch bei identischen Basisparametern.

**Erdős-Rényi-Netzwerk:**

Breitet sich relativ gleichmäßig aus, da das homogene Zufallsnetzwerk keine strukturellen Barrieren bietet. Es gibt keine dominanten Hubs. Die Peak-Höhe und -Timing variieren stochastisch mit dem Seed, folgen aber grob symmetrischen Mustern. Am Ende sind oft 60–80% infiziert oder genesen.

**Watts-Strogatz-Netzwerk:**

Die lokale Clusterstruktur führt zu phasenhafter Ausbreitung. Infektionen verbreiten sich zuerst innerhalb lokaler Gruppen, erreichen aber nicht sofort andere Gruppen. Long-Range-Verbindungen ermöglichen verzögerte Ausbreitung. Die Gesamtdauer ist oft länger und der finale Anteil infizierter Knoten kleiner.

**Barabási-Albert-Netzwerk:**

Hubs beschleunigen die systemweite Verbreitung deutlich. Frühe Infektion eines Hubs führt zu rasanter Ausbreitung über seine Verbindungen. Dies erzeugt schnellere Peaks und höhere Peak-Höhen. Oft werden 85–95% der Population erreicht.

Der Unterschied zu ER und WS ist oft dramatisch: während diese teilweise lokale Begrenzung zeigen, erreicht BA rasch die Gesamtpopulation.

## 4. Diskussion

Die Implementierung bestätigt das theoretische Verständnis: Netzwerkstruktur ist ein eigenständiger Treiber der Epidemiedynamik. Dies zeigt, warum reale epidemiologische Modelle nicht von homogenen Mischungsannahmen ausgehen können.

**Rolle der Topologie:**

Das Barabási-Albert-Modell demonstriert drastisch, wie Hubs wirken: Sie sind Zentren für schnelle Ausbreitung. Im Gegensatz dazu wirken lokale Cluster im Watts-Strogatz-Modell wie Schutzbarrieren – nicht weil Infizierte weniger ansteckend wären, sondern weil die geometrische Struktur Ausbreitungspfade einengt.

Das Erdős-Rényi-Modell liegt dazwischen: es hat weniger Barrieren als WS, aber keine extremen Hubs wie BA. Es ist das neutrale Referenzmodell.

**Saisonale Effekte im Extended Mode:**

Der Extended Mode zeigt, dass zeitabhängige Parameter zusätzlich zur Topologie wirken. Im Winter kann eine Epidemie länger andauern. An Feiertagen kann lokales Anschwellen entstehen. Diese Effekte sind vereinfacht, aber machen sichtbar, dass externe Faktoren den Verlauf modulieren.

**Stochastische Variabilität:**

Stochastik bleibt ein zentraler Bestandteil des Modells, ist aber vollständig kontrolliert. Der zentrale Seed bestimmt deterministisch die Netzwerkinstanz, den Starttag, Patient Zero und alle täglichen Bernoulli-Entscheidungen. Derselbe Seed erzeugt daher denselben Verlauf; unterschiedliche Seeds erzeugen unterschiedliche, aber jeweils reproduzierbare Verläufe.

## 5. Conclusion and Limitations

Das Modell eignet sich hervorragend, um topologieabhängige Mechanismen der Epidemieausbreitung didaktisch und visuell nachvollziehbar zu machen. Die parallele Animation aller drei Topologien ermöglicht direkten Vergleich ohne Ablenkung.

Die Trennung zwischen Basismodus und Extended Mode unterstützt isolierten Vergleich struktureller und zeitabhängiger Effekte.

**Wichtige Grenzen:**

- Keine empirische Kalibrierung auf reale Krankheitsparameter
- Keine Alters- oder Risikogruppen
- Keine Interventionen (Impfung, Quarantäne, Isolation)
- Ein initiales Infektionsereignis nur
- Keine räumliche Geometrie, nur Netzwerkkonnektivität
- Vereinfachte Tagesdynamik, keine Substeps

Trotz dieser Grenzen erfüllt das Modell seinen Zweck fundamental: Es demonstriert, dass Netzwerkstruktur epidemiologische Dynamik stark beeinflusst. Dies ist ein wichtiger Erkenntnisgewinn für das Verständnis komplexer Systeme.

## Literatur

Barabási, A.-L., & Albert, R. (1999). Emergence of scaling in random networks. Science, 286(5439), 509–512.

Erdős, P., & Rényi, A. (1959). On random graphs. Publicationes Mathematicae, 6, 290–297.

Kermack, W. O., & McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics. Proceedings of the Royal Society A, 115(772), 700–721.

Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of small-world networks. Nature, 393, 440–442.


## Appendix A: ODD-Protokoll (SIR-Netzwerksimulation)

Dieses Appendix dokumentiert das implementierte Modell nach ODD (Overview, Design Concepts, Details) und entspricht dem aktuellen Stand von main.py.

### I. Overview

#### 1. Purpose

Ziel des Modells ist der Vergleich der Epidemiedynamik eines SIR-Prozesses auf drei unterschiedlichen Netzwerktopologien:

- Erdős-Rényi
- Watts-Strogatz
- Barabási-Albert

Untersucht werden insbesondere Unterschiede in Ausbreitungsgeschwindigkeit, Peak-Verhalten und Simulationsdauer bei gleichen Basisparametern.

#### 2. Entities, State Variables, and Scales

##### 2.1 Entitäten

- Knoten: Individuen einer geschlossenen Population
- Kanten: Kontakte zwischen Individuen
- Graphen: je ein Netzwerk pro Topologie

##### 2.2 Zustandsvariablen

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

##### 2.3 Skalen

- Zeit: diskret, 1 Zeitschritt = 1 Tag
- Zeithorizont: maximal 365 Tage
- Kalenderdarstellung: zyklische Tageszählung 1 bis 365
- Raum: Netzwerkstruktur, keine explizite Geometrie

#### 3. Process Overview and Scheduling

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

### II. Design Concepts

#### 1. Basic Principles

Das Modell koppelt SIR-Übergänge mit expliziter Kontaktstruktur. Die Topologie bestimmt, welche Kontakte möglich sind und beeinflusst dadurch die globale Dynamik.

#### 2. Emergence

Die Kurven $S(t)$, $I(t)$ und $R(t)$ entstehen aus lokalen Nachbarschaftsinteraktionen und stochastischen Übergängen.

#### 3. Stochasticity

Zufall wird eingesetzt für:

- Netzwerkrealisierung (je Topologie)
- Starttag im Kalenderjahr
- Patient Zero
- tägliche Infektions- und Genesungsereignisse

Die Zufallssteuerung ist vollständig seed-deterministisch: Der zentrale Seed wird konsistent an alle stochastischen Teilprozesse weitergegeben. In der Epidemielogik wird ein lokaler Generator (`random.Random(seed)`) vor der Ermittlung von Starttag und Patient Zero initialisiert, sodass keine unkontrollierten globalen Zufallsaufrufe die Reproduzierbarkeit beeinflussen.

#### 4. Interaction

Interaktionen finden ausschließlich entlang existierender Kanten statt. Es gibt keine Fernkontakte außerhalb des Netzwerks.

#### 5. Adaptation

Es gibt keine adaptive Verhaltensänderung von Agenten. Optional verändert extended_mode nur die effektiven Parameter über Kalenderlogik.

#### 6. Observation

Pro Tag werden die globalen Zustandsgrößen gezählt:

- $S(t)$
- $I(t)$
- $R(t)$

Zusätzlich werden Kalenderinformationen für die Visualisierung genutzt (Monate, Jahreszeit, Feiertagsperioden).

### III. Details

#### 1. Initialization

Für jede Topologie wird ein eigener Graph erzeugt, jeweils mit denselben Eingabeparametern.

Topologie-spezifische Erzeugung:

1. Erdős-Rényi
   $p = \frac{\text{avg\_degree}}{N-1}$, begrenzt auf $[0,1]$.

2. Watts-Strogatz
   Nachbarschaftsparameter $k$ aus avg_degree (gerade, mindestens 2, höchstens $N-1$), Rewiring-Wahrscheinlichkeit 0.1.

3. Barabási-Albert
   $m = \max(1, \text{round}(\text{avg\_degree}/2))$, begrenzt auf $N-1$.

Alle Knoten starten in Zustand S. Ein zufälliger Knoten wird als Patient Zero auf I gesetzt. Der Starttag wird zufällig in $\{1,\dots,365\}$ gewählt.

Für identische Seeds sind diese Werte (Patient Zero und Starttag) identisch reproduzierbar.

#### 2. Submodels

##### 2.1 Seasonal and Holiday Modifier

Wenn extended_mode deaktiviert ist:

- $\beta_{\text{eff}}=\beta$
- $\gamma_{\text{eff}}=\gamma$

Wenn extended_mode aktiviert ist:

1. Wintertage: $d \le 90$ oder $d \ge 350$

$\gamma_{\text{eff}} = 0.8 \cdot \gamma$

2. Feiertagsperioden: Abstand zu definierten Feiertagen höchstens 3 Tage (zyklisch über Jahresgrenze)

$\beta_{\text{eff}} = 1.3 \cdot \beta$

Anschließend werden beide Werte auf $[0,1]$ begrenzt.

##### 2.2 Infection Submodel

Für jeden infizierten Knoten wird jeder Nachbar geprüft. Nur Nachbarn in Zustand S können infiziert werden. Die Bernoulli-Entscheidung nutzt $P_{\text{inf}}$.

##### 2.3 Recovery Submodel

Für jeden infizierten Knoten wird eine Bernoulli-Entscheidung mit $P_{\text{rec}}$ gezogen. Bei Erfolg wechselt der Zustand nach R.

##### 2.4 Observation and Visualization Submodel

Die Anwendung visualisiert parallel:

- oben: Netzwerkzustand je Topologie
- unten: Zeitreihen von $S(t)$, $I(t)$ und $R(t)$

Monatstexte auf der x-Achse werden aus dem Starttag und der Kalendertagsfortschreibung abgeleitet.
