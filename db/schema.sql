-- schema.sql
CREATE DATABASE IF NOT EXISTS university_db;
USE university_db;


-- users table for authentication demos
CREATE TABLE IF NOT EXISTS users (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(100) UNIQUE NOT NULL,
password VARCHAR(255) NOT NULL,
role VARCHAR(20) NOT NULL,
department VARCHAR(50) DEFAULT NULL
);


-- students table for ABAC / sensitive data
CREATE TABLE IF NOT EXISTS students (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(100),
department VARCHAR(50),
grade VARBINARY(255) -- stored encrypted in secure demo
);


-- comments table for XSS demo
CREATE TABLE IF NOT EXISTS comments (
id INT AUTO_INCREMENT PRIMARY KEY,
comment TEXT
);

-- seed.sql
USE university_db;


-- insert demo users (passwords are plaintext for demo simplicity; in real apps hash them)
INSERT IGNORE INTO users (username, password, role, department) VALUES
('admin','admin123','admin',NULL),
('alice','alice123','faculty','CSE'),
('bob','bob123','student','CSE');


-- insert students
INSERT IGNORE INTO students (name, department, grade) VALUES
('Rohan','CSE', 'A'),
('Meera','IT','B'),
('Aman','CSE','A'),
('Priya','ECE','C');


-- sample comment
INSERT IGNORE INTO comments (comment) VALUES
('<script>alert("XSS")</script>');