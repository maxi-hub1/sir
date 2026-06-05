# ODD-Protokoll: Netzwerkbasierte SIR-Epidemiesimulation

Dieses ODD-Protokoll (Overview, Design Concepts, Details) folgt dem standardisierten Dokumentationsschema für agenten- und systembasierte Modelle nach Grimm et al. (2006; 2010). Es beschreibt ein stochastisches Epidemiemodell auf heterogenen Netzwerktopologien unter Berücksichtigung von Kantengewichtungen und saisonalen Effekten.

---

## I. Overview (Übersicht)

### 1. Purpose (Zielsetzung)
Das Modell dient dem quantitativen Vergleich der Ausbreitungsdynamik einer Infektionskrankheit innerhalb von drei strukturell unterschiedlichen Systemarchitekturen. Ziel ist es zu analysieren, wie mathematische Topologiemuster (Zufallsnetze vs. Small-World-Phänomene vs. skalenfreie Netze) bei identischen epidemiologischen Basisparametern die Resilienz, die Ausbreitungsgeschwindigkeit und den Scheitelpunkt der Infektionskurve beeinflussen.

Zusätzlich evaluiert das Modell zwei Erweiterungen des klassischen Modells:
* Den Einfluss von Kontakthäufigkeiten mittels stochastischer Kantengewichtung.
* Den Einfluss externer Umweltfaktoren über eine saisonale Steuerung der Genesungsrate.

### 2. Entities, State Variables, and Scales (Entitäten, Zustandsvariablen und Skalen)

#### A. Globale Ebene (Das Gesamtsystem)
Das System aggregiert die Gesamtpopulation und steuert die globalen Rahmenbedingungen über die Zeitachse.
* `current_time` ($t \in \mathbb{N}_{\ge 0}$): Diskrete Zeitschritte, wobei ein Zeitschritt exakt einem Tag entspricht. Maximalwert: 365 Tage.
* `season` ($\in \{\text{Winter}, \text{Frühling}, \text{Sommer}, \text{Herbst}\}$): Dynamischer Zustand, abgeleitet aus $t$.
* `topology_type` ($\in \{\text{Erdős-Rényi}, \text{Watts-Strogatz}, \text{Barabási-Albert}\}$): Bestimmt das zugrundeliegende System.
* `weighted_mode` ($\in \{\text{True}, \text{False}\}$): Boolescher Schalter zur Aktivierung der heterogenen Kontakthäufigkeiten.
* `random_seed` ($\in \mathbb{Z}$): Gewährleistet die deterministische Reproduzierbarkeit stochastischer Prozesse.

#### B. Agenten-Ebene (Die Knoten / Personen)
Die Entitäten repräsentieren Individuen innerhalb einer geschlossenen Population von $N = 500$ (skalierbar über eine globale Konstante).
* `id` ($\in \mathbb{N}$): Eindeutiger Identifikator des Knotens ($0 \le \text{id} < N$).
* `state` ($\in \{S, I, R\}$): Der epidemiologische Zustand eines Agenten:
  * **Susceptible ($S$):** Gesund, nicht infiziert, empfänglich für den Erreger.
  * **Infected ($I$):** Aktiv infiziert und infektiös für Nachbarknoten.
  * **Recovered ($R$):** Genesen, dauerhaft immunisiert. Keine Reinfektion möglich.
* `next_state` ($\in \{S, I, R\}$): Temporärer Pufferzustand zur Vermeidung von Berechnungsartefakten während der synchronen Aktualisierung.

#### C. Netzwerk-Ebene (Die Kanten / Kontakte)
Kanten repräsentieren die soziale oder physische Interaktionsstruktur zwischen den Agenten.
* `source_id` / `target_id`: Verknüpfung der beteiligten Agenten.
* `weight` ($w_e \in [0, 1]$): Repräsentiert die relative Kontakthäufigkeit.
  * *Wenn `weighted_mode` = False:* $w_e = 1.0$ (homogene Kontakte).
  * *Wenn `weighted_mode` = True:* $w_e = \frac{X}{365}$, wobei $X \in [1, 365]$ die simulierten Begegnungstage pro Jahr darstellt.

---

### 3. Process Overview and Scheduling (Prozessübersicht und Ablaufplanung)

