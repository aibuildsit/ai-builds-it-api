from flask import Flask, request, jsonify
import os
import requests
import json
import re

app = Flask(__name__)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


@app.get("/")
def home():
    return "AI BUILDS IT API is online!"


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Brak wiadomości"}), 400

    if not NVIDIA_API_KEY:
        return jsonify({"error": "Brak NVIDIA_API_KEY"}), 500

    system_prompt = """
Jesteś AI BUILDS IT.

Masz sterować budowaniem w Roblox.

Gdy użytkownik chce coś ZBUDOWAĆ, MUSISZ zwrócić dane bloków.

Każdy blok ma dokładnie rozmiar 1x1x1.

BARDZO WAŻNE:
Twoja odpowiedź MUSI być poprawnym JSON-em.
Nie pisz instrukcji dla Roblox Studio.
Nie pisz Markdown.
Nie używaj tabel.
Nie używaj ```.

FORMAT:

{
  "reply": "Gotowe!",
  "blocks": [
    {
      "x": 0,
      "y": 0,
      "z": 0,
      "color": [255, 0, 0]
    }
  ]
}

Przykład:

Użytkownik:
zbuduj ścianę 3x3

Musisz zwrócić:

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

Jeżeli użytkownik NIE chce budować:

{
  "reply": "Cześć!",
  "blocks": []
}

Maksymalnie 100 bloków w jednej odpowiedzi.
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
        "temperature": 0.0,
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

        return jsonify({
            "error": "Nie można połączyć się z NVIDIA API",
            "details": str(e)
        }), 502


    if response.status_code != 200:

        print(response.text)

        return jsonify({
            "error": "NVIDIA API error",
            "status": response.status_code,
            "details": response.text
        }), 502


    try:

        result = response.json()

        content = result["choices"][0]["message"]["content"]

        print("AI RESPONSE:")
        print(content)


        # Próba znalezienia JSON-a
        json_text = content.strip()

        # Usuwanie ```json
        json_text = re.sub(
            r"```json\s*",
            "",
            json_text,
            flags=re.IGNORECASE
        )

        json_text = re.sub(
            r"```\s*",
            "",
            json_text
        )

        # Szukanie pierwszego { i ostatniego }
        start = json_text.find("{")
        end = json_text.rfind("}")

        if start != -1 and end != -1:

            json_text = json_text[start:end + 1]


        ai_data = json.loads(json_text)


        if not isinstance(ai_data, dict):
            raise ValueError("JSON nie jest obiektem")


        reply = ai_data.get(
            "reply",
            "Gotowe!"
        )


        blocks = ai_data.get(
            "blocks",
            []
        )


        if not isinstance(blocks, list):
            blocks = []


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

                    color = [
                        255,
                        255,
                        255
                    ]


                color = [
                    max(
                        0,
                        min(
                            255,
                            int(color[0])
                        )
                    ),
                    max(
                        0,
                        min(
                            255,
                            int(color[1])
                        )
                    ),
                    max(
                        0,
                        min(
                            255,
                            int(color[2])
                        )
                    )
                ]


                valid_blocks.append({
                    "x": x,
                    "y": y,
                    "z": z,
                    "color": color
                })


            except (
                KeyError,
                ValueError,
                TypeError,
                IndexError
            ):

                continue


        valid_blocks = valid_blocks[:100]


        print(
            "VALID BLOCKS:",
            len(valid_blocks)
        )


        return jsonify({
            "reply": str(reply),
            "blocks": valid_blocks
        })


    except Exception as e:

        print(
            "JSON ERROR:",
            str(e)
        )

        return jsonify({
            "reply": "AI nie zwróciło poprawnych danych budowania.",
            "blocks": [],
            "error": str(e)
        }), 200


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
    
