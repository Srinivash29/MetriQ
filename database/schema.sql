
USE metriq_db;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(15),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM(
        'applicant',
        'lmo',
        'gatc',
        'admin'
    ) NOT NULL DEFAULT 'applicant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 2. INSTRUMENTS TABLE
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    instrument_name VARCHAR(100) NOT NULL,
    instrument_type VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_instrument_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    UNIQUE (serial_number)
);


-- 3. APPLICATIONS TABLE
CREATE TABLE IF NOT EXISTS applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    instrument_id INT NOT NULL,
    application_type VARCHAR(100) NOT NULL,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferred_date DATE,
    status ENUM(
        'submitted',
        'under_review',
        'scheduled',
        'approved',
        'rejected'
    ) DEFAULT 'submitted',
    remarks TEXT,

    CONSTRAINT fk_application_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_application_instrument
        FOREIGN KEY (instrument_id)
        REFERENCES instruments(instrument_id)
);


-- 4. INSPECTIONS TABLE
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    inspector_id INT NOT NULL,
    inspection_date DATE NOT NULL,
    inspection_result ENUM(
        'passed',
        'failed',
        'pending'
    ) DEFAULT 'pending',
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inspection_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id),

    CONSTRAINT fk_inspection_inspector
        FOREIGN KEY (inspector_id)
        REFERENCES users(user_id)
);


-- 5. CERTIFICATES TABLE
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL UNIQUE,
    certificate_number VARCHAR(100) NOT NULL UNIQUE,
    qr_token CHAR(64) NOT NULL UNIQUE,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    certificate_status ENUM(
        'valid',
        'expired',
        'revoked'
    ) DEFAULT 'valid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_certificate_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
);

-- Verify all five tables
SHOW TABLES;
