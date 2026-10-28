PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Staff;
DROP TABLE IF EXISTS Room;
DROP TABLE IF EXISTS Customer;

-- 1. CUSTOMER
CREATE TABLE Customer (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    phone_number VARCHAR(15)
);

INSERT INTO Customer VALUES
(1, 'Aarav', 'Sharma', 'aarav@gmail.com', '9876543210'),
(2, 'Ananya', 'Reddy', 'ananya@gmail.com', '9876543211'),
(3, 'Rohan', 'Patil', 'rohan@gmail.com', '9876543212'),
(4, 'Priya', 'Verma', 'priya@gmail.com', '9876543213'),
(5, 'Ishaan', 'Mehta', 'ishaan@gmail.com', '9876543214'),
(6, 'Sneha', 'Rao', 'sneha@gmail.com', '9876543215'),
(7, 'Kabir', 'Joshi', 'kabir@gmail.com', '9876543216');

-- 2. ROOM
CREATE TABLE Room (
    room_id INTEGER PRIMARY KEY,
    room_name VARCHAR(100),
    theme VARCHAR(50),
    capacity INTEGER,
    price_per_person REAL,
    difficulty_level VARCHAR(20)
);

INSERT INTO Room VALUES
(101, 'Mystery Mansion', 'Horror', 6, 500.00, 'Hard'),
(102, 'Lost Temple', 'Adventure', 8, 400.00, 'Medium'),
(103, 'Space Escape', 'Science Fiction', 5, 600.00, 'Easy'),
(104, 'Haunted Hospital', 'Horror', 7, 550.00, 'Hard'),
(105, 'Detective Case', 'Mystery', 6, 450.00, 'Medium'),
(106, 'Jungle Quest', 'Adventure', 8, 350.00, 'Easy'),
(107, 'Time Machine', 'Sci-Fi', 5, 650.00, 'Hard');

-- 3. BOOKING
CREATE TABLE Booking (
    booking_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    booking_date DATE,
    time_slot VARCHAR(30),
    group_size INTEGER,
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
);

INSERT INTO Booking VALUES
(1001, 1, 101, '2026-10-20', '10:00 AM', 4, 'Confirmed'),
(1002, 2, 102, '2026-10-21', '02:00 PM', 6, 'Pending'),
(1003, 3, 103, '2026-10-22', '04:00 PM', 3, 'Confirmed'),
(1004, 4, 104, '2026-10-23', '11:00 AM', 5, 'Confirmed'),
(1005, 5, 105, '2026-10-24', '03:00 PM', 4, 'Cancelled'),
(1006, 6, 106, '2026-10-25', '01:00 PM', 7, 'Pending'),
(1007, 7, 107, '2026-10-26', '05:00 PM', 5, 'Confirmed');

-- 4. STAFF
CREATE TABLE Staff (
    staff_id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(50),
    email VARCHAR(100),
    phone_number VARCHAR(15),
    assigned_room_id INTEGER,
    FOREIGN KEY (assigned_room_id) REFERENCES Room(room_id)
);

INSERT INTO Staff VALUES
(201, 'Priya Rao', 'Manager', 'priya.staff@gmail.com', '9876500001', 101),
(202, 'Karan Das', 'Game Master', 'karan@gmail.com', '9876500002', 102),
(203, 'Meera Shah', 'Assistant', 'meera@gmail.com', '9876500003', 103),
(204, 'Rahul Nair', 'Game Master', 'rahul@gmail.com', '9876500004', 104),
(205, 'Neha Singh', 'Receptionist', 'neha@gmail.com', '9876500005', 105),
(206, 'Arjun Rao', 'Technician', 'arjun@gmail.com', '9876500006', 106),
(207, 'Diya Kapoor', 'Assistant', 'diya@gmail.com', '9876500007', 107);

-- 5. PAYMENT
CREATE TABLE Payment (
    payment_id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL,
    amount REAL,
    payment_date DATE,
    payment_method VARCHAR(30),
    payment_status VARCHAR(20),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
);

INSERT INTO Payment VALUES
(301, 1001, 2000.00, '2026-10-20', 'UPI', 'Paid'),
(302, 1002, 2400.00, '2026-10-21', 'Card', 'Pending'),
(303, 1003, 1800.00, '2026-10-22', 'Cash', 'Paid'),
(304, 1004, 2750.00, '2026-10-23', 'UPI', 'Paid'),
(305, 1005, 1800.00, '2026-10-24', 'Card', 'Refunded'),
(306, 1006, 2450.00, '2026-10-25', 'Cash', 'Pending'),
(307, 1007, 3250.00, '2026-10-26', 'UPI', 'Paid');

-- VERIFY ALL TABLES
SELECT * FROM Customer;
SELECT * FROM Room;
SELECT * FROM Booking;
SELECT * FROM Staff;
SELECT * FROM Payment;
CREATE VIEW BookingDetails AS
SELECT
    B.booking_id,
    C.first_name,
    C.last_name,
    R.room_name,
    B.booking_date,
    B.time_slot,
    B.status
FROM Booking B
JOIN Customer C
    ON B.customer_id = C.customer_id
JOIN Room R
    ON B.room_id = R.room_id;
CREATE TABLE BookingAudit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER,
    action TEXT,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER AfterBookingInsert
AFTER INSERT ON Booking
BEGIN
    INSERT INTO BookingAudit (booking_id, action)
    VALUES (NEW.booking_id, 'New booking created');
END;