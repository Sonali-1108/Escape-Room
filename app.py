
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escape room.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_dashboard_data():
    if not os.path.exists(DB_PATH):
        return {
            "error": "Database file not found. Place your existing escape room.db beside app.py.",
            "tables": []
        }

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
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
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM Booking")
            total_bookings = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM Booking
                WHERE status = 'Confirmed'
            """)
            confirmed_bookings = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Customer")
            total_customers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Room")
            total_rooms = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM Payment
                WHERE payment_status = 'Paid'
            """)
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
    connection = get_connection()

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

            if not all([
                first_name, last_name, email, phone,
                booking_date, time_slot
            ]):
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

            cursor.execute("""
                SELECT customer_id
                FROM Customer
                WHERE email = ?
                LIMIT 1
            """, (email,))
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


@app.route("/payment", methods=["GET", "POST"])
def payment_page():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        if request.method == "POST":
            booking_id = request.form.get("booking_id", "").strip()
            payment_method = request.form.get("payment_method", "").strip()

            if payment_method not in ["UPI", "Card", "Cash"]:
                return "Invalid demo payment method.", 400

            try:
                booking_id = int(booking_id)
            except ValueError:
                return "Invalid booking ID.", 400

            cursor.execute("""
                SELECT booking_id, group_size, room_id
                FROM Booking
                WHERE booking_id = ?
            """, (booking_id,))
            booking = cursor.fetchone()

            if booking is None:
                return "Booking not found.", 404

            cursor.execute("""
                SELECT price_per_person
                FROM Room
                WHERE room_id = ?
            """, (booking["room_id"],))
            room = cursor.fetchone()

            if room is None:
                return "Room not found.", 404

            amount = room["price_per_person"] * booking["group_size"]

            cursor.execute("""
                INSERT INTO Payment
                (booking_id, amount, payment_date,
                 payment_method, payment_status)
                VALUES (?, ?, DATE('now'), ?, 'Paid')
            """, (booking_id, amount, payment_method))

            connection.commit()

            return f"""
                <h2>Demo Payment Recorded!</h2>
                <p>Booking ID: {booking_id}</p>
                <p>Amount: ₹{amount:.2f}</p>
                <p>No real money was charged.</p>
                <a href="/">Back to Dashboard</a>
            """

        return render_template("payment.html")

    except sqlite3.Error:
        connection.rollback()
        return "A database error occurred.", 500

    finally:
        connection.close()


@app.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    if request.method == "POST":
        booking_id = request.form.get("booking_id", "").strip()
        rating = request.form.get("rating", "").strip()
        comments = request.form.get("comments", "").strip()

        try:
            booking_id = int(booking_id)
            rating = int(rating)
        except ValueError:
            return "Enter a valid booking ID and rating.", 400

        if not 1 <= rating <= 5:
            return "Rating must be between 1 and 5.", 400

        # Validate the booking without creating a Feedback table.
        connection = get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT booking_id FROM Booking WHERE booking_id = ?",
                (booking_id,)
            )

            if cursor.fetchone() is None:
                return "Booking not found. Please check your booking ID.", 404

        except sqlite3.Error:
            return "Could not verify the booking.", 500

        finally:
            connection.close()

        # Demo only: feedback is not stored permanently.
        return f"""
            <h2>Thank You for Your Feedback! 💜</h2>
            <p>Your rating: {rating}/5</p>
            <p>Your feedback was received for this demonstration.</p>
            <p>Your comments have not been permanently saved.</p>
            <a href="/">Back to Dashboard</a>
        """

    return render_template("feedback.html")


@app.route("/application", methods=["GET", "POST"])
def application_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        position = request.form.get("position", "").strip()
        experience = request.form.get("experience", "").strip()
        availability = request.form.get("availability", "").strip()

        if not all([name, email, phone, position, availability]):
            return "Please fill in all required fields.", 400

        allowed_positions = [
            "Game Master",
            "Receptionist",
            "Operations Staff"
        ]

        allowed_availability = [
            "Weekdays",
            "Weekends",
            "Flexible"
        ]

        if position not in allowed_positions:
            return "Please select a valid position.", 400

        if availability not in allowed_availability:
            return "Please select a valid availability option.", 400

        # Demo only: no Job Application table is created.
        return """
            <h2>Application Submitted! 💜</h2>
            <p>Thank you for your interest in joining our team.</p>
            <p>This is a demonstration. Your application has not been saved.</p>
            <a href="/">Back to Dashboard</a>
        """

    return render_template("application.html")


@app.route("/table/<table_name>")
def view_table(table_name):
    allowed_tables = [
        "Booking",
        "Customer",
        "Payment",
        "Room",
        "Staff"
    ]

    if table_name not in allowed_tables:
        return "Table not found", 404

    connection = get_connection()

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

    except sqlite3.Error:
        return "Could not read this database table.", 500

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
