import sqlite3
import json

DB_NAME = "shop.db"


# ================= 初始化数据库 =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 商品表
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
    """)

    # 聊天记录
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT
    )
    """)

    # 订单表
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        price REAL
    )
    """)

    conn.commit()

    # 初始化一些商品（如果为空）
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("iPhone 15", 5999, 10),
            ("小米 14", 3999, 20),
            ("华为 Mate60", 6999, 5),
            ("AirPods", 999, 50)
        ]
        c.executemany("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", products)
        conn.commit()

    conn.close()


# ================= 获取商品 =================
def fetch_products():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT name, price, stock FROM products")
    rows = c.fetchall()

    conn.close()

    return json.dumps([
        {"name": r[0], "price": r[1], "stock": r[2]}
        for r in rows
    ], ensure_ascii=False)


# ================= 保存聊天 =================
def save_chat(session_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT INTO chats (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )

    conn.commit()
    conn.close()


# ================= 创建订单 =================
def create_order(product_name, price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT INTO orders (product_name, price) VALUES (?, ?)",
        (product_name, price)
    )

    conn.commit()
    conn.close()