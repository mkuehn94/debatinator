# Protokoll: Gespräch red.fuchs & Pink Panther (Discord, 2026-11-04)

## Übersicht
Gespräch zwischen red.fuchs und Pink Panther (ca. 51 Min.) über ein Assistenz-Tool für Live-Debatten, das Argumente und Kniffe erkennt und kurze Hinweise gibt. Beschlossen wurden ein Terminal-(CLI-)Prototyp zuerst, Bottom-up-Vorgehen, ein schnelles Decision-/Classifier-Modell zur Einordnung und Kanban als Methode; das Thema Pinote (Sprecher-Trennung) wird geparkt. Offen bleiben Ausgabeform (Overlay vs. Browser), Sprache, Datensatz, API-Protokoll und Hosting des Boards. red.fuchs kommt nach eigener Aussage ca. ab nächstem Dienstag wieder voran. Quelle ist ein Maschinen-Live-Transkript; Schreibweisen sind verfälscht (z. B. „Pinote“ vermutlich pyannote, „Canban“ = Kanban).

## Beschlüsse
1. **Pinote parken** (Sprecher-Trennung, vermutlich pyannote) — [09:34] „dann würde ich tatsächlich Pinote erst mal parken“; PP [09:52] „Genau.“
2. **Schnelligkeit ist oberste Priorität** für die Einordnung — [12:25] PP: „weil es muss ja schnell sein“
3. **Schnelles Classifier-/Decision-Modell für die Einordnung** der Argumente statt großem LLM — [15:06] red.fuchs: „Classifier oder Decision Modell für schnelles Einordnen“; PP [15:07] „Ja.“
4. **Bottom-up:** erst Grundlogik mit Prototypen und Mockups — [24:31] red.fuchs: „erst mal die Grundlogik aufbauen sollen mit Prototypen und Mockups“; PP [24:48] „Das ja bottom up ist immer nein gute Idee.“
5. **Terminal/CLI zuerst**, TUI und Web-UI hinten angestellt — [32:12] red.fuchs: „Ich werde es CL, also Terminal ready erst mal machen.“; PP [32:28] „Ja, hab ich kein Problem mit.“
6. **Flexible Agilmethoden statt traditioneller Methoden** (Wasserfall/Gantt) — [45:58] red.fuchs: „Ich glaube, die traditionellen sind zu starr“; PP [46:06] „Ja.“
7. **Kanban als Methode** — [49:13] red.fuchs: „ich würde trotzdem sagen Canban ist eine gute Sache für uns“; PP [49:22] „Das klingt doch gut“

