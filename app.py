from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

MODEL = "openai/gpt-oss-20b"


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
Jesteś AI BUILDS IT dla Roblox.

Twoim zadaniem jest odpowiadać na polecenia gracza
i tworzyć instrukcje budowania.

Każdy klocek ma rozmiar 1x1x1.

Jeżeli gracz chce coś zbudować, zwróć odpowiednie
elementy w tablicy blocks.

Jeżeli gracz nie chce budować, blocks musi być pustą tablicą.

Nie opisuj jak budować w Roblox Studio.
Nie dawaj poradników.
Nie używaj Markdown.

Zwróć dane zgodne ze schematem JSON.

Przykład dla:
"zbuduj ścianę 3x3"

blocks powinno zawierać dokładnie 9 klocków:

x,y,z są liczbami całkowitymi.
color jest tablicą RGB.
"""


    schema = {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string"
            },
            "blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer"
                        },
                        "y": {
                            "type": "integer"
                        },
                        "z": {
                            "type": "integer"
                        },
                        "color": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            },
                            "minItems": 3,
                            "maxItems": 3
                        }
                    },
                    "required": [
                        "x",
                        "y",
                        "z",
                        "color"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": [
            "reply",
            "blocks"
        ],
        "additionalProperties": False
    }


    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


    payload = {
        "model": MODEL,

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

        "temperature": 0,

        "max_tokens": 4096,

        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "roblox_build",
                "schema": schema
            }
        }
    }


    try:
        response = requests.post(
            NVIDIA_URL,
            headers=headers,
            json=payload,
            timeout=45
        )

    except requests.Timeout:
        return jsonify({
            "error": "NVIDIA API timeout"
        }), 504

    except requests.RequestException as e:
        print("REQUEST ERROR:", str(e))

        return jsonify({
            "error": "Nie można połączyć się z NVIDIA API"
        }), 502


    # NVIDIA może zwrócić 202.
    if response.status_code == 202:

        print("NVIDIA zwróciło 202 - wynik oczekuje.")

        return jsonify({
            "error": "NVIDIA API nadal przetwarza żądanie. Spróbuj ponownie."
        }), 503


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

        print("AI RESPONSE:")
        print(content)


        ai_data = json.loads(content)


        if not isinstance(ai_data, dict):
            raise ValueError("AI nie zwróciło obiektu JSON")


        reply = str(
            ai_data.get(
                "reply",
                "Gotowe!"
            )
        )


        blocks = ai_data.get(
            "blocks",
            []
        )


        if not isinstance(blocks, list):
            blocks = []


        valid_blocks = []


        # Maksymalnie 100 bloków na jedno żądanie.
        for block in blocks[:100]:

            if not isinstance(block, dict):
                continue

            try:

                x = int(block["x"])
                y = int(block["y"])
                z = int(block["z"])

                color = block["color"]

                if not isinstance(color, list):
                    continue

                if len(color) != 3:
                    continue

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


            except (
                KeyError,
                TypeError,
                ValueError,
                IndexError
            ):
                continue


        print(
            "VALID BLOCKS:",
            len(valid_blocks)
        )


        return jsonify({
            "reply": reply,
            "blocks": valid_blocks
        })


    except Exception as e:

        print("JSON ERROR:", str(e))
        print("RAW RESPONSE:", response.text)

        return jsonify({
            "error": "Nieprawidłowa odpowiedź AI",
            "details": str(e)
        }), 502


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
