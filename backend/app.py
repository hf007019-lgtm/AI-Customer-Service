from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import uuid

# 导入你的业务层和数据层
from database import init_db, fetch_products, save_chat
from ai_agents import TOOLS, get_router_intent, call_department_agent, call_vision_agent

app = Flask(__name__, template_folder='../frontend')
CORS(app)  # 允许跨域请求

# 初始化数据
init_db()
db_data = fetch_products()

load_dotenv()
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")

if not ALIYUN_API_KEY:
    print("⚠️ 警告：未检测到 ALIYUN_API_KEY，请检查 .env 文件！")

# 内存 Session 存储池
sessions = {}


@app.route('/')
def index():
    """渲染前端页面"""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """核心聊天 API 接口"""
    data = request.get_json()
    user_message = data.get('message', '')  # 默认给空字符串防止报错
    session_id = data.get('session_id')
    base64_image = data.get('image')  # 🌟 获取前端传来的图片

    # 校验：没说话也没发图直接拦截
    if not user_message and not base64_image:
        return jsonify({"reply": "消息和图片不能同时为空"}), 400

    # 动态读取或生成 session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = []

    # 整理日志：记录用户的聊天或发图行为
    log_msg = user_message if user_message else "[发送了一张图片]"
    if base64_image and user_message:
        log_msg += " [附带图片]"

    sessions[session_id].append({"role": "user", "content": log_msg})
    save_chat(session_id, "user", log_msg)

    try:
        # 核心判断：是走纯文本还是走视觉大模型？
        if base64_image:
            # 进入视觉分支
            vision_res = call_vision_agent(base64_image, db_data, ALIYUN_API_KEY)
            reply = f"👁️ **图片解析结果**<br><br>{vision_res}"

        else:
            # 进入原本的纯文本业务分支
            dept = get_router_intent(user_message, ALIYUN_API_KEY)

            if dept == "Checkout":
                sys_prompt = "你是结算员。请调用 create_order 工具生成订单信息。"
                tools = TOOLS
            elif dept == "Inventory":
                sys_prompt = f"你是库管。基于以下数据客观回答库存与价格问题：\n{db_data}"
                tools = None
            else:
                sys_prompt = f"你是金牌导购。根据商品库提供专业的搭配建议：\n{db_data}"
                tools = None

            msgs = [{"role": "system", "content": sys_prompt}] + sessions[session_id][-4:]
            ai_res = call_department_agent(msgs, ALIYUN_API_KEY, tools)

            tool_calls = ai_res.get("tool_calls")
            if tool_calls:
                params = json.loads(tool_calls[0]["function"]["arguments"])
                product_name = params.get('product_name')
                price = params.get('price')
                reply = f"💳 **收银台已为您生成订单**<br><br>商品：{product_name}<br>金额：¥{price}<br><br><i>请确认无误后完成支付。</i>"
            else:
                reply = ai_res.get("content", "抱歉，暂时无法处理该请求。")

        # 无论哪个分支，统一保存记忆并返回
        sessions[session_id].append({"role": "assistant", "content": reply})
        save_chat(session_id, "assistant", reply)

        # 把大模型返回文本里的换行符(\n)替换为HTML换行符(<br>)，让排版更美观
        return jsonify({"reply": reply.replace('\n', '<br>')})

    except Exception as e:
        return jsonify({"reply": f"系统繁忙，请稍后再试: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)