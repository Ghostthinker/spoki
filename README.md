# SpoKI

## Über das Projekt
SpoKI ist ein KI Assistent für Feedback zu Aufgaben, Lernzielen und Anforderungssituationen in Bezug auf das DOSB-Kompetenzmodell.

Damit erhalten Bildungsverantwortliche eine direkte Unterstützung durch Feedback und Rückmeldung auf ihre Lernaufgaben und Lehrgangskonzepte. Als Grundlage dienen SpoKI die Kriterien aus dem DOSB-Kompetenzmodell, sowie vorliegende und evaluierte Inhalte oder Materialien aus der DOSB-Lizenzausbildung.

Planen Ausbilder\*innen einen Lehrgang, können sie die Rahmenbedingungen (wie z.B. den Ablaufplan und die Lernaufgaben) in einer Eingabemaske eingeben und um Feedback bitten. SpoKI gleicht die Ideen mit dem Kompetenzmodell ab, gibt Feedback und kann auch Verbesserungsvorschläge machen. Die Ausbilder\*innen können SpoKI so als eine Art Tutor nutzen, der sie dabei unterstützt,  auf der Grundlage des DOSB-Kompetenzmodells (1)  Bildungsformate zu entwickeln und dabei (2) ihr Wissen über das Modell auszubauen.


## Beteiligte
Das Projekt SpoKI wurde durch das Bildungsteam des DOSB gemeinsam mit Vertrer\*innen aus den DOSB-Mitgliedsorganisationen entwickelt. Finanziell wurde das Projekt von der Deutschen Stiftung für Engagement und Ehrenamt in der Förderlinie Transform_D unterstützt. Die Laufzeit war vom 01.01. - 31.12.2024. Ziel war es, am Ende der Projektlaufzeit einen lauffähigen Prototyp zu haben, der von den Bildungsverantwortlichen genutzt werden kann. Dabei wurde der DOSB durch das Team der Ghostthinker GmbH didaktisch und technisch unterstützt.

# Technische Hinweise 

## Voraussetzungen

- **Ollama-Server** (empfohlen): Ein lokaler Ollama-Server mit **LLaMA 3.1 von Meta** muss laufen **ODER**
- **OpenAI-Zugang** (Alternative):
  - Es kann eine kompatible API wie z. B. IONOS verwendet werden.
  - Setze folgende Umgebungsvariablen in der `.env`:
    - `OPENAI_API_KEY`
    - `OPENAI_API_MODEL`
    - `OPENAI_API_BASE` (optional, für die Base-URL der kompatiblen API)

## Schritte zum Starten

1. Kopiere die `.env.example` in eine neue Datei `.env`:

   ```bash
   cp .env.example .env
   ```

2. Passe die .env-Datei an:

Für Ollama: Keine weiteren Anpassungen erforderlich.
Für OpenAI oder kompatible APIs: Trage den API-Schlüssel, das Modell und ggf. die Base-URL in die `.env`-Datei ein.

3. Erstelle die Authentifizierungsdatei:

   ```bash
    cp auth.example.yaml auth.yaml
   ```

4. Starte das Projekt:

   ```bash
    ./start.sh
   ```
