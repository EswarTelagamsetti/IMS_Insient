CREATE DATABASE IF NOT EXISTS ims_insient;
USE ims_insient;

-- Branches Table
CREATE TABLE branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'employee', 'intern') NOT NULL,
    branch_id INT,
    work_type ENUM('office', 'remote') DEFAULT 'office',
    experience_start_date DATE,
    tickets_solved INT DEFAULT 0,
    is_available BOOLEAN DEFAULT FALSE,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL
);

-- Tickets Table
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    raised_by INT NOT NULL,
    assigned_to INT NOT NULL,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (raised_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE CASCADE
);

-- Add leave applications table
CREATE TABLE leave_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewed_by INT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Add activity logs table
CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    status BOOLEAN NOT NULL, -- TRUE = available, FALSE = unavailable
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Insert default admin
INSERT INTO users (name, email, password, role) VALUES 
('Admin', 'admin@insient.com', 'admin123', 'admin');


-- Disable safe update mode temporarily and update interns availability
SET SQL_SAFE_UPDATES = 0;
UPDATE users SET is_available = TRUE WHERE role = 'intern';
SET SQL_SAFE_UPDATES = 1;


-- Add notification columns to leave_applications table
ALTER TABLE leave_applications 
ADD COLUMN admin_notification_read BOOLEAN DEFAULT FALSE,
ADD COLUMN employee_notification_read BOOLEAN DEFAULT TRUE;

-- Disable safe update mode temporarily
SET SQL_SAFE_UPDATES = 0;

-- Update existing records
UPDATE leave_applications 
SET admin_notification_read = TRUE, 
    employee_notification_read = TRUE 
WHERE status != 'pending';

UPDATE leave_applications 
SET admin_notification_read = FALSE 
WHERE status = 'pending';

-- Re-enable safe update mode
SET SQL_SAFE_UPDATES = 1;