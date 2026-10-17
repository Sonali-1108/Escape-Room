
from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escape room.db")


def get_dashboard_data():
    if not os.path.exists(DB_PATH):
        return {"error": "Database file not found. Place your existing escape room.db beside app.py.", "tables": []}

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = []

        for item in cursor.fetchall():
            table_name = item["name"]
            safe_name = '"' + table_name.replace('"', '""') + '"'

            cursor.execute(f"SELECT COUNT(*) FROM {safe_name}")
            row_count = cursor.fetchone()[0]

            cursor.execute(f"PRAGMA table_info({safe_name})")
            columns = [column["name"] for column in cursor.fetchall()]

            tables.append({
                "name": table_name,
                "rows": row_count,
                "columns": columns
            })

        return {"error": None, "tables": tables}

    finally:
        connection.close()



@app.route("/")
def home():
    data = get_dashboard_data()

    if not data["error"]:
        connection = sqlite3.connect(DB_PATH)
        try:
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM Booking")
            total_bookings = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM Booking WHERE status = 'Confirmed'"
            )
            confirmed_bookings = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Customer")
            total_customers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Room")
            total_rooms = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM Payment "
                "WHERE payment_status = 'Paid'"
            )
            paid_revenue = cursor.fetchone()[0]

            data["analytics"] = {
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed_bookings,
                "total_customers": total_customers,
                "total_rooms": total_rooms,
                "paid_revenue": paid_revenue
            }
        finally:
            connection.close()

    return render_template("index.html", data=data)

@app.route("/table/<table_name>")
def view_table(table_name):
    allowed_tables = ["Booking", "Customer", "Payment", "Room", "Staff"]

    if table_name not in allowed_tables:
        return "Table not found", 404

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        safe_name = '"' + table_name.replace('"', '""') + '"'
        cursor.execute(f"SELECT * FROM {safe_name} LIMIT 100")

        columns = [item[0] for item in cursor.description]
        records = [dict(row) for row in cursor.fetchall()]

        return render_template(
            "table.html",
            table_name=table_name,
            columns=columns,
            records=records
        )
    finally:
        connection.close()


if __name__ == "__main__":
   import os

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
