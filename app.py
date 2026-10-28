
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escape room.db")


def initialize_db_objects():
    """Create the DBMS view, audit table, and trigger without dropping tables."""
    if not os.path.exists(DB_PATH):
        return

    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('Booking', 'Customer', 'Room')
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}

        # Create these objects only when their source tables are available.
        if {"Booking", "Customer", "Room"}.issubset(existing_tables):
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
                FROM Booking AS B
                JOIN Customer AS C ON B.customer_id = C.customer_id
                JOIN Room AS R ON B.room_id = R.room_id
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
        # Do not prevent the website from starting if DB setup needs attention.
        print(f"Could not initialize DBMS view/trigger: {error}")
        connection.rollback()
    finally:
        connection.close()


# Runs for both local Flask and Render/Gunicorn deployments.
initialize_db_objects()



def get_dashboard_data():
    if not os.path.exists(DB_PATH):
        return {
            "error": "Database file not found.",
            "tables": [],
            "stats": {}
        }

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name, type FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = [
            {"name": row["name"], "type": row["type"]}
            for row in cursor.fetchall()
        ]

        stats = {}

        for table in ["Booking", "Customer", "Room", "Payment", "Staff"]:
            if any(item["name"] == table and item["type"] == "table"
                   for item in tables):
                safe_name = '"' + table.replace('"', '""') + '"'
                cursor.execute(f"SELECT COUNT(*) FROM {safe_name}")
                stats[table] = cursor.fetchone()[0]
            else:
                stats[table] = 0

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM Booking
                WHERE status = 'Confirmed'
            """)
            stats["Confirmed"] = cursor.fetchone()[0]
        except sqlite3.Error:
            stats["Confirmed"] = 0

        try:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM Payment
                WHERE payment_status = 'Paid'
            """)
            stats["Revenue"] = cursor.fetchone()[0]
        except sqlite3.Error:
            stats["Revenue"] = 0

        return {
            "tables": tables,
            "stats": stats,
            "error": None
        }

    except sqlite3.Error as error:
        return {
            "tables": [],
            "stats": {},
            "error": str(error)
        }
    finally:
        connection.close()



@app.route("/")
def dashboard():
    data = get_dashboard_data()
    return render_template("index.html", data=data)



@app.route("/table/<table_name>")
def view_table(table_name):
    allowed_tables = [
        "Booking", "Customer", "Payment", "Room", "Staff",
        "BookingDetails", "BookingAudit"
    ]

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
    except sqlite3.Error as error:
        return f"Database error: {error}", 500
    finally:
        connection.close()


@app.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

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

        if request.method == "POST":
            try:
                booking_id = int(request.form.get("booking_id", ""))
                rating = int(request.form.get("rating", ""))
            except ValueError:
                return "Enter a valid booking ID and rating.", 400

            comments = request.form.get("comments", "").strip()

            if not 1 <= rating <= 5:
                return "Rating must be between 1 and 5.", 400

            cursor.execute(
                "SELECT booking_id FROM Booking WHERE booking_id = ?",
                (booking_id,)
            )
            if cursor.fetchone() is None:
                return "Booking not found.", 404

            cursor.execute("""
                INSERT INTO Feedback (booking_id, rating, comments)
                VALUES (?, ?, ?)
            """, (booking_id, rating, comments))

            connection.commit()
            return "Thank you for your feedback! <a href='/'>Back to Dashboard</a>"

        return render_template("feedback.html")

    except sqlite3.Error as error:
        connection.rollback()
        return f"Database error: {error}", 500
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
