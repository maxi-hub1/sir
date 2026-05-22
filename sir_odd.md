# 1. Purpose Patterns

Wir wollen wissen wie man die Ausbreitung einer Infektionskrankheit in einer Population simulieren kannn, deren Kontakte durch ein Netzwerk beschrieben werden.

Untersucht werden insbesondere:
- die Geschwindigkeit der Ausbreitung
- die maximale Anzahl gleicher Infizierter
- die Gesamtzahl der infizierten Personen am Ende der Simulation

# 2. Entities, State Variables, Scales

### Entities 


Knoten- Eine Person in der Population
Kante- Ein Kontakt zwischen zwei Personen
Netzwerke- Gesamtheit aller Personen und Kontakte

### State variables

 "state" - Epidemologischer Zustand "S","I", oder "R"
 "neighbors" - Liste der direkt verbundenen Nachbarn
 "degree" - Anzahl der Kontankte eines Knotens 
 "time_infected" Zeit seit der Infektion 

 Epidemologische Zustände:

 "S" - gesund, aber ansteckbar
 "I" - infiziert und ansteckend
 "R" - recovered - nicht mehr ansteckend und immun

 globale Variablen:

 "network_type" - Typ des Netzwerk 
 "N" - Anzahl der Knoten 
 "edges" - Menge aller Kontakte
 "average_degree" durchschnittliche Anzahl an Kontakten
 "seed" - Zufallswert zur Reproduzierbarkeit 

### Scales

Die Simulation läuft in diskreten Schritten. 1 Tag = 1 Zeitschritt

Der Raum des Modells ist das Netzwerk 

Geschlossene Population. Keine Geburten , Todesfölle, Migration oder Infektionen von außen


# 3. Process overview and scheduling
Pro Zeitschritt drei Hauptprozesse
1.Infektion
Jeder suszeptible Knoten prüft wie viele infizierte Nachbar er hat-> Infektionswahrscheinscheinlichkeit abgeleitet-> Wahrscheinlichkeit das Knoten von s auf i wechselt 

2.Genesung
Jeder infizierte Knoten kann mit Wahrscheinlichkeit p genesen -> state i auf r

3.Beobachtung 
Nach jedem Zeitschritt werden Anzahlen von s , i und r gespeichert 

### Schedulung

Die Aktualisierung erfolgt synchron
1.alle möglichen neuen Infizierten berechnet
2.alle möglichen neuen Genesungen brechnet
3.alle  neuen Zustände gleichzeitig aktualisiert
4.Beobachtungen werden gespeichert




# 4. Design Concepts

Basic Principles: Das Modell basiert auf dem SIR Modell.

Emergence: Der Epidemieverlauf entsteht durch lokale Infektionen und lokale Genesungen#

Adaption: Agenten passen ihr Verhalten nicht an

Objecitves: Agenten verfolgen keine Ziele, lernen nicht und machen keine Vorhersagen 

Learning: Agenten lernen nicht 

Predictions: Agenten berücksichtigen nur direkte Nachbarn

Sensing: Infizierte können suszeptible Nachbarn anstecken

Interactions: Infizierte Knoten können suszeptible Nachbarn mit Wahrscheinlichkeit beta anstecken.

Stochasticity: Zufall bei Netzwerkbildung, Startinfizierten, INfetkionen und Genesungen

Collectives: Es gibt keine aktiven Gruppen, aber Cluster können durch die Netzwerkstruktur entstehen

Beobachtet werden S(t), I(t) und R(t) 

# 5. Initialisierung

Zu Beginn werden Parameter festgelegt.

Anschließend wird das Netzwerk erzeugt 

Beim Erös - Renyi Netzwerk existiert jede mögliche Kante zwischen zwischen zwei Knoten mit einer Wahrscheinlichkeit "p"

Beim Watts - Strogatz - Netzwerk werden die Knoten zunächst lokal verbunden. Einige Kanten werden mit einer Wahrscheinlichkeit "rewiring_p" umgedrahtet.

Das Barabisi - Netzwerk wächst schrittweise. Neue Knoten verbinden sich bevorzugt mit bereits stark vernetzten Knoten.

#  Input Data
Alle benötigten Daten werden werden als Parameter bei der Initialisierung festgelegt

# 7. Submodels 

### Networksubmodels 
Das Netzwerk legt fest, welche Personen miteinander Kontakt haben.(Erös - Renyi, Watts - Strogatz oder Barabisi - Netzwerk)

### Infection submodels

Ein suszeptibler Knoten kann durch infizierte Nachbarn angesteckt werden. 
Hat ein suszeptibler Knoten "k" infizierte Nachbarn, dann berechnet sich die Infektionswahrscheinlichkeit als:
P(\text{Infektion}) = 1 - (1 - \beta)^k

###  Recovery submodel

Ein infizierter Knoten kann pro Zeitschritt genesen. Die Genesungswahrscheinlichkeit lautet:
P(Genesung)=γ

### observation

Nach jedem werden die folgenden Zustände gezählt 

S(t)= Anzahl der suszeptiblen Personen
I(t)= Anzahl der infizierten Personen 
R(t)= Anzahl der genesenen Personen 

Außerdem können wichtige Kennzahlen berechnet werden 

I_max - maximale Anzahl der infizierten Knoten
t_peak - Zeitpunkt des Infektionspeaks



