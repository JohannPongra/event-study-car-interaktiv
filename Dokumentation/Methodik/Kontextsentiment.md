> Diese Anleitung dokumentiert das optionale Kontextverfahren. Im Reproduktionspaket ist das festgelegte FinBERT-TONE-Modell enthalten; zusätzliche finbert-lc-Gewichte sind darin nicht enthalten. Die Standardreproduktion verwendet die Satzmethode.

# Kontextbasierte Sentimentanalyse nach Atsiwo (2024)

## Festlegung und Datenstand

Gewünschte Grundlage ist Abraham Atsiwo, *Financial Sentiment Analysis: Leveraging Actual and Synthetic Data for Supervised Fine-tuning*, arXiv:2412.09859v1. Die veröffentlichten Gewichte werden für den Vergleich mit der bestehenden Satzanalyse verwendet.

Die 170 korrigierten Transkripte aus `EXPORT_LAPTOP_20261015` sind bereits im aktiven Datenbestand eingebunden. Die gezielte menschliche Nachprüfung betrifft 57 Hörstellen und ist keine vollständige Hörkontrolle aller Calls. Jeder vollständige Call steht als eine Textzeile ohne erfundene Sprecherzuordnung bereit. Die Satztrennung liefert 80.262 Sätze; für den bisherigen FinBERT-Tokenizer beträgt das Maximum 440 Tokens. Alle Sätze und Kontextabschnitte wurden zusätzlich mit dem eigenen Tokenizer von finbert-lc geprüft; keine Eingabe überschreitet 512 Tokens einschließlich Spezialtokens.

## Was aus dem Artikel übernommen wird

