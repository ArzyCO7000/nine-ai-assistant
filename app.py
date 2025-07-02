from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
import openai
import requests
import os

app = Flask(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()
    response.say("Hello, welcome to Nine. Please tell me how I can help you.", voice='Polly.Joanna')
    response.record(timeout=2, transcribe=True, transcribe_callback="/transcription")
    return str(response)

@app.route("/transcription", methods=['POST'])
def transcription():
    user_input = request.form.get('TranscriptionText', '')
    reply = gpt_response(user_input)
    audio_url = generate_tts(reply)
    
    response = VoiceResponse()
    response.play(audio_url)
    response.hangup()
    return str(response)

def gpt_response(prompt):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    system_prompt = "You are a classy virtual assistant for a high-end restaurant in London called Nine. The caller said: " + prompt
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": system_prompt}]
    )
    return res.choices[0].message.content

def generate_tts(text):
    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
    VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    tts_response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream",
        headers=headers,
        json=data
    )

    with open("response.mp3", "wb") as f:
        f.write(tts_response.content)

    return "https://yourdomain.com/response.mp3"  # We will replace this with a real file host later

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

