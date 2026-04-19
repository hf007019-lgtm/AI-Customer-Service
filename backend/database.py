import os
import sqlite3

# 获取当前 database.py 所在的 backend 目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 拼接出 ../data/shop.db 的绝对路径，再也不会乱跑了！
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'shop.db')

def get_db_connection():
    """获取数据库连接并设置 row_factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化 DDL 与基础 Mock 数据"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # 创建商品表
        cursor.execute('''CREATE TABLE IF NOT EXISTS t_product(
                id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, category TEXT NOT NULL,
                price REAL NOT NULL, stock INTEGER NOT NULL DEFAULT 0, tags TEXT, description TEXT, status INTEGER NOT NULL DEFAULT 1)''')
        # 创建聊天记录表
        cursor.execute('''CREATE TABLE IF NOT EXISTS t_chat_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL, create_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        # 预填充商品
        cursor.execute("SELECT COUNT(*) FROM t_product")
        if cursor.fetchone()[0] == 0:
            products = [
                ('雷蛇黑寡妇机械键盘', '数码外设', 699.0, 150, '电竞,RGB', '机械轴体，手感干脆。'),
                ('罗技 MX Master 3S', '数码外设', 599.0, 200, '办公,静音', '人体工学设计，程序员首选。'),
                ('Sony WH-1000XM5', '影音娱乐', 1999.0, 50, '降噪', '行业顶尖降噪效果。')
            ]
            cursor.executemany('INSERT INTO t_product (product_name, category, price, stock, tags, description) VALUES (?, ?, ?, ?, ?, ?)', products)
        conn.commit()

def fetch_products():
    """获取在售商品列表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, price, stock FROM t_product WHERE status = 1")
            rows = cursor.fetchall()
            return "\n".join([f"【{r['product_name']}】 价格: {r['price']}元 | 库存: {r['stock']}件" for r in rows])
    except sqlite3.Error:
        return "数据库暂不可用"

def save_chat(session_id, role, content):
    """持久化聊天日志"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO t_chat_log (session_id, role, content) VALUES (?, ?, ?)",
                           (session_id, role, str(content)))
            conn.commit()
    except Exception:
        pass