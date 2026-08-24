from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

@app.get("/")
def home():
    return "AI BUILDS IT API is online!"

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Brak wiadomości"}), 400

    if not NVIDIA_API_KEY:
        return jsonify({"error": "Brak NVIDIA_API_KEY"}), 500

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "system",
                "content": "Jesteś AI BUILDS IT. Pomagasz graczowi tworzyć konstrukcje w Robloxie."
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    response = requests.post(
        NVIDIA_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        return jsonify({
            "error": "NVIDIA API error",
            "details": response.text
        }), 502

    result = response.json()

    reply = result["choices"][0]["message"]["content"]

    return jsonify({
        "reply": reply
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
