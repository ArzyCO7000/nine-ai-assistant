import os
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
import openai
import requests

app = Flask(__name__)

@app.route("/voice", methods=["POST"])
def voice():
    resp = VoiceResponse()
    resp.say("Welcome to Nine. How can I help you?")
    resp.record(
        transcribe=False,
        max_length=10,
        timeout=1,
        action="/transcription"
    )
    return str(resp)

@app.route("/transcription", methods=["POST"])
def transcription():
    recording_url = request.form["RecordingUrl"] + ".mp3"
    user_input = transcribe_audio(recording_url)
    reply = gpt_response(user_input)
    generate_voice(reply)

    resp = VoiceResponse()
    resp.play("https://nine-ai-assistant.onrender.com/response.mp3")
    return str(resp)

def transcribe_audio(url):
    audio = requests.get(url)
    with open("input.mp3", "wb") as f:
        f.write(audio.content)

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=open("input.mp3", "rb")
    )
    return transcript.text

def gpt_response(user_input):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = """
    You are a friendly and classy assistant for the restaurant Nine, located on the top floor of Radisson Red Hotel in North Greenwich, London.

    Your job is to answer caller questions about:
    - bookings (make, change, cancel)
    - running late
    - directions and parking
    - opening hours, last order times
    - dress code (smart casual, no tracksuits)
    - age policy (18+ after 8pm, children welcome before)
    - shisha (not available)
    - alcohol (served)
    - halal status (yes, all meats are halal)
    - private events and large group bookings

    If a customer is rude, vague or confused — stay polite but direct.

    Don’t waffle. Keep answers short, helpful and in a classy tone.
    """

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return completion.choices[0].message.content.strip()

def generate_voice(text):
    eleven_api = os.getenv("ELEVEN_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID")

    headers = {
        "xi-api-key": eleven_api,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers=headers,
        json=payload
    )

    with open("response.mp3", "wb") as f:
        f.write(response.content)

@app.route("/response.mp3")
def serve_audio():
    return send_file("response.mp3", mimetype="audio/mpeg")
