
from flask import Flask, render_template, request
import sqlite3
import os
from datetime import date

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escape room.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_db_objects():
    """Safely create the DBMS view, audit table and trigger."""
    if not os.path.exists(DB_PATH):
        return

    connection = get_connection()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('Booking', 'Customer', 'Room')
        """)
        existing = {row["name"] for row in cursor.fetchall()}

        if not {"Booking", "Customer", "Room"}.issubset(existing):
            return

        cursor.execute("""
            CREATE VIEW IF NOT EXISTS BookingDetails AS
            SELECT
                B.booking_id,
                C.first_name,
                C.last_name,
                R.room_name,
                B.booking_date,
                B.time_slot,
                B.status
            FROM Booking B
            JOIN Customer C ON B.customer_id = C.customer_id
            JOIN Room R ON B.room_id = R.room_id
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BookingAudit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                action TEXT,
                action_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS AfterBookingInsert
            AFTER INSERT ON Booking
            BEGIN
                INSERT INTO BookingAudit (booking_id, action)
                VALUES (NEW.booking_id, 'New booking created');
            END
        """)

        connection.commit()

    except sqlite3.Error as error:
        connection.rollback()
        print("DBMS initialization error:", error)
    finally:
        connection.close()


initialize_db_objects()


def get_dashboard_data():
    data = {
        "error": None,
        "tables": [],
        "analytics": {
            "total_bookings": 0,
            "confirmed_bookings": 0,
            "total_customers": 0,
            "total_rooms": 0,
            "paid_revenue": 0
        }
    }

    if not os.path.exists(DB_PATH):
        data["error"] = (
            "Database file not found. "
            "Place escape room.db beside app.py."
        )
        return data

    connection = get_connection()

    try:
        cursor = connection.cursor()

        queries = {
            "total_bookings": "SELECT COUNT(*) FROM Booking",
            "confirmed_bookings": (
                "SELECT COUNT(*) FROM Booking WHERE status = 'Confirmed'"
            ),
            "total_customers": "SELECT COUNT(*) FROM Customer",
            "total_rooms": "SELECT COUNT(*) FROM Room",
            "paid_revenue": (
                "SELECT COALESCE(SUM(amount), 0) FROM Payment "
                "WHERE payment_status = 'Paid'"
            )
        }

        for key, query in queries.items():
            try:
                cursor.execute(query)
                data["analytics"][key] = cursor.fetchone()[0]
            except sqlite3.Error as error:
                print(f"Analytics query {key} failed:", error)

        cursor.execute("""
            SELECT name, type
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        for item in cursor.fetchall():
            name = item["name"]
            safe_name = '"' + name.replace('"', '""') + '"'

            cursor.execute(f"SELECT COUNT(*) FROM {safe_name}")
            row_count = cursor.fetchone()[0]

            cursor.execute(f"PRAGMA table_info({safe_name})")
            columns = cursor.fetchall()

            data["tables"].append({
                "name": name,
                "rows": row_count,
                "columns": [column["name"] for column in columns]
            })

    except sqlite3.Error as error:
        data["error"] = f"Database error: {error}"
        print("Dashboard error:", error)

    finally:
        connection.close()

    return data


@app.route("/")
def dashboard():
    data = get_dashboard_data()
    return render_template("index.html", data=data)


@app.route("/book", methods=["GET"])
def book_page():
    if not os.path.exists(DB_PATH):
        return "Database file not found.", 500

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT room_id, room_name, price_per_person
            FROM Room ORDER BY room_id
        """)
        rooms = cursor.fetchall()

        return render_template(
            "booking.html",
            rooms=rooms,
            error=None,
            success=None
        )
    except sqlite3.Error as error:
        return f"Could not load rooms: {error}", 500
    finally:
        connection.close()


@app.route("/create_booking", methods=["POST"])
def create_booking():
    if not os.path.exists(DB_PATH):
        return "Database file not found.", 500

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone_number", "").strip()
    booking_date = request.form.get("booking_date", "").strip()
    time_slot = request.form.get("time_slot", "").strip()

    try:
        room_id = int(request.form.get("room_id", ""))
        group_size = int(request.form.get("group_size", ""))
    except (TypeError, ValueError):
        return "Enter a valid room and group size.", 400

    if not all([
        first_name, last_name, email, phone,
        booking_date, time_slot
    ]):
        return "Please complete all booking fields.", 400

    if group_size < 1:
        return "Number of people must be at least 1.", 400

    try:
        date.fromisoformat(booking_date)
    except ValueError:
        return "Enter a valid booking date.", 400

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT room_id, capacity FROM Room WHERE room_id = ?",
            (room_id,)
        )
        room = cursor.fetchone()

        if room is None:
            return "Selected room was not found.", 404

        if group_size > room["capacity"]:
            return (
                f"This room can accommodate at most "
                f"{room['capacity']} people."
            ), 400

        cursor.execute(
            "SELECT customer_id FROM Customer WHERE email = ?",
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
                (customer_id, room_id, booking_date,
                 time_slot, group_size, status)
            VALUES (?, ?, ?, ?, ?, 'Confirmed')
        """, (
            customer_id, room_id, booking_date,
            time_slot, group_size
        ))

        booking_id = cursor.lastrowid
        connection.commit()

        cursor.execute("""
            SELECT room_id, room_name, price_per_person
            FROM Room ORDER BY room_id
        """)
        rooms = cursor.fetchall()

        return render_template(
            "booking.html",
            rooms=rooms,
            error=None,
            success=f"Booking confirmed! Your Booking ID is {booking_id}."
        )

    except sqlite3.Error as error:
        connection.rollback()
        print("Booking error:", error)
        return "Unable to create booking. Please check the database.", 500

    finally:
        connection.close()


