CREATE TABLE `Customer` (
  `customer_id` integer PRIMARY KEY AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `phone_number` varchar(15)
);

CREATE TABLE `Room` (
  `room_id` integer PRIMARY KEY AUTO_INCREMENT,
  `room_name` varchar(100) NOT NULL,
  `theme` varchar(50),
  `capacity` integer,
  `price_per_person` real,
  `difficulty_level` varchar(20)
);

CREATE TABLE `Staff` (
  `staff_id` integer PRIMARY KEY AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `role` varchar(50),
  `email` varchar(100) UNIQUE NOT NULL,
  `phone_number` varchar(15)
);

CREATE TABLE `Booking` (
  `booking_id` integer PRIMARY KEY AUTO_INCREMENT,
  `customer_id` integer NOT NULL,
  `room_id` integer NOT NULL,
  `staff_id` integer NOT NULL,
  `booking_date` date NOT NULL,
  `time_slot` varchar(20) NOT NULL,
  `num_players` integer NOT NULL,
  `total_amount` real NOT NULL,
  `status` varchar(20) DEFAULT 'Confirmed'
);

CREATE TABLE `Payment` (
  `payment_id` integer PRIMARY KEY AUTO_INCREMENT,
  `booking_id` integer NOT NULL,
  `payment_date` date NOT NULL,
  `amount` real NOT NULL,
  `payment_method` varchar(30) NOT NULL,
  `payment_status` varchar(20) DEFAULT 'Completed'
);

ALTER TABLE `Booking` ADD FOREIGN KEY (`customer_id`) REFERENCES `Customer` (`customer_id`);

ALTER TABLE `Booking` ADD FOREIGN KEY (`room_id`) REFERENCES `Room` (`room_id`);

ALTER TABLE `Booking` ADD FOREIGN KEY (`staff_id`) REFERENCES `Staff` (`staff_id`);

ALTER TABLE `Payment` ADD FOREIGN KEY (`booking_id`) REFERENCES `Booking` (`booking_id`);
