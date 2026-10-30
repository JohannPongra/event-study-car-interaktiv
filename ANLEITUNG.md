# Event Study – interaktive Kopie

**Start: `START_INTERFACE.bat` doppelklicken.** Die Oberfläche öffnet sich im
Browser. Sie läuft ausschließlich auf diesem Computer und lässt sich unten
mit „Interface beenden“ schließen.

Diese Kopie enthält eigene Daten, Ergebnisse und eine eigene Python-Umgebung.
Die vereinfachte Fassung im bisherigen Ordner bleibt unverändert.

## Was du in der Oberfläche tun kannst

1. **Vorhandene Analyse neu durchführen:** „Analyse starten“ berechnet alle
   170 Berichte neu und prüft die zwölf Referenztabellen. Anschließend erscheinen
   die aktualisierten Grafiken. Dieser Weg braucht kein Internet.
2. **Neue Daten sammeln:** Unternehmen und Berichtszeitraum auswählen, Schlüssel
   für Alpha Vantage und SerpAPI eingeben und den Abruf starten. Jeder neue Abruf
   bekommt einen eigenen Datenbestand. Beim Erreichen des Anfragelimits den
   Bestand auswählen, Schlüssel erneut eingeben und „Abruf fortsetzen“ wählen.
3. **Neue Daten analysieren:** „Daten prüfen“ bereitet die Antworten auf und nennt
   fehlende Veröffentlichungszeiten. Für neue Transkripte einmal „FinBERT
   einrichten“ anklicken. Danach „Diesen Bestand analysieren“ starten.
4. **Ergebnisse vergleichen:** Unter „Berechneter Ergebnisstand“ einen Lauf
   auswählen. Grafiken, PDFs und vollständiger Ergebnisbericht sind verknüpft.
   Die 25 Bilder aus dem Word-Arbeitsstand bleiben separat sichtbar.

## Voraussetzungen für neue Daten

Du benötigst eigene API-Schlüssel und ein ausreichendes Kontingent. Der verwendete
Endpunkt für adjustierte Tageskurse ist bei Alpha Vantage eine Premiumfunktion.
Die Oberfläche zeigt Begrenzung und Pause für die Anfragen; es wird kein Tarif
gebucht. Schlüssel bleiben während des Auftrags im Arbeitsspeicher und werden
weder in den Einstellungen noch in den gespeicherten Anbieterantworten abgelegt.

Neue Transkripte werden mit dem lokalen FinBERT-Modell bewertet. Die einmalige
Einrichtung lädt dessen Python-Abhängigkeiten aus dem Internet und prüft danach
Modellladen und eine Vorhersage. Die Modellgewichte werden bei der Einrichtung aus der Originalquelle geladen; Version und Prüfsummen sind festgelegt.

Unbekannte Veröffentlichungszeiten werden nicht als nachbörslich angenommen.
Unter „Fehlende Veröffentlichungszeiten ergänzen“ lassen sich belegte AMC-/BMO-
Angaben mit Quellen einfügen. Die Studie nutzt AMC-Berichte. Unvollständige
Kurse, fehlende Suchwerte oder zu kleine Stichproben können eine vollständige
Auswertung verhindern; die Oberfläche meldet die Ursache. Neue Ergebnisse sind
keine Reproduktion der alten Stichprobe und müssen fachlich geprüft werden.

## Aufbau

- `Interface/`: Oberfläche, lokaler Server, Auftragssteuerung und Anleitung.
- `analyse.py`, `statistik.py`, `grafiken.py`: geprüfte Kernanalyse der Seminararbeit.
- `Programm/`: wiederverwendete Aufbereitung, Datenerhebung und Statistik der
  gesicherten Vollversion; für neue Datenbestände benötigt.
- `Daten/Arbeitsbestaende/`: neue Rohdaten mit Abrufparametern und Prüfsummen.
- `Ergebnisse/Analysen/`: separate Ergebnisläufe der neuen Datenbestände.
- `Daten/Modelle/FinBERT/`: festgelegtes lokales Modell.

Nach dem Herunterladen `INSTALLIEREN.bat` mit Python 3.12 (64 Bit) ausführen. FinBERT anschließend in der Oberfläche einrichten.

Quellen: [Alpha Vantage](https://www.alphavantage.co/documentation/),
[Google Trends über SerpAPI](https://serpapi.com/google-trends-api).
