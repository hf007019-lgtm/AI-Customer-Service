from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS

from ai_agents import call_department_agent

load_dotenv()
API_KEY = os.getenv("ALIYUN_API_KEY")

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "API 正常运行 🚀"

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    messages = [
        {"role": "system", "content": "你是电商客服"},
        {"role": "user", "content": user_msg}
    ]

    ai_msg = call_department_agent(messages, API_KEY)

    return jsonify({
        "reply": ai_msg.get("content", "出错了")
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)