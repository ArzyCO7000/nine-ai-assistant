import os
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import requests

from pydub import AudioSegment

app = Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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

def gpt_response(user_input):
    system_prompt = "You are a polite and helpful phone assistant for a classy rooftop restaurant in London called Nine."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()

def transcribe_audio(url):
    audio = requests.get(url)
    with open("input.mp3", "wb") as f:
        f.write(audio.content)

    audio_data = open("input.mp3", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_data
    )
    return transcript.text

def generate_voice(text):
    eleven_api = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ["ELEVENLABS_VOICE_ID"]
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

@app.route("/response.mp3", methods=["GET"])
def serve_audio():
    return send_file("response.mp3", mimetype="audio/mpeg")
