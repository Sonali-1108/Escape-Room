# Escape Room Management System

## 📌 Project Overview

The **Escape Room Management System** is a web-based database management project designed to manage escape room operations. It provides a structured way to handle bookings, payments, feedback, and related information through a web interface backed by a database.

This project was developed as part of a college **Problem-Based Learning (PBL)** project for the Database Management Systems (DBMS) subject.

## 🎯 Objectives

- To design and implement a database for an escape room management system.
- To manage booking and payment information efficiently.
- To develop a user-friendly web interface.
- To organize and retrieve data using SQL queries.
- To understand the integration of a web application with a database.

## ✨ Features

- **Booking Management:** Handles escape room booking information.
- **Payment Management:** Provides a page for payment-related operations.
- **Feedback Management:** Includes a feedback interface.
- **Database Management:** Stores project data in a database.
- **Web Interface:** Uses HTML templates and CSS for the user interface.
- **SQL Queries:** Includes SQL files for database structure and queries.

## 🛠️ Technologies Used

- **Python** — Application logic
- **Flask** — Web application framework
- **HTML** — Web page structure
- **CSS** — Styling and layout
- **SQLite** — Database, if used by the application
- **SQL** — Database creation and queries
- **GitHub** — Version control and project hosting

## 📂 Project Structure

```text
escape-room-pbl/
│
├── app.py
├── escape room.db
├── escape-room.sql
├── query.sql
└── tables.html
├── escape-room.png
├── csv.txt
├── details.json
├── requirements.txt
├── README.md
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── booking.html
    ├── feedback.html
    ├── payment.html
    ├── table.html
    
```

## 📄 File Description

| File / Folder | Purpose |
|---|---|
| `app.py` | Main Python application file. |
| `escape room.db` | Database file, if this is the database used by the application. |
| `escape-room.sql` | SQL script for database setup or table creation. |
| `query.sql` | Contains SQL queries. |
| `escape-room.png` | Project image or database diagram. |
| `csv.txt` | Supporting text file; its exact purpose depends on its contents. |
| `details.json` | Stores structured data in JSON format. |
| `requirements.txt` | Lists Python dependencies. |
| `static/style.css` | Contains the website's CSS styles. |
| `templates/` | Contains the HTML templates used by the application. |

## 🗄️ Database Design

The project uses a database to organize and manage escape room information. The SQL files support database creation and querying.

The database design and its entities, attributes, primary keys, foreign keys, and relationships are documented in the project's ER diagram.

## 🚀 How to Run the Project

1. Clone or download this repository.
2. Install Python if it is not already installed.
3. Open a terminal in the project folder.
4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the Flask application:

   ```bash
   python app.py
   ```

6. Open the local URL displayed in the terminal in your web browser.

**Note:** The database file and configuration must be set up correctly for the application to run.

## 📚 Learning Outcomes

- Understanding relational database design.
- Working with SQL queries and database tables.
- Connecting a Python application to a database.
- Developing web pages using HTML and CSS.
- Understanding the integration of backend logic and frontend templates.

## 👥 Contributors

Developed as a college Problem-Based Learning (PBL) project for the DBMS subject.

## 📄 License

This project is intended for academic and educational purposes.

