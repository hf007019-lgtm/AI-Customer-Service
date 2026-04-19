from dashscope import Generation, MultiModalConversation
import logging

# 注册下单工具
TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "用于生成订单。当用户确认购买特定商品时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "price": {"type": "number"}
            },
            "required": ["product_name", "price"]
        }
    }
}]

def get_router_intent(user_text, api_key):
    """分类意图：下单、查库存、导购"""
    prompt = "你是路由节点。请根据用户输入输出：【下单】、【查库存】或【导购】。"
    try:
        response = Generation.call(
            api_key=api_key,
            model="deepseek-v3",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_text}]
        )
        content = response.output.choices[0].message.content
        if "下单" in content: return "Checkout"
        if "查库存" in content: return "Inventory"
    except Exception as e:
        logging.error(f"Router API Error: {e}")
    return "Sales"

def call_department_agent(messages, api_key, active_tools=None):
    """通用业务 Agent 调用入口"""
    try:
        response = Generation.call(
            api_key=api_key,
            model="deepseek-v3",
            messages=messages,
            result_format="message",
            tools=active_tools
        )
        return response.output.choices[0].message
    except Exception as e:
        logging.error(f"Agent API Error: {e}")
        return {"content": "抱歉，系统通讯异常，请稍后再试。", "role": "assistant"}

def call_vision_agent(base64_image, db_data, api_key):
    """多模态图像识别分析"""
    try:
        msgs = [{"role": "user", "content": [
            {"image": base64_image},
            {"text": f"基于图片和商品库给出搭配建议：\n{db_data}"}
        ]}]
        response = MultiModalConversation.call(api_key=api_key, model='qwen-vl-max', messages=msgs)
        return response.output.choices[0].message.content[0]["text"]
    except Exception:
        return "视觉识别服务暂时不可用。"