# Event Study mit interaktiver Analyse und Datenabruf

Lokale Oberfläche zur W-Seminararbeit von Johann Pongratz. Sie kann die vorhandene
CAR-Analyse erneut ausführen, **neue Daten sammeln**, separate Datenbestände
analysieren und die Ergebnisse als Tabellen und Grafiken anzeigen.

Die [schlanke Reproduktionsfassung](https://github.com/JohannPongra/event-study-car-reproduzierbar)
enthält nur die Kernanalyse und eine statische Galerie.

## Start unter Windows

1. Repository herunterladen oder klonen; Python **3.12, 64 Bit** installieren.
2. `INSTALLIEREN.bat` ausführen.
3. `START_INTERFACE.bat` öffnen. Die Oberfläche startet im Browser auf diesem Computer.

Das Analyseprogramm läuft auf `127.0.0.1`; es wird kein öffentlicher Webserver
bereitgestellt. Unten in der Oberfläche lässt es sich mit „Interface beenden“ schließen.

## Funktionen

- **Analyse starten:** 170 vorhandene Berichte neu auswerten und zwölf Referenztabellen prüfen; nach Installation offline nutzbar.
- **Neue Daten sammeln:** Unternehmen und Berichtszeitraum auswählen; Anfragelimit und Pause einstellen.
- **Abruf fortsetzen:** bereits gespeicherte Anbieterantworten wiederverwenden.
- **Daten prüfen:** Eingaben aufbereiten und fehlende Veröffentlichungszeiten anzeigen.
- **Neue Daten analysieren:** FinBERT, CAR, Einflussgrößen, Regressionen und Grafiken ausführen.
- **Ergebnisse vergleichen:** zwischen getrennten Ergebnisläufen wechseln; PDFs und Tabellen öffnen.

## Datenquellen und Voraussetzungen

[Alpha Vantage](https://www.alphavantage.co/documentation/) liefert Kurse, Volumen,
Gewinnberichte und Transkripte. [SerpAPI](https://serpapi.com/google-trends-api)
liefert die Google-Trends-Zeitreihen. Neue Abrufe benötigen eigene API-Schlüssel,
entsprechende Kontingente und gegebenenfalls einen passenden Tarif. Die Schlüssel
werden nur für den laufenden Auftrag verwendet und nicht gespeichert.

Für neue Transkripte einmal **„FinBERT einrichten“** wählen. Dabei werden die
Python-Abhängigkeiten und das ca. 439 MB große Modell
[`yiyanghkust/finbert-tone`](https://huggingface.co/yiyanghkust/finbert-tone)
heruntergeladen. Die Revision `4921590d3c0c3832c0efea24c8381ce0bda7844b` und
SHA-256-Prüfsummen sind festgelegt. Anschließend wird eine Vorhersage getestet.

## Methodik und Reproduzierbarkeit

Einfache Tagesrenditen; Marktmodell `[-250,−30]`; `CAR = AR_0 + AR_1`.
Die Modelle enthalten SUE bzw. |SUE|, VOL, PREVOL, SEARCH und TONE, feste Effekte
sowie nach Ereignishandelstag geclusterte Standardfehler. Die Untersuchung nutzt
nachbörsliche Berichte. Fehlende Veröffentlichungszeiten werden nicht geraten;
belegte Angaben können ergänzt werden.

Die Ausgangsdaten reproduzieren **170 Ereignisse und 113 Datumscluster**.
Neue Datenbestände können andere Fallzahlen und Ergebnisse liefern.
**170 vollständige Transkripte und 80.262 bewertete Sätze mit ihren Texten**
sind enthalten: [Transkripte einzeln lesen](Daten/Transkripte/README.md).
Modellgewichte, persönliche Downloads, API-Schlüssel und Laufzeitdateien
werden nicht mit Git versioniert.

[Bedienungsanleitung](Interface/README.md) · [Weitere Details](ANLEITUNG.md) ·
[Datenherkunft](Daten/README.md)

Die Reproduktion wurde geprüft; der Abruf mit simulierten Anbieterantworten
einschließlich Fortsetzung getestet. Ein erfolgreicher Live-Abruf hängt von
Schlüsseln, Tarif und der Verfügbarkeit der Anbieter ab.