Die Simulation läuft in einer diskreten Zeitschleife. Ein globaler Zeitschritt ($t \to t+1$) ist strikt in zwei Phasen unterteilt (synchrone Aktualisierung), um eine künstliche Signalübertragung innerhalb desselben Tages zu verhindern:

* **Phase 1: Stochastische Zustandsevaluation (Schleife über alle Knoten)**
  * Falls `state` == $I$: Der Knoten versucht, jeden verbundenen Nachbarn im Zustand $S$ mit der Wahrscheinlichkeit $P_{\text{inf}} = \beta \cdot w_e$ zu infizieren. Bei Erfolg wird der Zielknoten auf `next_state` = $I$ gesetzt.
  * Falls `state` == $I$: Der Knoten evaluiert seine eigene Genesung mit der tagesaktuellen Wahrscheinlichkeit $P_{\text{rec}} = \gamma_t$. Bei Erfolg wird `next_state` = $R$.
* **Phase 2: Zustands-Commit (Schleife über alle Knoten)**
  * Alle Knoten kopieren gleichzeitig den Wert aus `next_state` in ihren aktiven `state`.

---

## II. Design Concepts (Designkonzepte)

### 1. Basic Principles (Grundprinzipien)
Das Modell kombiniert die klassische Epidemiologie (SIR-Modell) mit der Graphentheorie. Es bricht mit der Annahme der homogenen Massenwirkungskinetik. Die Ausbreitung ist lokal beschränkt und direkt abhängig von der Netzwerktopologie:
* **Erdős-Rényi:** Homogene, zufällige Verteilung der Kontakte.
* **Watts-Strogatz:** Hohe lokale Clusterung bei kurzen durchschnittlichen Pfadlängen.
* **Barabási-Albert:** Extrem heterogene Struktur. Wenige Hubs besitzen eine extrem hohe Anzahl an Kanten.

### 2. Emergence (Emergenz)
Die globalen Epidemiekurven ($S(t), I(t), R(t)$) sind emergente Eigenschaften des Systems. Sie resultieren direkt aus dem Zusammenspiel der lokalen Netzwerkstruktur mit den stochastischen Infektionspfaden.

### 3. Adaptation & Interaction (Anpassung und Interaktion)
* **Interaktion:** Findet ausschließlich direkt zwischen topologisch verknüpften Knoten statt (Nachbarschaft ersten Grades).
* **Anpassung:** Das System passt sich über die Saisonalität an. Im Winter (Tag 0–90 und 270–365) sinkt die Genesungsrate $\gamma_t$ um 20%, was die effektive Krankheitsdauer verlängert.

### 4. Stochasticity (Stochastizität)
Stochastizität wird bei der Netzwerkkonstruktion, der Auswahl von Patient Null zum Startzeitpunkt ($t_{\text{start}}$) sowie bei den täglichen Infektions- und Genesungsprüfungen mittels Pseuduzufallszahlen angewendet.

### 5. Observation (Beobachtung)
Am Ende jedes Zeitschritts werden die globalen Summen von $S$, $I$ und $R$ berechnet und für die spätere grafische Auswertung in Zeitreihengespeichert.

---

## III. Details (Details)

### 1. Initialization (Initialisierung)
Zu Beginn der Simulation ($t = 0$) wird das System über folgende Schritte in einen definierten Ausgangszustand versetzt:
1. Generierung von drei Graphen ($N = 500$) über NetworkX (`erdos_renyi_graph`, `watts_strogatz_graph`, `barabasi_albert_graph`), kalibriert auf denselben mittleren Knotengrad.
2. Falls `weighted_mode` == True: Zuweisung eines zufälligen Kantengewichts $w_e = X/365$.
3. Alle Knoten starten mit `state` = $S$. Ein zufälliger Starttag $t_{\text{start}}$ wird gewählt, an dem ein zufälliger Knoten auf `state` = $I$ gesetzt wird.

### 2. Submodels (Submodelle)
* **Saisonalitäts-Modifikator:** Reduziert $\gamma_{\text{basis}}$ in Winterperioden.
* **Stochastischer Transmissions-Check:** Zieht eine Zufallszahl $r \sim \mathcal{U}(0,1)$ und infiziert, wenn $r \le \beta \cdot w_e$.
