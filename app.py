from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.get("/")
def home():
    return "AI BUILDS IT API is online!"

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    return jsonify({
        "reply": "Otrzymałem: " + message
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
