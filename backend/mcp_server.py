from mcp.server.fastmcp import FastMCP
import sqlite3

# 1. 初始化你的第一个 MCP 服务器
mcp = FastMCP("Shop-Database")


# 2. 核心魔法：使用 @mcp.tool() 装饰器
# 只要加上这一行，下面这个普通的 Python 函数，就会瞬间变成一个符合 MCP 标准的“全球通用 API”！
@mcp.tool()
def get_in_stock_products() -> str:
    """查询店铺所有在售商品、价格和库存信息。大模型会自动读取这段注释来理解工具用途。"""
    try:
        conn = sqlite3.connect('../data/shop.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, price, stock FROM t_product WHERE status = 1")
        results = cursor.fetchall()
        conn.close()

        if not results:
            return "当前店铺没有上架任何商品。"

        return "\n".join([f"【{row['product_name']}】 价格: {row['price']} 库存: {row['stock']}" for row in results])
    except Exception as e:
        return f"数据库查询失败: {e}"


# 3. 启动监听
if __name__ == "__main__":
    mcp.run()