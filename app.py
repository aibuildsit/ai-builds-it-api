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
Jesteś AI BUILDS IT dla gry Roblox.

Twoim zadaniem jest wykonywanie poleceń gracza dotyczących budowania.

BARDZO WAŻNE:
Zawsze odpowiadaj WYŁĄCZNIE poprawnym JSON-em.
NIE używaj Markdown.
NIE używaj ```.
NIE dodawaj tabel.
NIE pisz nic poza JSON-em.

Format odpowiedzi MUSI wyglądać dokładnie tak:

{
  "reply": "krótka odpowiedź dla gracza",
  "blocks": [
    {
      "x": 0,
      "y": 0,
      "z": 0,
      "color": [255, 0, 0]
    }
  ]
}

ZASADY BUDOWANIA:

- Każdy element "blocks" oznacza dokładnie jeden klocek 1x1x1.
- x, y oraz z muszą być liczbami całkowitymi.
- color musi być tablicą [R,G,B].
- R, G i B muszą być liczbami od 0 do 255.
- Maksymalnie 500 elementów w "blocks".
- Jeśli gracz prosi o ścianę 5x5, wygeneruj 25 bloków.
- Jeśli gracz prosi o podłogę 10x10, wygeneruj 100 bloków.
- Nie twórz jednego dużego Parta.
- Każdy blok ma być osobnym elementem.
- Jeśli gracz nie prosi o budowanie, zwróć "blocks": [].
- Jeśli polecenie jest niejasne, zapytaj gracza w "reply" i zwróć "blocks": [].

PRZYKŁAD:

Polecenie:
zbuduj ścianę 3x3

Odpowiedź:
{
  "reply": "Gotowe! Zbudowałem ścianę 3x3.",
  "blocks": [
    {"x":0,"y":0,"z":0,"color":[255,0,0]},
    {"x":1,"y":0,"z":0,"color":[255,0,0]},
    {"x":2,"y":0,"z":0,"color":[255,0,0]},
    {"x":0,"y":1,"z":0,"color":[255,0,0]},
    {"x":1,"y":1,"z":0,"color":[255,0,0]},
    {"x":2,"y":1,"z":0,"color":[255,0,0]},
    {"x":0,"y":2,"z":0,"color":[255,0,0]},
    {"x":1,"y":2,"z":0,"color":[255,0,0]},
    {"x":2,"y":2,"z":0,"color":[255,0,0]}
  ]
}
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
        "temperature": 0.1,
        "max_tokens": 4000,
        "response_format": {
            "type": "json_object"
        }
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

        content = result["choices"][0]["message"]["content"]

        print("AI RAW RESPONSE:")
        print(content)

        ai_data = json.loads(content)

        if not isinstance(ai_data, dict):
            raise ValueError("Odpowiedź AI nie jest obiektem JSON")

        reply = ai_data.get("reply", "Gotowe!")
        blocks = ai_data.get("blocks", [])

        if not isinstance(blocks, list):
            blocks = []

        # Maksymalnie 500 bloków z jednej odpowiedzi
        blocks = blocks[:500]

        valid_blocks = []

        for block in blocks:

            if not isinstance(block, dict):
                continue

            try:
                x = int(block["x"])
                y = int(block["y"])
                z = int(block["z"])

                color = block.get(
                    "color",
                    [255, 255, 255]
                )

                if (
                    not isinstance(color, list)
                    or len(color) != 3
                ):
                    color = [255, 255, 255]

                color = [
                    max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2])))
                ]

                valid_blocks.append({
                    "x": x,
                    "y": y,
                    "z": z,
                    "color": color
                })

            except (KeyError, ValueError, TypeError, IndexError):
                continue

        print("VALID BLOCKS:", len(valid_blocks))

        return jsonify({
            "reply": str(reply),
            "blocks": valid_blocks
        })

    except Exception as e:

        print("INVALID AI RESPONSE:")
        print(response.text)
        print("ERROR:", str(e))

        return jsonify({
            "error": "AI zwróciło nieprawidłowy JSON",
            "details": str(e)
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
