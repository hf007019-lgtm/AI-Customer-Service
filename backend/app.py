import streamlit as st
import base64
import uuid
import json

from database import init_db, fetch_products, save_chat
from ai_agents import TOOLS, get_router_intent, call_department_agent, call_vision_agent
from dotenv import load_dotenv
import os

load_dotenv()

ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")

# 初始化应用依赖
init_db()


def render_checkout_card(product_name, price):
    """渲染订单支付组件 UI"""
    st.success("收银台已为您生成专属订单")
    with st.container(border=True):
        st.markdown(f"### 购买商品：{product_name}")
        st.markdown(f"**应付金额：** <span style='color:red; font-size:24px'>¥{price}</span>", unsafe_allow_html=True)
        st.text_input("收货地址", placeholder="请输入您的详细地址...")
        st.button("立即微信支付", type="primary", use_container_width=True)


# 基础页面配置
st.set_page_config(page_title="AI Store", layout="centered")
st.title("AI 智能导购系统")


# Session State 初始化
if "messages" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []

# 预加载商品上下文
db_data = fetch_products()

# ================= Sidebar: 视觉分析模块 =================
with st.sidebar:
    st.markdown("### 图像识别测试")
    uploaded_image = st.file_uploader("上传参考图", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded", use_container_width=True)
        base64_image = f"data:image/jpeg;base64,{base64.b64encode(uploaded_image.getvalue()).decode('utf-8')}"
        if st.button("开始分析", type="primary"):
            with st.spinner("处理中..."):
                vision_result = call_vision_agent(base64_image, db_data, ALIYUN_API_KEY)
                st.write(vision_result)
                # 将视觉结果静默注入上下文
                st.session_state.messages.append({"role": "assistant", "content": f"（图片解析结论）：{vision_result}"})

# ================= Main: 会话历史渲染 =================
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ================= Main: 核心交互逻辑 =================
if prompt := st.chat_input("输入对话内容..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat(st.session_state.session_id, "user", prompt)

    with st.chat_message("assistant"):
        with st.status("处理中...", expanded=True) as status:
            # 1. Intent Routing (意图识别)
            target_department = get_router_intent(prompt, ALIYUN_API_KEY)

            # 2. 组装对应 Agent 的上下文策略
            if target_department == "Checkout":
                status.update(label="路由到: Checkout Agent", state="running")
                agent_prompt = "你是收银员。立刻调用 create_order 工具，不要返回其他闲聊文本。"
                active_tools = TOOLS
            elif target_department == "Inventory":
                status.update(label="路由到: Inventory Agent", state="running")
                agent_prompt = f"你是仓管员。根据以下结构化数据回答库存/价格问题：\n{db_data}"
                active_tools = None
            else:
                status.update(label="路由到: Sales Agent", state="running")
                agent_prompt = f"""
                你是一个顶级电商导购专家，请遵循以下规则：

                1. 必须基于商品库推荐具体商品
                2. 优先推荐性价比高的产品
                3. 回答要像真人销售（自然、有引导）
                4. 如果用户犹豫，要主动推荐2-3个选择
                5. 不允许编造商品（必须来自商品库）

                【商品库】
                {db_data}
                """
                active_tools = None

            # 3. 构造请求 Payload (仅携带最近 4 条历史防止 Token 超出)
            agent_messages = [{"role": "system", "content": agent_prompt}]
            for msg in st.session_state.messages[-4:]:
                agent_messages.append(msg)

            # 4. 执行 Agent 调用
            ai_msg_obj = call_department_agent(agent_messages, ALIYUN_API_KEY, active_tools)
            status.update(label="请求完成", state="complete")

            # 5. 处理响应机制 (Function Calling vs 文本输出)
            if ai_msg_obj.get("tool_calls"):  # <--- 换成最安全的 .get() 方法
                tool_call = ai_msg_obj.get("tool_calls")[0]
                if tool_call["function"]["name"] == "create_order":
                    arguments = json.loads(tool_call["function"]["arguments"])
                    render_checkout_card(arguments["product_name"], arguments["price"])
                    ai_reply = f"已为您生成【{arguments['product_name']}】的结算单，请核对。"
                    st.markdown(ai_reply)
            else:
                ai_reply = ai_msg_obj.get("content", "")  # <--- 这里也换成安全的 .get()
                st.markdown(ai_reply)

        # 落盘与状态更新
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        save_chat(st.session_state.session_id, "assistant", ai_reply)