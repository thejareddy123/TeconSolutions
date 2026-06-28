-- ============================================================
-- TraitSoftwares Database Schema
-- Run this SQL to create all tables
-- Usage: mysql -u root -p traitsoftwares_db < schema.sql
-- ============================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS teconsolutions_db;
USE teconsolutions_db;

-- ============================================================
-- TABLE: users
-- Stores all employees and admin users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Basic info
    employee_id VARCHAR(20) UNIQUE NOT NULL,    -- e.g., "EMP001"
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    
    -- Auth
    password_hash VARCHAR(255) NOT NULL,        -- bcrypt hashed password
    role ENUM('admin', 'manager', 'employee') DEFAULT 'employee',
    
    -- Employment details
    department VARCHAR(100),                    -- e.g., "Engineering"
    designation VARCHAR(100),                   -- e.g., "Software Developer"
    date_of_joining DATE,
    manager_id INT,                             -- Points to another user who is their manager
    
    -- Leave balance (in days)
    annual_leave_balance DECIMAL(5,2) DEFAULT 12.00,
    sick_leave_balance DECIMAL(5,2) DEFAULT 6.00,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,            -- Account locked after failed attempts
    failed_login_attempts INT DEFAULT 0,
    
    -- Profile
    profile_photo VARCHAR(255),                 -- Path to profile photo
    address TEXT,
    date_of_birth DATE,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME,
    
    -- Foreign key: manager_id references another user
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: tasks
-- Stores all tasks created in the system
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Who created this task
    created_by INT NOT NULL,
    
    -- Task details
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('todo', 'in_progress', 'review', 'completed', 'cancelled') DEFAULT 'todo',
    
    -- Dates
    start_date DATE,
    due_date DATE,
    completed_date DATE,
    
    -- Project this task belongs to (optional)
    project_name VARCHAR(255),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: task_assignments
-- Links tasks to employees (many-to-many)
-- One task can be assigned to many employees
-- ============================================================
CREATE TABLE IF NOT EXISTS task_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    assigned_by INT NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Make sure same task isn't assigned to same person twice
    UNIQUE KEY unique_task_user (task_id, user_id),
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: timesheets
-- Daily work log submitted by employees
-- ============================================================
CREATE TABLE IF NOT EXISTS timesheets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Work date
    work_date DATE NOT NULL,
    
    -- Hours worked
    hours_worked DECIMAL(4,2) NOT NULL,         -- e.g., 8.5 means 8 hours 30 mins
    
    -- What they worked on
    task_id INT,                                -- Optional: link to a specific task
    description TEXT NOT NULL,                 -- What work was done
    
    -- Status flow: draft -> submitted -> approved/rejected
    status ENUM('draft', 'submitted', 'approved', 'rejected') DEFAULT 'draft',
    
    -- Review
    reviewed_by INT,                            -- Manager who approved/rejected
    reviewed_at DATETIME,
    review_notes TEXT,                          -- Reason if rejected
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- One timesheet entry per user per day
    UNIQUE KEY unique_user_date (user_id, work_date),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: leaves
-- Leave requests from employees
-- ============================================================
CREATE TABLE IF NOT EXISTS leaves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Leave details
    leave_type ENUM('annual', 'sick', 'maternity', 'paternity', 'unpaid', 'other') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days DECIMAL(4,1) NOT NULL,           -- Calculated: end - start + 1
    
    -- Reason
    reason TEXT NOT NULL,
    
    -- Status flow: pending -> approved/rejected
    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
    
    -- Review
    reviewed_by INT,
    reviewed_at DATETIME,
    rejection_reason TEXT,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: holidays
-- Company holidays (added by admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    name VARCHAR(255) NOT NULL,                 -- e.g., "Diwali"
    holiday_date DATE NOT NULL UNIQUE,
    description TEXT,
    
    -- Type of holiday
    holiday_type ENUM('national', 'religious', 'company') DEFAULT 'national',
    
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: messages
-- Internal messaging between employees
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    
    subject VARCHAR(255),
    body TEXT NOT NULL,
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: notifications
-- System notifications for users
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- What triggered this notification
    notification_type ENUM(
        'leave_applied', 'leave_approved', 'leave_rejected',
        'task_assigned', 'task_deadline',
        'timesheet_submitted', 'timesheet_approved', 'timesheet_rejected',
        'message_received', 'account_created', 'general'
    ) DEFAULT 'general',
    
    -- Link to relevant page (optional)
    link VARCHAR(255),
    
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: ai_documents
-- Documents uploaded to the AI knowledge base
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,            -- Where the file is stored
    file_type ENUM('pdf', 'docx', 'txt') NOT NULL,
    file_size_kb INT,
    
    -- Document category
    category VARCHAR(100),                      -- e.g., "Leave Policy", "HR Policy"
    description TEXT,
    
    -- Indexing status
    is_indexed BOOLEAN DEFAULT FALSE,           -- Has it been added to ChromaDB?
    indexed_at DATETIME,
    chunk_count INT DEFAULT 0,                  -- How many chunks created
    
    uploaded_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: ai_chat_history
-- Stores AI assistant conversations per user
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    user_id INT NOT NULL,
    
    -- The conversation
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    
    -- Optional: which documents were used to answer
    sources_used TEXT,                          -- JSON list of document names
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- INSERT: Default Admin User
-- Password: Admin@123 (change after first login!)
-- bcrypt hash of "Admin@123"
-- ============================================================
INSERT IGNORE INTO users (
    employee_id, first_name, last_name, email, 
    password_hash, role, department, designation,
    date_of_joining
) VALUES (
    'EMP001',
    'Admin',
    'User',
    'admin@traitsoftwares.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFOaI1WS5X.Y2Ku',  -- Admin@123
    'admin',
    'Administration',
    'System Administrator',
    CURDATE()
);

-- ============================================================
-- INSERT: Sample Holidays
-- ============================================================
INSERT IGNORE INTO holidays (name, holiday_date, holiday_type, description) VALUES
('New Year', '2025-01-01', 'national', 'New Year Day'),
('Republic Day', '2025-01-26', 'national', 'Republic Day of India'),
('Holi', '2025-03-14', 'religious', 'Festival of Colors'),
('Good Friday', '2025-04-18', 'religious', 'Good Friday'),
('Independence Day', '2025-08-15', 'national', 'Independence Day of India'),
('Gandhi Jayanti', '2025-10-02', 'national', 'Birth anniversary of Mahatma Gandhi'),
('Diwali', '2025-10-20', 'religious', 'Festival of Lights'),
('Christmas', '2025-12-25', 'religious', 'Christmas Day');

-- Show success message
SELECT 'Database setup completed successfully!' AS Status;
