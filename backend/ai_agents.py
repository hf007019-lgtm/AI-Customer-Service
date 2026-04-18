from dashscope import Generation, MultiModalConversation
import json

# ================= Function Calling =================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "当用户明确要购买商品时调用",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "商品名称"
                    },
                    "price": {
                        "type": "number",
                        "description": "商品价格"
                    }
                },
                "required": ["product_name", "price"]
            }
        }
    }
]


# ================= 🧠 意图识别（更稳定版本） =================
def get_router_intent(user_text, api_key):
    """
    Router Agent：判断用户意图
    """

    prompt = f"""
你是一个高精度意图识别系统，只允许输出以下三个词之一：

【下单】
【查库存】
【导购】

判断规则：
- 出现“买 / 下单 / 结算 / 我要这个” → 下单
- 出现“库存 / 多少钱 / 还有吗” → 查库存
- 其他全部 → 导购

用户输入：
{user_text}
"""

    response = Generation.call(
        api_key=api_key,
        model="deepseek-v3",
        messages=[
            {"role": "system", "content": prompt}
        ]
    )

    result = response.output.choices[0].message.content.strip()

    if "下单" in result:
        return "Checkout"
    elif "查库存" in result:
        return "Inventory"
    else:
        return "Sales"


# ================= 🤖 通用 Agent 调用 =================
def call_department_agent(messages, api_key, active_tools=None):
    """
    调用大模型（支持 function calling）
    """

    try:
        response = Generation.call(
            api_key=api_key,
            model="deepseek-v3",
            messages=messages,
            tools=active_tools,
            result_format="message"
        )

        msg = response.output.choices[0].message

        # 安全处理
        return {
            "content": msg.get("content", ""),
            "tool_calls": msg.get("tool_calls")
        }

    except Exception as e:
        return {
            "content": f"系统错误：{str(e)}",
            "tool_calls": None
        }


# ================= 🧠 Prompt增强策略 =================
def enhance_prompt_with_strategy(user_text):
    """
    根据用户意图增强提示词（让AI更像销售）
    """

    if any(word in user_text for word in ["推荐", "买什么", "哪个好"]):
        return "请推荐 2-3 个不同价位的商品，并说明区别"

    if "便宜" in user_text:
        return "优先推荐最便宜且性价比高的商品"

    if "贵一点" in user_text or "高端" in user_text:
        return "推荐高端产品，并强调品质和优势"

    return ""


# ================= 🖼 多模态（图像识别） =================
def call_vision_agent(base64_image, db_data, api_key):
    """
    调用视觉模型分析图片
    """

    messages = [
        {
            "role": "user",
            "content": [
                {"image": base64_image},
                {
                    "text": f"""
请分析图片中的商品，并结合商品库推荐类似商品：

商品库：
{db_data}
"""
                }
            ]
        }
    ]

    response = MultiModalConversation.call(
        api_key=api_key,
        model="qwen-vl-max",
        messages=messages
    )

    return response.output.choices[0].message.content[0]["text"]