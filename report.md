# SIR-Epidemie auf Netzwerken

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

Der Seed bestimmt Patient Zero, Starttag und Netzwerkinstanz. Derselbe Seed erzeugt reproduzierbare Läufe. Unterschiedliche Seeds zeigen natürliche Variabilität. Dies ist realistisch: reale Epidemien sind stochastische Prozesse.

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