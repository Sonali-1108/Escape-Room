
from flask import Flask, render_template, request, redirect, url_for
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


@app.route("/book", methods=["GET", "POST"])
def create_booking():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone_number", "").strip()
            room_id = request.form.get("room_id", "").strip()
            booking_date = request.form.get("booking_date", "").strip()
            time_slot = request.form.get("time_slot", "").strip()

            try:
                group_size = int(request.form.get("group_size", "0"))
                room_id = int(room_id)
            except ValueError:
                return "Please enter a valid room and group size.", 400

            if not all([first_name, last_name, email, phone,
                        booking_date, time_slot]):
                return "Please fill in every field.", 400

            if group_size < 1:
                return "Group size must be at least 1.", 400

            cursor.execute(
                "SELECT capacity FROM Room WHERE room_id = ?",
                (room_id,)
            )
            room = cursor.fetchone()

            if room is None:
                return "Please select a valid room.", 400

            if group_size > room["capacity"]:
                return "Group size exceeds this room's capacity.", 400

            cursor.execute(
                "SELECT customer_id FROM Customer WHERE email = ? LIMIT 1",
                (email,)
            )
            customer = cursor.fetchone()

            if customer:
                customer_id = customer["customer_id"]
            else:
                cursor.execute("""
                    INSERT INTO Customer
                    (first_name, last_name, email, phone_number)
                    VALUES (?, ?, ?, ?)
                """, (first_name, last_name, email, phone))
                customer_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Booking
                (customer_id, room_id, booking_date, time_slot,
                 group_size, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id, room_id, booking_date,
                time_slot, group_size, "Confirmed"
            ))

            connection.commit()
            return redirect(url_for("home"))

        cursor.execute("""
            SELECT room_id, room_name, capacity, price_per_person
            FROM Room
            ORDER BY room_id
        """)
        rooms = cursor.fetchall()

        return render_template("booking.html", rooms=rooms)

    except sqlite3.Error:
        connection.rollback()
        return "A database error occurred. Please check your database.", 500

    finally:
        connection.close()

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
