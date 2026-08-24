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
                "content": (
                    "Jesteś AI BUILDS IT. "
                    "Pomagasz graczowi tworzyć konstrukcje w Robloxie. "
                    "Odpowiadaj jasno i krótko."
                )
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            NVIDIA_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
    except requests.RequestException as e:
        print("REQUEST ERROR:", str(e))
        return jsonify({
            "error": "Nie można połączyć się z NVIDIA API",
            "details": str(e)
        }), 502

    if response.status_code != 200:
        print("NVIDIA STATUS:", response.status_code)
        print("NVIDIA RESPONSE:", response.text)

        return jsonify({
            "error": "NVIDIA API error",
            "status": response.status_code,
            "details": response.text
        }), 502

    try:
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as e:
        print("INVALID NVIDIA RESPONSE:", response.text)
        return jsonify({
            "error": "Nieprawidłowa odpowiedź NVIDIA",
            "details": str(e)
        }), 502

    return jsonify({
        "reply": reply
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
