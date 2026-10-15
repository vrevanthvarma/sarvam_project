# MahaConnect AI

A trilingual speech and translation hub for **Telugu, Hindi and English**, built with Flask and the [Sarvam AI](https://www.sarvam.ai/) Python SDK.

Type or speak in one language, get the translation in another, and hear it read aloud.

## Features

| Feature | Endpoint | Sarvam model |
|---|---|---|
| Text translation (formal mode, auto language detection) | `POST /api/translate` | `sarvam-translate:v1` |
| Speech-to-text from browser recordings or uploaded audio | `POST /api/transcribe` | `saarika:v2.5` |
| Text-to-speech with a voice per language | `POST /api/speak` | `bulbul:v3` |
| Language detection | `POST /api/detect_language` | language identification |

The browser client (`templates/index.html`) is plain HTML, CSS and JavaScript. It records from the microphone with the MediaRecorder API, plays back the generated audio, and has a copy-to-clipboard option.

## API reference

**`POST /api/translate`**: JSON `{ "text": "...", "source": "auto" | "en-IN" | "hi-IN" | "te-IN", "target": "en-IN" | "hi-IN" | "te-IN" }`
Returns `{ "translated_text", "detected_language", "detected_language_label" }`. Text is limited to 2,000 characters.

**`POST /api/transcribe`**: multipart form with `file` (audio) and optional `language` (defaults to `unknown` for auto-detection).
Returns `{ "transcript", "language_code", "language_label" }`.

**`POST /api/speak`**: JSON `{ "text": "...", "language": "en-IN" | "hi-IN" | "te-IN" }`
Returns `{ "audio_base64" }` (a base64-encoded WAV). Text is limited to 2,500 characters.

**`POST /api/detect_language`**: JSON `{ "text": "..." }`
Returns `{ "language_code", "language_label" }`.

Invalid input returns HTTP 400 with `{ "error": "..." }`. Upstream failures return HTTP 500 with an error message, and the full traceback is logged on the server. Uploads are capped at 25 MB, and temporary audio files are always deleted after transcription.

## Run it locally

Requires Python 3.9+ and a Sarvam AI API key.

```bash
git clone https://github.com/vrevanthvarma/sarvam_project.git
cd sarvam_project
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your own key in it:

```
SARVAM_API_KEY=your_sarvam_api_key_here
```

Start the server with the Flask CLI, which loads `.env` automatically:

```bash
flask --app app run
```

Then open http://127.0.0.1:5000.

If you run `python app.py` instead, set `SARVAM_API_KEY` as an environment variable first, because that command does not read `.env`.

> Never commit `.env`. It is listed in `.gitignore`.

## Tech stack

Python · Flask · Sarvam AI SDK (`sarvamai`) · HTML · CSS · JavaScript

## Author

Vejandla Revanth Varma · [GitHub](https://github.com/vrevanthvarma) · [LinkedIn](https://www.linkedin.com/in/vrevanthvarma)
