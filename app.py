import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import date

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            quantity INTEGER,
            sales_date TEXT
        )
"""
    )
    conn.commit()
    conn.close()


init_db()


def get_connection():
    """products.dbに接続してconnectionを返す。"""
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_sales_history(cursor):
    """売上履歴を新しいものから１０件取得する"""
    cursor.execute(
        """
                SELECT sales.*, products.name
                FROM sales
                JOIN products
                ON sales.product_id = products.product_id
                ORDER BY sales_date DESC
                LIMIT 10
                """
    )
    return cursor.fetchall()


def get_products(cursor, keyword, order_by):
    """商品一覧を取得する。keywordがある場合は部分一致検索し、order_byで並び替える。"""
    if keyword:
        cursor.execute(
            f"SELECT * FROM products WHERE name LIKE ? ORDER BY {order_by}",
            ("%" + keyword + "%",),
        )
    else:
        cursor.execute(f"SELECT * FROM products ORDER BY {order_by}")
    return cursor.fetchall()


def get_sales_summary(cursor):
    """商品ごとの売上回数を集計して取得"""
    cursor.execute(
        """
        SELECT products.name, COUNT(*) AS total_sales
        FROM sales
        JOIN products
        ON sales.product_id = products.product_id
        GROUP BY products.name
        ORDER BY total_sales DESC           
        """
    )
    return cursor.fetchall()


def get_total_sales(cursor):
    """総売上金額を取得する。"""
    cursor.execute(
        """
        SELECT SUM(products.price)
        FROM sales
        JOIN products
        ON sales.product_id = products.product_id

"""
    )
    return cursor.fetchone()


def get_daily_sales(cursor, start_date, end_date):
    """期限指定があればその範囲の日別売上を集計して取得"""
    if start_date and end_date:
        cursor.execute(
            """
            SELECT sales.sales_date, SUM(products.price) AS daily_total
            FROM sales
            JOIN products
            ON sales.product_id = products.product_id
            WHERE sales.sales_date BETWEEN ? AND ?
            GROUP BY sales.sales_date
            ORDER BY sales.sales_date ASC
            """,
            (start_date, end_date),
        )
    else:
        cursor.execute(
            """
            SELECT sales.sales_date, SUM(products.price) AS daily_total
            FROM sales
            JOIN products
            ON sales.product_id = products.product_id
            GROUP BY sales.sales_date
            ORDER BY sales.sales_date ASC
            """
        )
    return cursor.fetchall()


@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    sort = request.args.get("sort", "stock")

    conn = get_connection()
    cursor = conn.cursor()
    if sort == "price":
        order_by = "price DESC"
    else:
        order_by = "stock DESC"
    products = get_products(cursor, keyword, order_by)
    sales = get_sales_history(cursor)
    sales_summary = get_sales_summary(cursor)
    total_sales = get_total_sales(cursor)
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    daily_sales = get_daily_sales(cursor, start_date, end_date)

    conn.close()

    return render_template(
        "index.html",
        products=products,
        keyword=keyword,
        sales=sales,
        sales_summary=sales_summary,
        total_sales=total_sales,
        daily_sales=daily_sales,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/add", methods=["POST"])
def add_product():
    product_id = request.form["product_id"]
    name = request.form["name"]
    price = int(request.form["price"])
    stock = int(request.form["stock"])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO products (product_id, name, price, stock)
            VALUES (?, ?, ?, ?)
        """,
            (product_id, name, price, stock),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        conn.close()
        return render_template(
            "index.html", products=products, error="IDが重複しています"
        )

    conn.close()
    return redirect(url_for("index"))


@app.route("/delete", methods=["POST"])
def delete_product():
    product_id = request.form["product_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/sell", methods=["POST"])
def sell_product():
    product_id = request.form["product_id"]
    quantity = 1
    d = date.today()
    sales_date = d.strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET stock = stock - 1
        WHERE product_id = ? AND stock > 0
    """,
        (product_id,),
    )
    if cursor.rowcount == 1:
        cursor.execute(
            """
            INSERT INTO sales(product_id, quantity,sales_date)
            VALUES (?,?,?)""",
            (product_id, quantity, sales_date),
        )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/edit/<product_id>")
def edit_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return render_template("edit.html", product=product)


@app.route("/update", methods=["POST"])
def update_product():
    product_id = request.form["product_id"]
    name = request.form["name"]
    price = int(request.form["price"])
    stock = int(request.form["stock"])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET name = ?, price = ?, stock = ?
        WHERE product_id = ?
    """,
        (name, price, stock, product_id),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/restock", methods=["POST"])
def restock_product():
    product_id = request.form["product_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET stock = stock + 1
        WHERE product_id = ?
        """,
        (product_id,),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
