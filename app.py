from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
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

    system_prompt = """
Jesteś AI BUILDS IT dla Roblox.

Twoim zadaniem jest zamieniać polecenia gracza na budowanie z klocków.

KAŻDY klocek ma rozmiar 1x1x1.

Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.

Format:

{
  "reply": "krótka wiadomość dla gracza",
  "blocks": [
    {
      "x": 0,
      "y": 0,
      "z": 0,
      "color": [255, 0, 0]
    }
  ]
}

Zasady:
- x, y, z muszą być liczbami całkowitymi.
- color to [R,G,B], każda liczba od 0 do 255.
- Jeden element blocks = jeden klocek 1x1x1.
- Nie twórz więcej niż 500 klocków w jednej odpowiedzi.
- Jeśli gracz nie prosi o budowanie, blocks ma być pustą tablicą.
- Nie dodawaj markdownu.
- Nie dodawaj ```json.
"""

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.2,
        "max_tokens": 4000
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
            "error": "Nie można połączyć się z NVIDIA API"
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
        content = result["choices"][0]["message"]["content"]

        ai_data = json.loads(content)

        if "reply" not in ai_data:
            ai_data["reply"] = "Gotowe!"

        if "blocks" not in ai_data:
            ai_data["blocks"] = []

        return jsonify(ai_data)

    except Exception as e:
        print("INVALID AI RESPONSE:", response.text)
        print("ERROR:", str(e))

        return jsonify({
            "error": "AI zwróciło nieprawidłowy JSON"
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
