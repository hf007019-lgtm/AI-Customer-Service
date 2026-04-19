import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_connection():
    print("🔄 正在尝试通过 MCP 协议连接数据库服务器...")

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    # 2. 建立标准的 stdio 通信管道
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 握手初始化
            await session.initialize()
            print("✅ 连接成功！正在向服务器发送 '查询库存' 的协议指令...\n")

            result = await session.call_tool("get_in_stock_products", arguments={})

            # 打印服务器返回的结果
            print("📦 服务器返回的数据如下：")
            print("-" * 30)
            # 解析并打印纯文本结果
            print(result.content[0].text)
            print("-" * 30)


if __name__ == "__main__":
    # 运行异步客户端
    asyncio.run(test_mcp_connection())