## Vorschläge (offen)
1. **Ausbaustufe 1: Text-Analyse-Tool** für Chats (Discord/X), analysiert Text von beiden Seiten — Vorschlag red.fuchs [06:50] „das auf Text läuft und den Text analysiert“; PP [07:03] „Ja.“ (nur Zustimmung zu Stufe 1)
2. **Ausbaustufe 2: Live-Audio** mit Transkription der eigenen und der Gegenstimme, schnelle Einordnung — red.fuchs [07:21] „und das versucht so schnell wie möglich einzuordnen“
3. **Ausbaustufe 3: mehrere Gesprächspartner** einordnen (evtl. zusammen mit Stufe 2) — red.fuchs [07:36] „mehrere Gesprächspartner auseinander zu Frieel“; PP [07:51] „Nur zwei sind“ (Einschränkung auf zwei)
4. **Audioquelle: Ausgabe-Audio abgreifen** statt Mikrofon, dann nur das Gegenüber hörbar — PP [07:55] „du hast eine Audioquelle quasi Output.“
5. **Denkschulen-Test:** eine Denkschule gegen mehrere andere — red.fuchs [09:06] „Das könnten wir aber auch testen, ja.“
6. **Fokus auf schnelle Transkription** statt Sprecher-Diarisierung für den Live-Modus — red.fuchs [09:47] „sondern Fokus auf schnelle Transkriptierung“
7. **Lokaler Modell-Server** mit Standard-API (OpenAI- oder Llama-Protokoll), fest verdrahtet nicht gewollt; externe Modelle optional — red.fuchs [10:11] „Das ist am besten natürlich die verhalten sich wie ein lokaler Server, den man ansprechen kann.“; PP [10:24] „nicht verstanden.“
8. **LFM3-Decision-Modelle** (Liquid AI, zwei Modelle in der Familie) als konkrete Wahl für die Einordnung — red.fuchs [12:02] „und ich hab jetzt auch hier von Liquid AI die neue Familie.“
9. **Kleines LLM schreibt Inspirationen** (Denkanstöße für den Debattierenden) — red.fuchs [15:13] „dass ein kleines Larial Langage Model Inspirationen schreibt“; PP [16:36] „Ja genau aber das ist doch was wir bauen wollen oder nicht“
10. **Ausgabeformat:** Visualisierung der Argumente mit Wahrscheinlichkeit, darunter 1–2 Sätze Zusammenfassung, darunter Inspiration — red.fuchs [15:57] „so vielleicht ein, zwei, wo das Ganze in Kontext zusammengefasst wird“
11. **Nur bei Schwellenwert anzeigen** (Fallacy-Hinweis nur ab hoher Wahrscheinlichkeit, sonst drei Antworten) — PP [19:25] „dann würde das angezeigt“; red.fuchs [19:40] bestätigt die Grundidee (Hörhilfe-Vergleich)
12. **Ausgabefenster:** PP schlägt Webserver im Browser vor; red.fuchs schlägt kleines frei bewegliches Bild-in-Bild-Fenster vor — PP [21:26] „er macht halt einfach einen Webserver auf auf einen gewissen Porten“; red.fuchs [21:12] „Das müsste sowas wie ein kleines Hopp-up Fenster sein“
13. **Tauri als Shell** mit lokalem Webserver darin (PP); red.fuchs skeptisch wegen Electron — PP [24:18] „Also Tauri da drin, dann lokaler Webs Server mit“; red.fuchs [23:39] „aber Elektron habe ich immer in der Vergangenheit gemerkt ist eine ziemlich zig Angelegenheit“
14. **Datensatz:** kuratierte englische Trainingssätze nutzen; YouTube-Transkripte gezielt von Debatten mit genau zwei Sprechern ohne Moderator — red.fuchs [26:21] „gibt es einige der Trainingssätze, die schon gut kuratiert sind.“; [26:50] „Ansonsten, was ich mir auch vorstellen könnten, wären die Transkripte von YouTube.“; PP [26:44] „Das wäre dann schon mal sehr gut zum zum Pre Training“
15. **Trainingsdaten synthetisieren** mit dem lokalen Modell Heretic E4B aus analysierten Transkripten — red.fuchs [27:19] „und Trainingsdaten daraus synthetisieren“
16. **Anime-VTuber-Debattenfigur** (TTS plus LLM) als Gag-/Ausgabe-Idee — red.fuchs [36:19] „dann hat man plötzlich eine Debatten Anime Girl oder sowas.“; PP [36:25] „Das wäre interessant.“
17. **Chatbot mit libertärer Literatur** (über 500 Bücher) als frei nutzbarer Lern-Bot — red.fuchs [36:46] „dass wir sowas wie eine Art Learn oder kleiner Chatbot bauen“; PP fragt nach Ausrichtung [37:03]; red.fuchs verneint Ideologie-Fokus [37:15] „Nein nein nein, das ist nicht die Idee“
18. **Projektplan als Gantt und Netzplan** (von KI erstellt, PDF geteilt) — red.fuchs [42:05] „Projektmanagermäßig einen Gant und einen Netzplan zu bauen“; von red.fuchs selbst relativiert [43:39] „aber Gantdiagramme sind da wenig“
19. **Board-Hosting:** statische GitHub-Seite (red.fuchs) vs. eigene Website von PP mit Login — red.fuchs [50:01] „Da könnten wir das Canan über eine statische Github Seite abbilden.“; PP [50:10] „Ich kann dir einfach auf meiner Website hosten sonst oder?“

## Aufgaben
| Aufgabe | Owner | Frist | TS |
|---|---|---|---|
| Terminal-(CLI-)Prototyp bauen: „Ich werde es CL, also Terminal ready erst mal machen.“ | red.fuchs | – | [32:12] |
| Decision-Modell auf typische Kniffe testen: „das erste was ich machen werde, ist überhaupt zu schauen, wie gut er ist“ | red.fuchs | – | [33:01] |
| Classifier-Testläufe auf dem Mac: „Das könnte ich schon machen.“ | red.fuchs | – | [25:53] |
| Projektdaten in die KI geben, Prompt anpassen (Meilensteine und Gold definieren): „Dann werde ich das Ganze in die ki stecken“ | red.fuchs | – | [41:53] |
| Hosting-Lösung für das Board erkunden: „aber ich kann mich ein bisschen erkundigen“ | red.fuchs | – | [50:35] |
| Wieder in die Arbeit einsteigen: „rechne erst circa am nächsten Dienstag, dass ich in die Pötte komme“ | red.fuchs | ca. nächster Dienstag | [50:35] |
| Tauri-Variante auf Windows ausprobieren: „wird mir ja sogar Spaß machen, das mal auszuprobieren“ | Pink Panther | – | [24:05] |