Der Artikel erweitert die Trainingsdaten um längere zusammengesetzte sowie synthetisch erzeugte Finanztexte. Ein domänenspezifisches Next-Sentence-Prediction-Modell (NSP) prüft Satzfolgen; der Sentimentklassifikator heißt finbert-lc. Das ist ein eigenes trainiertes Modell und kein bloßer Parameterwechsel im vorhandenen FinBERT. Für die Anwendung stehen veröffentlichte Modellgewichte bereit. Ein erneutes Training ist daher für einen ersten Anwendungstest nicht erforderlich. [Artikel, Abschnitte 3 und 4](https://arxiv.org/html/2412.09859v1).

Die folgende Übertragung auf Earnings Calls, die Aufteilung vollständiger Calls und die Aggregation auf Call-Ebene sind **eigene Projektfestlegungen**. Der Artikel ist keine fertige Anleitung für diese Event Study.

## Modelle und geprüfte Versionen

| Aufgabe | Modell | feste Revision |
|---|---|---|
| Bisherige Satzanalyse | `yiyanghkust/finbert-tone` | `4921590d3c0c3832c0efea24c8381ce0bda7844b` |
| Sentiment nach dem Artikel | `ab30atsiwo/finbert-gpt-50agree` | `cddcf0cbc757e26443712bcacd92edbf3e00ef7a` |
| Optionale NSP-Kontextbildung | `ab30atsiwo/nsp-finetuned-bloombery` | `4b1e0d9d5492130101e11fc2d40b644da7067343` |

Die öffentlichen Modellmetadaten und Konfigurationen wurden am 16.10.2026 abgerufen. Beide zusätzlichen Modelle sind BERT-Klassifikatoren mit maximal 512 Positionen. Die Sentimentklassen sind beim neuen Modell **0 negativ, 1 neutral, 2 positiv** und unterscheiden sich von der bisherigen Klassenreihenfolge. Wahrscheinlichkeiten müssen über die Modellkonfiguration zugeordnet werden. [Sentimentmodell](https://huggingface.co/ab30atsiwo/finbert-gpt-50agree), [festgelegte Konfiguration](https://huggingface.co/ab30atsiwo/finbert-gpt-50agree/blob/cddcf0cbc757e26443712bcacd92edbf3e00ef7a/config.json).

## Konkrete Umsetzung für diese Studie

1. **Satzbasierte Vergleichsbasis fertigstellen.** Dieselben 170 Exporttexte werden mit dem bisherigen FinBERT bewertet. Alte Call-Tonwerte werden nicht übernommen. Bereits geprüfte Vorhersagen exakt identischer Satztexte derselben Modellrevision dürfen als Cache wiederverwendet werden; ihre Herkunft wird gespeichert.
2. **finbert-lc auf einzelnen Sätzen anwenden.** Das liefert die Kontrolle für einen Modellwechsel, ohne zugleich das Kontextfenster zu verändern.
3. **Zusammenhängende Abschnitte bilden.** Innerhalb jedes Calls werden unmittelbar aufeinanderfolgende vollständige Sätze bis zur maximalen Tokenzahl zusammengeführt. Eingabe einschließlich Spezialtokens höchstens 512 Tokens, keine stillen Kürzungen, keine Überlappungen und keine Vermischung verschiedener Calls. Jeder Satz muss genau einmal vorkommen. Fehlende Sprechergrenzen werden als Einschränkung dokumentiert. Synthetische Texte und nach Sentiment sortierte Satzgruppen gehören nicht in die zu messenden Originalcalls.
4. **Optional NSP zur Grenzwahl einsetzen.** Als Übertragung des Gedankens auf die Anwendung lässt sich jeweils prüfen, ob der nächste Satz zum bisherigen Abschnitt passt. Bei einer Fortsetzungswahrscheinlichkeit über 0,5 und eingehaltenen Tokenlimits wird angefügt, sonst beginnt ein neuer Abschnitt. Die Paar-Eingabe des NSP-Modells und die Eingabe des Sentimentmodells werden jeweils mit ihrem eigenen Tokenizer geprüft. Auch abgelehnte Kandidaten bleiben im Call erhalten. Vor diesem Schritt muss die unten beschriebene Klassenzuordnung geklärt werden.
5. **Abschnitte mit finbert-lc bewerten.** Für jeden Abschnitt werden Text, Satzbereich, Tokenzahl, Klasse und alle drei Wahrscheinlichkeiten gespeichert. Das Modell bewertet den ganzen Abschnitt, nicht jeden darin enthaltenen Satz separat.
6. **Call-Werte und Regressionen vergleichen.** Alle Verfahren verwenden dieselbe Ereignisstichprobe, dieselben Kontrollgrößen, Zeitfenster, festen Effekte und Standardfehler. Es wird jeweils nur die Sentimentvariable ersetzt.

Diese drei Hauptvarianten sind erforderlich, um die Ergebnisse einzuordnen:

| Variante | Modell | Einheit |
|---|---|---|
| A: bisheriger Ansatz | bisheriges FinBERT | einzelner Satz |
| B: Kontrolle des Modellwechsels | finbert-lc | einzelner Satz |
| C: Kontextansatz | finbert-lc | zusammenhängender Mehrsatzabschnitt |

Der Vergleich B gegen C untersucht den Einfluss der längeren Eingabe innerhalb desselben Modells. A gegen C verändert zusätzlich Modell und Trainingsdaten. Ein Ergebnisunterschied ist dann kein isolierter Nachweis eines Kontexteffekts.

Die Grenze von 512 Tokens ist die technische Eingabegrenze des Modells und keine empirisch nachgewiesene optimale Kontextlänge für Earnings Calls. Die hier festgelegte Abschnittsregel wird vor Sichtung der Vergleichsergebnisse angewandt. Kürzere Fenster oder andere Grenzen wären getrennte, vorab zu definierende Varianten; sie dürfen nicht nach dem günstigsten Regressions-p-Wert ausgewählt werden. Ohne verlässliche Sprechersegmentierung können Abschnitte mehrere Redebeiträge enthalten.

## Aggregation und Dateien

Für Call i wird als primäre Erweiterung der bisherigen harten Klassifikation verwendet:

`TONE_CONTEXT_i = Summe_b[n_b × z_b] / Summe_b[n_b]`

`n_b` ist die Satzanzahl eines Abschnitts; `z_b` ist +1 bei positiv, −1 bei negativ und 0 bei neutral. Kurze Restabschnitte erhalten dadurch weniger Gewicht. Der Wertebereich bleibt −1 bis +1. Diese Gewichtung ist eine Projektfestlegung, keine aus dem Artikel übernommene Formel. Das Blocklabel wird rechnerisch allen enthaltenen Sätzen zugewiesen; die Interpretation unterscheidet sich daher vom ursprünglichen Satzmaß.

Zusätzlich kann ein Wahrscheinlichkeitsscore aus `p_positive − p_negative` berechnet werden. Für einen fairen Vergleich muss dann derselbe Wahrscheinlichkeitsscore auch in der Satzvariante verwendet werden.

Der eigene Analyseschritt erzeugt `lc_saetze.csv`, `kontext_abschnitte.csv`, `lc_abschnitte.csv`, `tone_lc_sentence.csv` und `tone_lc_context.csv`. Sein Manifest hält Modellrevisionen, Klassenbelegung, Tokengrenzen, Satz- und Blockregel, Textprüfsummen und Gewichtung fest. Die vollständigen Event-Study-Läufe speichern zusätzlich ihre Paketversionen und den verwendeten Programmstand. Das bisherige `tone.csv` wird nicht still überschrieben. Bei einer späteren NSP-Variante müssten auch die Grenzentscheidungen separat gespeichert werden.

Für die noch ausstehende inhaltliche Validierung werden 200 nach Unternehmen und Jahren verteilte Textstellen zur manuellen Bewertung bereitgestellt, möglichst durch zwei Personen ohne Kenntnis der Kursreaktion oder der Modellvorhersage. Die vorliegenden Regressionsvergleiche sind bis dahin explorativ. Wenn die Aufbereitung anhand menschlicher Bewertungen verändert wird, müssen Entwicklungs- und Prüfbestand nach Calls getrennt werden; Accuracy, Macro-F1 und Konfusionsmatrix werden anschließend nur auf dem zurückgehaltenen Prüfbestand berichtet. Regressions-p-Werte dienen nicht zur Wahl der Textaufbereitung oder des Modells.

## Offene technische Frage im veröffentlichten NSP

Es gibt einen überprüfbaren Widerspruch zwischen der veröffentlichten NSP-Konfiguration und dem Forschungscode:

- Die [Konfiguration der festen NSP-Revision](https://huggingface.co/ab30atsiwo/nsp-finetuned-bloombery/blob/4b1e0d9d5492130101e11fc2d40b644da7067343/config.json) nennt `0 = isNext`, `1 = notNext`.
- Der [Code zur Erzeugung längerer Texte](https://github.com/abraham-atsiwo/filbert-lc/blob/da722d943136f42651ed751ea51baf84c49d9de0/pipeline/generate_long_sentence.py) verwendet dagegen die Wahrscheinlichkeit an Position 1 als Fortsetzungswert. Die [Erzeugung der Trainingslabels](https://github.com/abraham-atsiwo/filbert-lc/blob/da722d943136f42651ed751ea51baf84c49d9de0/pipeline/load_nsp_data.py) weist tatsächlichen Fortsetzungen ebenfalls Label 1 zu.

Daraus lässt sich allein noch nicht sicher ableiten, ob die veröffentlichte Konfiguration oder die Beispielimplementierung zum veröffentlichten Gewichtsstand passt. Vor einer automatischen NSP-Segmentierung ist die Belegung an einem unabhängig gelabelten Satzpaar-Testbestand zu prüfen. Bis dahin darf keine NSP-Variante als verifiziert dargestellt werden. Die Anwendung des Sentimentklassifikators finbert-lc auf natürliche fortlaufende Abschnitte kann unabhängig davon vorbereitet werden.

## Umsetzungsstand

Transkriptimport, Textintegrität und Erhalt der Finanzdaten sind geprüft. Die festgelegten finbert-lc-Gewichte wurden heruntergeladen und gegen die veröffentlichte SHA256 geprüft. Die Satz- und Kontextbewertung sind für alle 170 Calls abgeschlossen. Die Abschnittsbildung ergibt 3.694 Abschnitte aus 80.262 Sätzen; ein Abschnitt enthält im Median 21 Sätze. Acht gezielte Tests der Abschnittsbildung, Aggregation und Herkunftsprüfung sowie die 17 HTTP-Tests der erweiterten Oberfläche sind bestanden. Es werden die veröffentlichten Sentimentgewichte angewandt; eine vollständige Reproduktion des Modelltrainings wird damit nicht behauptet. Die menschliche inhaltliche Validierung steht noch aus.
## Bedienung und Ergebnisdateien

In der Oberfläche steht unter **Tonalitätsverfahren** die Auswahl zwischen dem bisherigen FinBERT pro Satz, finbert-lc pro Satz und finbert-lc mit Kontext zur Verfügung. **Drei Verfahren vergleichen** erzeugt die drei vollständigen Event-Study-Auswertungen und einen gemeinsamen Vergleichsbericht. Die Ereignisstichproben werden vor den Regressionsläufen auf Gleichheit geprüft. Die aktuell ausgewählte Hauptvariante wird durch den Vergleich nicht in den Einstellungen überschrieben.

Für die getrennte Ausführung stehen `Kontextanalyse.py` und `Kontextvergleich.py` bereit. Beide verwenden den aktiven Datenbestand und die festgelegten lokalen Modellgewichte. Bereits bewertete identische Texte derselben Modellrevision werden aus einem eigenen finbert-lc-Cache gelesen; ein unterbrochener Lauf kann fortgesetzt werden.

Die Bewertungen und ihr Manifest stehen unter `Sentiment/Kontext/`. Der Vergleich erzeugt `Ergebnisse/Kontextvergleiche/vergleich_…/bericht.html`, `Call_Tonwerte.csv`, `Korrelationen.csv`, `TONE_Koeffizienten.csv`, `Klassenverteilung.csv`, die Grafiken als PNG/PDF und eine blinde menschliche Prüfstichprobe mit 200 Abschnitten aus allen fünf Unternehmen und verschiedenen Jahren. Die vollständigen Einzelberichte behalten ihre eigenen Einstellungen, Daten und Prüfsummen.

## Abgeschlossener Vergleich am 16.10.2026

Der historische Vergleichslauf `vergleich_20261016_125758_69b99d` gehört nicht zum eingefrorenen Referenzlauf dieses Reproduktionspakets. Die folgenden Angaben dokumentieren den damaligen Ausgangsstand; sie sind kein neuer Prüfbericht der Umstrukturierung. Alle drei Varianten verwenden 170 Ereignisse ohne Ausschlüsse. 20 Abschlussprüfungen bestätigen unter anderem die vollständige Satzabdeckung, die Call-Aggregation, gleiche Stichproben und Kontrollgrößen, unabhängige OLS- und Cluster-Nachrechnungen sowie die Exporte. Alle 13 lokalen Verweise im Vergleichsbericht sind über die Oberfläche erreichbar; beide Vergleichsgrafiken wurden visuell geprüft.

Der Kontext-TONE korreliert mit finbert-lc pro Satz mit r = 0,723. Im Vollmodell beträgt sein Zusammenhang mit CAR je einer Standardabweichung 1,84 Prozentpunkte (95%-Intervall 0,37 bis 3,30; p = 0,0144). Für ABS_CAR ist der Zusammenhang statistisch nicht klar (p = 0,4662). Das sind Ergebnisse der gemeinsamen explorativen Regressionsspezifikation, kein Nachweis einer besseren Klassifikationsqualität und keine kausalen Effekte. Die menschliche Prüfung der bereitgestellten 200 Abschnitte steht weiterhin aus.
