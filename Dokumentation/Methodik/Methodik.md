# Methodik der Event Study mit einfachen Renditen

Seit 28.10.2026 verwendet die Standardanalyse einfache Tagesrenditen. Maßgeblich sind `Technik/Konfiguration/einstellungen.json` und die Vergleichswerte unter `Pruefungen/Testdaten/CAR_einfache_Renditen/`. Die historischen logarithmischen Ergebnisse bleiben unter `Archiv/Referenzlauf/` erhalten. Die Zuordnung zur bisherigen Seminararbeit steht in `Dokumentation/Datenherkunft/Abgleich_Seminararbeit.md`.

## Daten und Ereigniszeit

170 Quartalsberichte von AAPL, AMZN, GOOGL, META und MSFT; 34 je Unternehmen, veröffentlicht zwischen 31.01.2018 und 30.04.2026. Jedes Ereignis besitzt eine eindeutige `event_id`. Das Veröffentlichungsquartal der Kontrollvariablen ist vom Geschäftsquartal des Transkripts zu unterscheiden.

Für die im Bestand als nachbörslich eingestuften Berichte gilt der nächste im SPY-Datensatz vorhandene Handelstag als Tag 0. Tag +1 ist der nächste Handelstag danach. Die Veröffentlichungstage werden zur Reproduktion unverändert übernommen. Das historische Manifest bezeichnet 166 von 170 Zeitzuordnungen als nicht unabhängig belegt; es wird keine zusätzliche Prüfung behauptet.

## Rendite und CAR

- `r_i,t = P_i,t / P_i,t−1 − 1` mit split- und dividendenbereinigten Schlusskursen.
- Im Schätzfenster Tag −250 bis −30 werden 221 Renditepaare der Aktie und von SPY verwendet. OLS schätzt `r_i,t = alpha + beta · r_SPY,t + Fehler`.
- Im Ereignisfenster 0 bis +1: `AR = tatsächliche Rendite − (alpha + beta · Marktrendite)`.
- `CAR = AR_0 + AR_1`; `abs_car = |CAR|`.

Aktien- und Marktrenditen werden beide als einfache Tagesrenditen berechnet. Renditen stehen in den CSV-Dateien als Dezimalzahlen: CAR = 0,01 entspricht einer kumulierten abnormalen Rendite von 1 Prozentpunkt. CAR addiert die täglichen AR; es erfolgt keine Aufzinsung. CAR misst die Abweichung von der erwarteten Rendite und ist kein tatsächlicher Anlagegewinn. Die logarithmische Alternative ist mit `--renditen log` weiterhin reproduzierbar. VOL, PREVOL und SEARCH behalten ihre bisherigen Definitionen einschließlich ihrer Logarithmen.

## Einflussgrößen

| Größe | Festlegung |
|---|---|
| UE | Tatsächlicher minus erwarteter EPS. |
| SUE | Aktuelle UE geteilt durch die korrigierte Stichprobenstandardabweichung der UE der genau acht vorherigen Quartalsberichte; ddof=1, keine zukünftigen Werte. |
| SAV | Logarithmiertes Volumen minus dessen Mittelwert an Tagen −60 bis −10, geteilt durch die korrigierte Standardabweichung desselben 51-tägigen Fensters. |
| VOL | Mittelwert von SAV an Tagen 0 und +1. |
| PREVOL | Mittelwert von SAV an Tagen −3, −2 und −1. |
| SEARCH | Logarithmus aus Suchinteresse der Woche von Tag 0 geteilt durch den Median der acht Vorwochen. Alle neun Wochen müssen aus demselben US-Export mit demselben Suchbegriff stammen. |
| TONE | `(Anzahl positiver Sätze − Anzahl negativer Sätze) / Anzahl aller Sätze`; neutrale Sätze gehören zum Nenner. |

TONE verwendet den vollständigen verfügbaren Earnings Call mit allen Sprecherbeiträgen. Es wird keine Sprecherzuordnung erfunden. FinBERT-Modell: `yiyanghkust/finbert-tone`, feste Revision `4921590d3c0c3832c0efea24c8381ce0bda7844b`. Deterministische Satztrennung `english_rules_v1`; 80.262 gespeicherte Satzvorhersagen. Überlange Modellsätze werden nicht still abgeschnitten. Bei gleichen Klassenwahrscheinlichkeiten gilt die Reihenfolge neutral, positiv, negativ.

Die Standardreproduktion liest die gespeicherten Vorhersagen nach identischen Satzkennungen; diese binden Modell, Revision, Ereignis, Beitrag, Satzposition und Text. Sie berechnet die Klassenzahlen und TONE erneut. Eine vollständige neue Modellinferenz ist ein eigener optionaler Lauf.

## Regression und Prüfung

Das Hauptmodell erklärt CAR gemeinsam durch SUE, VOL, PREVOL, SEARCH und TONE. Kontrolliert werden Unternehmen, Veröffentlichungsjahr und Kalenderquartal. Das ergänzende Betragsmodell erklärt |CAR| und verwendet |SUE| anstelle von SUE. Im Ausgangsmodell wird nicht winsoriert.

Die Standardfehler werden mit CR1 nach Ereignishandelstag geclustert. Koeffiziententests verwenden die t-Verteilung mit G−1 Freiheitsgraden; hier G=113. Die Tests sind zweiseitig. Heteroskedastizität wird dadurch für die Inferenz berücksichtigt, nicht aus den Daten entfernt. Zeitliche Abhängigkeiten zwischen verschiedenen Ereignistagen werden so nicht gezielt erfasst.

Diagnostik: Residuen, Cook-Distanzen, VIF, Jarque-Bera und Koenker-Breusch-Pagan. Sensitivitätsprüfungen: gemeinsame Winsorierung von SUE, VOL und PREVOL am 1./99. Perzentil, Weglassen der Kontrollen, Ausschluss je eines Unternehmens und alternative CAR-Fenster [−1,+1] bzw. [0,+2]. Beim Fensterwechsel bleiben die Erklärungsgrößen unverändert. Die zusätzliche Einzelereignis-/Wild-Bootstrap-Analyse ist in diesem Referenzlauf ausgeschaltet.

Fehlende oder nicht definierte Kennzahlen werden nicht durch Nullwerte ersetzt. Im Referenzlauf sind alle 170 Ereignisse vollständig; es gibt keine Ausschlüsse. Die Zusammenhänge sind keine Kausalitätsnachweise. Ein bestandener Reproduktionsvergleich prüft dieselbe Rechnung mit denselben Eingaben, nicht die Fehlerfreiheit aller Quellen oder Modellannahmen.
