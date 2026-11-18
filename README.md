# KI-Frust: lokaler Logikrätsel-Test

Ein lokaler Streamlit-Prototyp zum Thema **„Das Ende der Frustration"**. Alle
Teilnehmenden bearbeiten dieselben acht Vierer-Zuordnungsrätsel in fester
Reihenfolge. Zu Beginn wird zufällig eine Bedingung ausgelost:

- keine Hilfe,
- drei stufenweise statische Hinweise,
- ein kontextbezogener KI-Chat.

In den ersten vier Rätseln steht die ausgeloste Hilfe zur Verfügung. Ab Rätsel
fünf wird sie für alle Teilnehmenden entfernt. Die App erfasst Auswahlantworten,
Bearbeitungszeit, Frustbewertung und die Nutzung von Hinweisen bzw. KI-Chat.

## Lokal starten

Voraussetzung: Python 3.11 oder neuer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Anschließend öffnet sich die App normalerweise unter `http://localhost:8501`.

## KI einrichten

Öffne auf der Startseite **⚙ Einstellungen**. Dort wählst du Anbieter und
Modell, gibst den passenden API-Key ein und wählst **„Verbindung testen und
speichern"**. Die App testet dabei eine kurze echte Textanfrage gegen den
tatsächlich verwendeten Chat-Endpunkt.

Unterstützte Standardmodelle:

- OpenAI: `gpt-4.1-mini`
- Google Gemini: `gemini-2.5-flash-lite`, `gemini-2.5-flash`
- DeepSeek: `deepseek-chat`, `deepseek-reasoner`

Ein eigener Modellname kann ebenfalls gewählt werden. Die aktuelle Auswahl und
der gespeicherte Key werden auf der Startseite nur maskiert angezeigt. Zum
Ändern oder Löschen eines Keys öffnest du erneut die Einstellungen.

### Lokale Secrets-Datei

Keys werden lokal in `.streamlit/secrets.toml` gespeichert. Die Datei ist in
`.gitignore` und wird nicht veröffentlicht. Als Orientierung liegt
`.streamlit/secrets.example.toml` ohne Key im Repository. Die App legt die
echte Datei erst nach einem erfolgreichen Verbindungstest an.

Teile die echte `secrets.toml` niemals. Wer das Repository selbst lokal startet,
hinterlegt einen eigenen Key über die Einstellungen.

## Fehlerhilfe für Anbieter

- **Gemini:** Die App hält den Google-Client während der gesamten Anfrage offen.
  Der frühere Fehler „client has been closed" sollte dadurch nicht mehr auftreten.
- **DeepSeek:** Die App prüft keine Modell-Metadaten mehr. Ein 404 für
  `deepseek-chat` beim Modellabruf bedeutet deshalb nicht mehr, dass ein gültiger
  Key fälschlich abgelehnt wird.
- Bei ungültigem Key, fehlendem Modellzugriff, Guthaben-/Rate-Limits oder
  Netzwerkproblemen erscheint eine gesonderte, deutschsprachige Meldung.

## Lokale Daten

Ergebnisse liegen ausschließlich in `data/ki_frust.db`. Die Datei wird beim
ersten Start automatisch angelegt und ist ebenfalls durch `.gitignore`
geschützt. Das Dashboard zeigt ausschließlich abgeschlossene Tests aus dieser
lokalen Installation an. Separate Klone oder Rechner teilen keine Daten.

Gespeichert werden anonyme Sitzungs-IDs, Bedingung, Anbieter, Modell,
Antworten, Lösungsrichtigkeit, Bearbeitungszeiten, Frustwerte und Anzahl der
Hinweise bzw. KI-Nachrichten. Nicht gespeichert werden Namen, E-Mail-Adressen,
IP-Adressen, API-Keys oder Chatnachrichten.

Um mit einer leeren Datensammlung zu beginnen, beende die App und lösche nur
`data/ki_frust.db`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Hinweis zur Durchführung

Die App ist ein Lehr- und Demonstrationsprototyp, keine zentral betriebene
Studienplattform. Personen sollten freiwillig teilnehmen und im KI-Chat keine
personenbezogenen Daten eingeben. Für ein gemeinsames lokales Dashboard müssen
alle Tests dieselbe App-Installation bzw. SQLite-Datei verwenden.
