# SIR- Epidemie auf Netzwerken
Das Programm soll 'susceptible-infected-recovered' - Epedemien anhand folgender Netzwerken festlegen:
**Erdös-Renyi-Zufallsnetz**:
- Homogenität: Die meisten Knoten haben etwa gleich viele Verbindungen
- Clustering kaum vorhanden 
- Sir-Dynamik: gleichmäßiges Netz -> eindeutige Epedemieschwellen

**Watts-Sttrognatz-Small-World-Netz**:
- Startpunkt: Ringgitter z.b. Nachabrn sind untereinander verbunden 
- hohes Clustering, lokae Ausbrüche
- hinzufügen von long-range- jumps, ein paar längere Kanten verbinden die Ringgitter
- Sir-Dynamik: lokale Aubrüche bleiben zuerst in der Umgebung, bei long-range-jumps -> weite Ausbreitung

**Barabasi-Albertt-Netz - Skalenfrei** 
- Knoten wird bekommt ständig neue Kanten
- Knoten mit vielen Verbindungen bekommen noch mehr "rich-get-richer"
- wenige Knoten mit vielen Verbindungen (Hub)
- viele KNoten mit wenige Verbindunge (1 bis zwei)
- Sir-Dynamik: Sytem bricht bei infezierten hub zusammen