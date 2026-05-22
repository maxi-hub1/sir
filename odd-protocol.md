# SIR-Epidemie auf Netzwerken ODD Beschreibung 
Dieses Protokoll behandelt die systematische Unterscheidung von anfällig- infizierten- genesenen Krankheitssytemen.
Wie dem Erdös-Renyi-Zufallsnetz, Watts-Strogatz-Small-World und skalenfreies Barabasi-Alber-Netz.

## 1. Purpose and Patterns 
Das Modell wird entworfen um die unterschieldichen Netzwerk-Topoliegen einer SIR- Epidemie zu vergleichen. 
In diesem Modell gehen wir davon aus das es nicht nur eine Ansteckungsgefahr gibt und jeder jeden anstecken kann.
Sondern wir betrachten die Personen als einzige Knoten welche Freundschaften und Kontakte (Nimdumgstücke) zu anderen personen haben.

## 2. Entities, State Variables, and Scales 
Wir nutzen eine Person als Agent, die durch Kanten bzw. Verbindungen zu anderen Personen connceted sind.
- *beta* Wahrscheinlichkeit suszeptiblen Personen werden infeziert
- *gamma* Wahrscheinlichkeit Infezierte genesen

Zeitverlauf ein Jahr jeder Tag ist ein timestep
- TIMESTEPS 365
an Feiertagen, Ferien steigt die Wahrscheinlichkeit KOnttakt zu anderen Personen.


## 3. process Overview and Scheduling

## 4. Design Concepts

## 5. Initialization

## 6. Input Data

## 7. Submodels

