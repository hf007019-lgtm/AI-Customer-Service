from dashscope import Generation, MultiModalConversation

# Function Calling 注册表
TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "当用户明确决定购买某件商品时，必须调用此函数来生成结算单。",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "要购买的商品全称"},
                "price": {"type": "number", "description": "商品单价"}
            },
            "required": ["product_name", "price"]
        }
    }
}]


def get_router_intent(user_text, api_key):
    """
    意图路由层 (Router Agent)
    根据用户输入内容判定下游链路
    """
    prompt = """你是智能路由节点。请严格分析用户意图并输出以下三个枚举值之一：
    【下单】（用户明确包含购买、下单、结算等交易意图）
    【查库存】（用户明确询问商品余量、特定价格等数据）
    【导购】（其他咨询、推荐请求或日常闲聊）"""

    response = Generation.call(
        api_key=api_key,
        model="deepseek-v3",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_text}]
    )
    intent = response.output.choices[0].message.content.strip()

    # 意图分发
    if "下单" in intent: return "Checkout"
    if "查库存" in intent: return "Inventory"
    return "Sales"


def call_department_agent(messages, api_key, active_tools=None):
    """通用大模型执行器，支持动态注入 System Prompt 和 Tools"""
    response = Generation.call(
        api_key=api_key,
        model="deepseek-v3",
        messages=messages,
        result_format="message",
        tools=active_tools
    )
    return response.output.choices[0].message


def call_vision_agent(base64_image, db_data, api_key):
    """调用 Qwen-VL 进行多模态图像识别"""
    vision_messages = [{"role": "user", "content": [
        {"image": base64_image},
        {"text": f"请分析图片，基于商品库给出推荐。\n\n【商品库】\n{db_data}"}
    ]}]
    response = MultiModalConversation.call(api_key=api_key, model='qwen-vl-max', messages=vision_messages)
    return response.output.choices[0].message.content[0]["text"]