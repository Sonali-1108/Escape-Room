
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escape room.db")


def initialize_db_objects():
    """
    Safely create the DBMS view, audit table, and trigger.
    This does not drop or recreate any existing tables.
    """
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

        # Only create the view after its source tables exist.
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
                JOIN Customer AS C
                    ON B.customer_id = C.customer_id
                JOIN Room AS R
                    ON B.room_id = R.room_id
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
        # Keep the existing website available if database setup needs attention.
        print(f"Could not initialize DBMS view/trigger: {error}")
        connection.rollback()
    finally:
        connection.close()


# This also runs when deployed with a WSGI server such as Gunicorn.
initialize_db_objects()


def get_dashboard_data():
    if not os.path.exists(DB_PATH):
        return {"error": "Database file not found. Place your existing escape room.db beside app.py.", "tables": []}

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name, type FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY CASE type WHEN 'view' THEN 1 ELSE 0 END, name
            """)
