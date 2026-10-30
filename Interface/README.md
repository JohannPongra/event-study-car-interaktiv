# Interface – Analyse, Datenabruf und Grafiken

**`STARTEN.bat` oder im Projektordner `START_INTERFACE.bat` öffnen.** Ein bloßer
Doppelklick auf `index.html` zeigt die Galerie; Berechnung und Datenabruf benötigen
den lokalen Analyseserver. „Interface beenden“ schließt ihn wieder.

## Bedienung

- **Analyse starten:** die vorhandenen 170 Berichte neu auswerten und mit zwölf
  Referenztabellen vergleichen. Die Grafiken werden danach aktualisiert.
- **Neuen Datenbestand sammeln:** Unternehmen, Berichtszeitraum und API-Schlüssel
  eingeben. Das angezeigte Anfragelimit gilt pro Start. Nach einem Abbruch den
  Bestand wählen und „Abruf fortsetzen“ anklicken; gespeicherte Antworten werden
  wiederverwendet. Für einen frischen Abruf einen neuen Bestand starten.
- **Daten prüfen:** aufbereiten und fehlende Veröffentlichungszeiten anzeigen.
  Belegte Zeiten können über die CSV-Eingabe ergänzt werden.
- **FinBERT einrichten:** einmalige Installation der Python-Pakete über das
  Internet; die festgelegten Modellgewichte werden heruntergeladen, per Prüfsumme geprüft und anschließend mit einer Vorhersage getestet.
- **Diesen Bestand analysieren:** Daten aufbereiten, TONE berechnen, CAR und
  Einflussgrößen bilden, Regressionen schätzen und Grafiken erzeugen.
- **Berechneter Ergebnisstand:** zwischen Ausgangsdaten und neuen Läufen wechseln.

## Datenquellen

[Alpha Vantage](https://www.alphavantage.co/documentation/) liefert mit `EARNINGS`
Gewinnberichte, mit `TIME_SERIES_DAILY_ADJUSTED` Kurse und Volumen und mit
`EARNINGS_CALL_TRANSCRIPT` die Transkripte. Adjustierte Tageskurse benötigen einen
passenden Premiumtarif. [SerpAPI](https://serpapi.com/google-trends-api) liefert
Google-Trends-Zeitreihen (`TIMESERIES`). Beide Dienste benötigen eigene Schlüssel.
Abrufe verbrauchen das jeweilige Kontingent; Schlüssel werden nicht gespeichert.

SEARCH nutzt neun vollständige Wochen aus demselben Export. Unvollständige
aktuelle Wochen werden ausgelassen. Unbekannte Veröffentlichungszeiten werden
nicht geraten. Für die AMC-Studie können fehlende Angaben zu Ausschlüssen führen.

## Wie die Grafiken entstehen

Die Kurse werden in einfache Tagesrenditen umgerechnet. Das Marktmodell wird
über `[-250,−30]` geschätzt; `CAR = AR_0 + AR_1`. Darauf folgen Regressionen mit
Unternehmens-, Jahres- und Quartalseffekten sowie nach Ereignistag geclusterte
Standardfehler. Matplotlib erzeugt die Diagramme als PNG und PDF. Die Kennzahlen
und Regressionen werden bei jedem Analysestart erneut berechnet.

Die Ansicht **In der Arbeit** enthält dagegen die 25 unverändert aus
`W-Seminar-Johann-PongratzNeu.docx` übernommenen Bilder. `erstellen.py` liest diese
Bilder und ihre Beschriftungen aus; `AKTUALISIEREN.bat` übernimmt spätere Änderungen
am Word-Arbeitsstand. Die Word-Datei selbst wird nicht verändert. Sie ist nicht im Repository enthalten; bei Bedarf den Pfad an `AKTUALISIEREN.bat` übergeben.

`server.py` nimmt lokale Aufträge entgegen; `auftrag.py` führt sie getrennt aus.
Neue Daten und Ergebnisse liegen ausschließlich in dieser Kopie. Ein neuer
Datenbestand kann andere Fallzahlen und Ergebnisse als die Seminararbeit haben.
