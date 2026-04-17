import sqlite3

DB_PATH = 'shop.db'

def init_db():
    """初始化 SQLite 数据库及测试 Mock 数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # DDL: 创建商品表
    cursor.execute('''CREATE TABLE IF NOT EXISTS t_product(
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, category TEXT NOT NULL,
            price REAL NOT NULL, stock INTEGER NOT NULL DEFAULT 0, tags TEXT, description TEXT, status INTEGER NOT NULL DEFAULT 1)''')

    # DDL: 创建聊天会话日志表
    cursor.execute('''CREATE TABLE IF NOT EXISTS t_chat_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL,
            content TEXT NOT NULL, create_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # 插入基础测试数据
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

def fetch_products():
    """获取所有上架商品信息，用于注入 RAG Prompt"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price, stock, tags, description FROM t_product WHERE status = 1")
    results = cursor.fetchall()
    conn.close()

    if not results:
        return "当前店铺没有上架任何商品。"
    return "\n".join([f"【{row['product_name']}】 - 售价: {row['price']}元 | 库存: {row['stock']}件。" for row in results])

def save_chat(session_id, role, content):
    """异步/后台落盘聊天记录 (TODO: 生产环境需改为连接池或异步队列)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO t_chat_log (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, str(content)))
        conn.commit()
        conn.close()
    except Exception as e:
        # 记录 log，避免阻断主流程
        pass