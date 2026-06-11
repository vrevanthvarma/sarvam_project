"""
MahaConnect AI – Flask Backend
Trilingual Translation Hub: Telugu ↔ Hindi ↔ English
Powered by Sarvam AI official Python SDK (sarvamai)
"""

import os
import base64
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template
from sarvamai import SarvamAI

# ──────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024   # 25 MB upload limit

# Sarvam client is initialized per-request so the key is read fresh each call
def get_client():
    api_key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "SARVAM_API_KEY environment variable is not set. "
            "Please set it before running the server."
        )
    return SarvamAI(api_subscription_key=api_key)


# ──────────────────────────────────────────────
# Language helpers
# ──────────────────────────────────────────────
LANGUAGE_LABELS = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "te-IN": "Telugu",
}

# Speaker voices per language for TTS (bulbul:v3)
TTS_SPEAKERS = {
    "en-IN": "ritu",
    "hi-IN": "pooja",
    "te-IN": "priya",
}


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/api/translate", methods=["POST"])
def translate():
    """
    Translate text using Sarvam AI.
    Body JSON: { "text": str, "source": str, "target": str }
    Returns: { "translated_text": str, "detected_language": str }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Request body must be JSON."}), 400

        text = (data.get("text") or "").strip()
        source = (data.get("source") or "auto").strip()
        target = (data.get("target") or "en-IN").strip()

        if not text:
            return jsonify({"error": "Input text cannot be empty."}), 400
        if len(text) > 2000:
            return jsonify({"error": "Input text exceeds 2000 character limit."}), 400

        client = get_client()

        # Use sarvam-translate:v1 which supports auto detection + all 3 languages
        response = client.text.translate(
            input=text,
            source_language_code=source,
            target_language_code=target,
            model="sarvam-translate:v1",
            mode="formal",
        )

        return jsonify({
            "translated_text": response.translated_text,
            "detected_language": response.source_language_code or source,
            "detected_language_label": LANGUAGE_LABELS.get(
                response.source_language_code or source,
                response.source_language_code or source
            ),
        })

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as exc:
        # Log full traceback to server console for debugging
        traceback.print_exc()
        return jsonify({"error": f"Translation failed: {str(exc)}"}), 500


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """
    Transcribe audio to text using Sarvam AI (saarika:v2.5).
    Multipart form: file=<audio>, language=<code or 'unknown'>
    Returns: { "transcript": str, "language_code": str }
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No audio file provided. Include 'file' in form data."}), 400

        audio_file = request.files["file"]
        if audio_file.filename == "":
            return jsonify({"error": "Empty filename. Please select a valid audio file."}), 400

        language_code = (request.form.get("language") or "unknown").strip()

        # Save to a temporary file so Sarvam SDK can read it
        suffix = os.path.splitext(audio_file.filename)[-1].lower() or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        try:
            client = get_client()

            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            # Pass raw bytes via file tuple: (filename, bytes, content_type)
            response = client.speech.transcribe(
                file=(os.path.basename(tmp_path), audio_bytes, "audio/wav"),
                model="saarika:v2.5",
                language_code=language_code,
            )

            return jsonify({
                "transcript": response.transcript,
                "language_code": response.language_code or language_code,
                "language_label": LANGUAGE_LABELS.get(
                    response.language_code or language_code,
                    response.language_code or language_code
                ),
            })
        finally:
            # Always clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Transcription failed: {str(exc)}"}), 500


@app.route("/api/speak", methods=["POST"])
def speak():
    """
    Convert text to speech using Sarvam AI (bulbul:v3).
    Body JSON: { "text": str, "language": str }
    Returns: { "audio_base64": str }   (WAV, base64-encoded)
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Request body must be JSON."}), 400

        text = (data.get("text") or "").strip()
        language = (data.get("language") or "en-IN").strip()

        if not text:
            return jsonify({"error": "Text cannot be empty."}), 400
        if len(text) > 2500:
            return jsonify({"error": "Text exceeds 2500 character limit for TTS."}), 400

        speaker = TTS_SPEAKERS.get(language, "ritu")
        client = get_client()

        response = client.text_to_speech.convert(
            text=text,
            target_language_code=language,
            speaker=speaker,
            model="bulbul:v3",
            speech_sample_rate=22050,
            pace=1.0,
        )

        # response.audios is a list of base64-encoded WAV strings
        if not response.audios:
            return jsonify({"error": "No audio returned from Sarvam TTS API."}), 500

        return jsonify({"audio_base64": response.audios[0]})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Text-to-speech failed: {str(exc)}"}), 500


@app.route("/api/detect_language", methods=["POST"])
def detect_language():
    """
    Detect the language of input text.
    Body JSON: { "text": str }
    Returns: { "language_code": str, "language_label": str }
    """
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()

        if not text:
            return jsonify({"error": "Text cannot be empty."}), 400

        client = get_client()
        response = client.text.identify_language(input=text)

        lang_code = response.language_code or "unknown"
        return jsonify({
            "language_code": lang_code,
            "language_label": LANGUAGE_LABELS.get(lang_code, lang_code),
        })

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Language detection failed: {str(exc)}"}), 500


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("   MahaConnect AI — Sarvam AI Translation Hub")
    print("="*60)
    print("  Open your browser at:  http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