@app.route("/payment", methods=["GET", "POST"])
def payment_page():
    if not os.path.exists(DB_PATH):
        return "Database file not found.", 500

    if request.method == "GET":
        return render_template("payment.html", booking_id="")

    try:
        booking_id = int(request.form.get("booking_id", ""))
    except (TypeError, ValueError):
        return "Enter a valid booking ID.", 400

    payment_method = request.form.get("payment_method", "").strip()

    if payment_method not in ("UPI", "Card", "Cash"):
        return "Select a valid demo payment method.", 400

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT B.booking_id, B.group_size, R.price_per_person
            FROM Booking B
            JOIN Room R ON B.room_id = R.room_id
            WHERE B.booking_id = ?
        """, (booking_id,))

        booking = cursor.fetchone()

        if booking is None:
            return "Booking not found. Check the booking ID.", 404

        amount = booking["price_per_person"] * booking["group_size"]

        cursor.execute("""
            INSERT INTO Payment
                (booking_id, amount, payment_date,
                 payment_method, payment_status)
            VALUES (?, ?, DATE('now'), ?, 'Paid')
        """, (booking_id, amount, payment_method))

        connection.commit()

        return (
            f"<h2>Demo payment recorded successfully!</h2>"
            f"<p>Booking ID: {booking_id}</p>"
            f"<p>Amount: ₹{amount:.2f}</p>"
            f"<p>Method: {payment_method}</p>"
            f"<p>No real money was charged.</p>"
            f"<a href='/'>Back to Dashboard</a>"
        )

    except sqlite3.Error as error:
        connection.rollback()
        print("Payment error:", error)
        return "Unable to record payment. Please check the database.", 500

    finally:
        connection.close()


@app.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    if not os.path.exists(DB_PATH):
        return "Database file not found.", 500

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comments TEXT,
                feedback_date DATE DEFAULT (DATE('now')),
                FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
            )
        """)
        connection.commit()

        if request.method == "GET":
            return render_template("feedback.html")

        try:
            booking_id = int(request.form.get("booking_id", ""))
            rating = int(request.form.get("rating", ""))
        except (TypeError, ValueError):
            return "Enter a valid booking ID and rating.", 400

        comments = request.form.get("comments", "").strip()

        if not 1 <= rating <= 5:
            return "Rating must be between 1 and 5.", 400

        cursor.execute(
            "SELECT booking_id FROM Booking WHERE booking_id = ?",
            (booking_id,)
        )

        if cursor.fetchone() is None:
            return "Booking not found. Please check the booking ID.", 404

        cursor.execute("""
            INSERT INTO Feedback (booking_id, rating, comments)
            VALUES (?, ?, ?)
        """, (booking_id, rating, comments))

        connection.commit()

        return (
            "<h2>Thank you for your feedback!</h2>"
            "<a href='/'>Back to Dashboard</a>"
        )

    except sqlite3.Error as error:
        connection.rollback()
        print("Feedback error:", error)
        return "Unable to save feedback. Please check the database.", 500

    finally:
        connection.close()


@app.route("/table/<table_name>")
def view_table(table_name):
    allowed_tables = {
        "Booking", "Customer", "Payment", "Room", "Staff",
        "BookingDetails", "BookingAudit", "Feedback"
    }

    if table_name not in allowed_tables:
        return "Table not found.", 404

    if not os.path.exists(DB_PATH):
        return "Database file not found.", 500

    connection = get_connection()

    try:
        cursor = connection.cursor()
        safe_name = '"' + table_name.replace('"', '""') + '"'
        cursor.execute(f"SELECT * FROM {safe_name} LIMIT 100")

        columns = [item["name"] for item in cursor.description]
        records = [dict(row) for row in cursor.fetchall()]

        return render_template(
            "table.html",
            table_name=table_name,
            columns=columns,
            records=records
        )

    except sqlite3.Error as error:
        print("Table view error:", error)
        return f"Unable to display this table: {error}", 500

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