## Zahlen & Kosten
| Zahl | Bezug | TS |
|---|---|---|
| 3 | Ausbaustufen (Text-Tool, Live-Audio, mehrere Gesprächspartner) | [06:36] |
| 2 | Sprecher für den ersten Live-Fall (1:1); PP-Einwand gegen mehr | [07:51] |
| 3 | Antworten pro Anzeige (Argumentliste), PP-Vorschlag | [19:25] |
| ca. 90 % | Anteil sachlicher Aussagen in einer Debatte (Schätzung PP) | [18:49] |
| 10–15 GB | Arbeitsspeicher für den Stack hinter dem Audio-Modell (Heretic E4B) | [38:57] |
| unter 3 ms (Einheit unsicher) | Suchzeit pro Suche, BM25 + Vektor (red.fuchs; Transkript „unter drei unter Millisekunde“) | [37:25] |
| 2 | Decision-Modelle in der LFM3-Familie (Liquid AI) | [12:16] |
| 200 | Credits des Claude-Angebots (laut PP, bisher nicht nutzbar) | [28:10] |
| 25 | Wert im RAG-Abruf für Skills (vermutlich Trefferanzahl; Transkript unklar) | [29:43] |
| über 500 | Bücher (libertäre Literatur u. a.) im geplanten Chatbot-Korpus | [36:46] |
| unklar | Größe des Audio-Modells (Transkript „zwölf schnell 2 Billionen Parameter“) | [39:21] |
| ein paar Monate bis Jahre | Rückstand lokaler Modelle gegenüber Frontier-Modellen (Einschätzung red.fuchs) | [31:39] |
| mehr als zwei | Entwickler, ab dem Kanban für das Team relevant (PP) | [48:51] |

## Risiken
1. **Kleine Modelle scheitern an Denkschulen** (komplexer) — [10:37] red.fuchs: „ich glaube das scheitert dann bei Denkschulen, weil das ist komplexer.“
2. **Lokale Qualität schwankt** stark nach Bereich — [31:14] red.fuchs: „in anderen Bereichen hat's halt negativ Ausschläge nach unten“
3. **Keine Validierung** der Einschätzung bisher — [11:21] red.fuchs: „ich werde das natürlich nach validieren“
4. **Anthropic-Policy/Abrechnung** erschwert die Nutzung von Cloud-Modellen — [27:52] red.fuchs: „Ich muss aber ein bisschen aufpassen, seit Cloud Antropic ihre Policy geändert haben“
5. **Plattform-Abhängigkeit** des Overlays; Tests nur unter Windows möglich — [24:05] PP: „Also ich kann es da nur in Windows testen“
6. **Datenqualität** entscheidend für Klassifikation — [25:52] PP: „es sollte halt auch wirklich stimmen“
7. **Decision-Modell kann keine Inspiration** formulieren, nur Entscheidungen — [12:45] red.fuchs: „Es macht nur Entscheidungen.“
8. **Verzögerung:** red.fuchs für die nächsten Tage stark ausgebucht — [50:35] red.fuchs: „Die nächsten paar Tage werde ich sehr ausgebucht sein.“
9. **Kapazität PP** ungewiss — [50:55] PP: „eventuell bin ich viel zu langsam“
10. **Tonalität:** Persönlichkeit der Antworten schwer zu erreichen — [40:53] PP: „damit das wirklich Persönlichkeit hat und nicht einfach nur“
11. **Mehrere Sprecher im Audio** könnten stören — [08:14] red.fuchs: „Dann kommen halt auch mehrere Sachen rein.“

## Offene Fragen
1. Ziel-Sprache des Prototyps: „Sollen wir es auf eine Pie oder Rust Anwendung fokussieren“ (Transkript unklar) — [20:55]
2. Welches API-Protokoll für lokale und externe Modelle: „Open AIProtokoll ist natürlich Standard oder Lama-Standard“ — [10:11]
3. Ton der Antworten: „unbedingt sachlich und verdammt kurz“ (red.fuchs) vs. Persönlichkeit (PP) — [40:30]
4. Woher der Datensatz kommt (Suche, Kuration oder Synthese): PP [26:14] „Suchen ist nicht der richtige Begriff.“ — [26:14]
5. Denkschulen-Zuordnung: Classifier oder LLM? red.fuchs: „aber was es jetzt so größere Sachen angeht, wie zum Beispiel Denkschulen zuordnen“ — [11:02]
6. Hosting des Boards: GitHub-Seite oder PP-Website mit Login; PP: „Ich kann dir einfach auf meiner Website hosten sonst oder?“ — [50:10]
7. Ausgabefenster: Overlay oder Browser-Webserver; PP: „oder er macht halt einfach einen Webserver auf auf einen gewissen Porten“ — [21:26]
8. Umgang mit Mehrsprecher-Audio: red.fuchs: „Ich weiß halt nicht, ob das störend ist“ — [08:14]
