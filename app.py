import streamlit as st
from dashscope import Generation, MultiModalConversation
import sqlite3
import json
import base64
import uuid

# ==========================================
# 1. 数据库逻辑 (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    # 创建商品表 (修复了 tags TEXT 的空格问题)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS t_product(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            tags TEXT, 
            description TEXT,
            status INTEGER NOT NULL DEFAULT 1
        )
    ''')
    # 创建聊天日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS t_chat_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 初始化数据
    cursor.execute("SELECT COUNT(*) FROM t_product")
    if cursor.fetchone()[0] == 0:
        products = [
            ('雷蛇黑寡妇机械键盘', '数码外设', 699.00, 150, '机械键盘,电竞,RGB背光', '适合电竞玩家的高端机械键盘。'),
            ('罗技 MX Master 3S 鼠标', '数码外设', 599.00, 200, '办公神器,人体工学,静音', '程序员首选的人体工学无线鼠标。'),
            ('Sony WH-1000XM5 降噪耳机', '影音娱乐', 1999.00, 50, '主动降噪,头戴式,高保真', '行业顶级的头戴式主动降噪耳机。'),
            ('Akko 樱花粉机械键盘', '数码外设', 459.00, 80, '猛男粉,定制键帽,高颜值', '粉色系高颜值键盘，送礼绝佳。'),
            ('人体工学护腰靠垫', '家居日用', 89.00, 500, '记忆棉,护腰,久坐必备', '缓解久坐疲劳。')
        ]
        cursor.executemany('INSERT INTO t_product (product_name, category, price, stock, tags, description) VALUES (?, ?, ?, ?, ?, ?)', products)
    conn.commit()
    conn.close()

init_db()

def fetch_products_from_sqlite():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price, stock, tags, description FROM t_product WHERE status = 1")
    results = cursor.fetchall()
    conn.close()
    if not results: return "当前店铺没有上架任何商品。"
    return "\n".join([f"【{row['product_name']}】 - 售价: {row['price']}元 | 库存: {row['stock']}件。" for row in results])

def save_chat_to_sqlite(session_id, role, content):
    try:
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO t_chat_log (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, str(content)))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

# ==========================================
# 2. UI 工具与大模型配置
# ==========================================
def render_checkout_card(product_name, price):
    """前端 UI 工具：在网页上画出一个精美的结算单 (被你弄丢的函数找回来啦)"""
    st.balloons()
    st.success("🎉 AI 已为您生成专属订单！")
    with st.container(border=True):
        st.markdown(f"### 🛍️ 购买商品：{product_name}")
        st.markdown(f"**应付金额：** <span style='color:red; font-size:24px'>¥{price}</span>", unsafe_allow_html=True)
        st.text_input("📍 收货地址", placeholder="请输入您的详细地址...")
        st.button("立即微信支付 💳", type="primary", use_container_width=True)

tools = [{
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "当用户明确决定购买某件商品时，必须调用此函数来生成结算单。",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "用户要购买的商品全称"},
                "price": {"type": "number", "description": "该商品的单价"}
            },
            "required": ["product_name", "price"]
        }
    }
}]

# ==========================================
# 3. 页面初始化
# ==========================================
st.set_page_config(page_title="AI 智能体店长", page_icon="🛒", layout="centered")
st.title("🛒 拥有行动力的 AI 店长")

# ⚠️ 这里填入你的 API Key
ALIYUN_API_KEY = "sk-7e8c34117bf94c02af0edde27837b553"

if "messages" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) # 给顾客发身份证
    real_time_product_data = fetch_products_from_sqlite() # 改成调 sqlite 了
    system_prompt = f"""
    你是本店的 AI 店长。你的任务是推销以下商品：
    {real_time_product_data}

    【极其重要的指令】：
    如果用户明确表示“我要买”、“帮我下单”、“就买这个了”，你**必须**调用 `create_order` 函数，不要回复废话！
    """
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# ==========================================
# 4. 侧边栏多模态视觉引擎
# ==========================================
with st.sidebar:
    st.markdown("### 👁️ 专属视觉引擎")
    st.markdown("不知道买啥？发张你的照片，让 AI 帮你搭配！")
    uploaded_image = st.file_uploader("📸 上传照片", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        st.image(uploaded_image, caption="已上传照片", use_container_width=True)
        base64_image = f"data:image/jpeg;base64,{base64.b64encode(uploaded_image.getvalue()).decode('utf-8')}"
        if st.button("开始视觉分析 🚀", type="primary"):
            with st.spinner("正在用“火眼金睛”分析图片..."):
                current_db_data = fetch_products_from_sqlite() # 修复了旧名字
                vision_messages = [{
                    "role": "user",
                    "content": [
                        {"image": base64_image},
                        {"text": f"请分析图片，基于商品库推荐商品。\n\n【商品库】\n{current_db_data}"}
                    ]
                }]
                response = MultiModalConversation.call(api_key=ALIYUN_API_KEY, model='qwen-vl-max', messages=vision_messages)
                vision_result = response.output.choices[0].message.content[0]["text"]
                st.success("分析完成！")
                st.write(vision_result)
                st.session_state.messages.append({"role": "assistant", "content": f"（视觉分析结论）：{vision_result}"})
                save_chat_to_sqlite(st.session_state.session_id, "assistant", f"（视觉分析结论）：{vision_result}")

# ==========================================
# 5. 主聊天区域与工具调用
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] not in ["system", "tool"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("想买点什么？或者直接说‘帮我下单xx’"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat_to_sqlite(st.session_state.session_id, "user", prompt) # 记录用户说话

    with st.chat_message("assistant"):
        with st.spinner("🤖 店长正在处理..."):
            response = Generation.call(
                api_key=ALIYUN_API_KEY,
                model="deepseek-v3",
                messages=st.session_state.messages,
                result_format="message",
                tools=tools
            )

            message = response.output.choices[0].message

            if "tool_calls" in message and message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                if function_name == "create_order":
                    render_checkout_card(arguments["product_name"], arguments["price"])
                    ai_reply = f"好的，已经为您生成【{arguments['product_name']}】的结算单，请核对支付！"
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    save_chat_to_sqlite(st.session_state.session_id, "assistant", ai_reply) # 记录AI下单
            else:
                ai_reply = message.content
                st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                save_chat_to_sqlite(st.session_state.session_id, "assistant", ai_reply) # 记录AI说话