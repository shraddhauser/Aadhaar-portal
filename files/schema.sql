-- =============================================================
-- Aadhaar Analytics Portal - Database Schema
-- =============================================================

CREATE DATABASE IF NOT EXISTS aadhaar_analytics;
USE aadhaar_analytics;

-- -------------------------------------------------------------
-- Table: regions
-- Stores state/district hierarchy for geographic filtering
-- -------------------------------------------------------------
CREATE TABLE regions (
    region_id     INT AUTO_INCREMENT PRIMARY KEY,
    state_name    VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    region_code   VARCHAR(20)  UNIQUE NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Table: enrollments
-- Core table tracking Aadhaar enrollment records
-- -------------------------------------------------------------
CREATE TABLE enrollments (
    enrollment_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    region_id          INT NOT NULL,
    enrollment_date    DATE NOT NULL,
    gender             ENUM('Male','Female','Other') NOT NULL,
    age_group          ENUM('0-18','19-35','36-60','60+') NOT NULL,
    enrollment_status  ENUM('Pending','Verified','Rejected','Generated') NOT NULL DEFAULT 'Pending',
    aadhaar_generated  BOOLEAN DEFAULT FALSE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- -------------------------------------------------------------
-- Table: updates
-- Tracks update requests (name, address, biometric, etc.)
-- -------------------------------------------------------------
CREATE TABLE updates (
    update_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    region_id      INT NOT NULL,
    update_date    DATE NOT NULL,
    update_type    ENUM('Name','Address','Mobile','Email','Biometric','Photo','DOB') NOT NULL,
    update_status  ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- -------------------------------------------------------------
-- Table: biometric_data
-- Anonymized biometric quality metrics per enrollment batch
-- -------------------------------------------------------------
CREATE TABLE biometric_data (
    biometric_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id       BIGINT NOT NULL,
    fingerprint_quality TINYINT CHECK (fingerprint_quality BETWEEN 0 AND 100),
    iris_quality        TINYINT CHECK (iris_quality BETWEEN 0 AND 100),
    photo_quality       TINYINT CHECK (photo_quality BETWEEN 0 AND 100),
    captured_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
);

-- -------------------------------------------------------------
-- Table: anomalies
-- Detected irregularities flagged by the analytics engine
-- -------------------------------------------------------------
CREATE TABLE anomalies (
    anomaly_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    region_id     INT NOT NULL,
    anomaly_type  ENUM('Duplicate','Quality','Surge','Drop','Mismatch') NOT NULL,
    severity      ENUM('Low','Medium','High','Critical') NOT NULL,
    description   TEXT,
    detected_on   DATE NOT NULL,
    resolved      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- -------------------------------------------------------------
-- Table: daily_stats
-- Pre-aggregated daily enrollment/update counts for dashboards
-- -------------------------------------------------------------
CREATE TABLE daily_stats (
    stat_id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    stat_date           DATE NOT NULL,
    region_id           INT NOT NULL,
    total_enrollments   INT DEFAULT 0,
    total_updates       INT DEFAULT 0,
    aadhaar_generated   INT DEFAULT 0,
    pending_count       INT DEFAULT 0,
    rejected_count      INT DEFAULT 0,
    UNIQUE KEY uq_date_region (stat_date, region_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- -------------------------------------------------------------
-- Table: admin_users
-- Portal admin authentication (hashed passwords)
-- -------------------------------------------------------------
CREATE TABLE admin_users (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150),
    role          ENUM('SuperAdmin','Analyst','Viewer') NOT NULL DEFAULT 'Viewer',
    last_login    TIMESTAMP,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Seed: Sample regions
-- -------------------------------------------------------------
INSERT INTO regions (state_name, district_name, region_code) VALUES
('Maharashtra','Mumbai','MH-MUM'),
('Maharashtra','Pune','MH-PUN'),
('Maharashtra','Nashik','MH-NSK'),
('Karnataka','Bengaluru','KA-BLR'),
('Karnataka','Mysuru','KA-MYS'),
('Tamil Nadu','Chennai','TN-CHN'),
('Tamil Nadu','Coimbatore','TN-CBE'),
('Uttar Pradesh','Lucknow','UP-LKO'),
('Uttar Pradesh','Agra','UP-AGR'),
('Delhi','New Delhi','DL-NDL');

-- -------------------------------------------------------------
-- Seed: Default admin (password: Admin@1234 — change in prod)
-- -------------------------------------------------------------
INSERT INTO admin_users (username, password_hash, full_name, role)
VALUES ('admin', '$2b$12$KIX9XaRb8HtF5nV2Qe3.Ke8m2mHgz5lP7YqNwJFHlRpXtGZwDtCdW', 'System Admin', 'SuperAdmin');

-- -------------------------------------------------------------
-- View: enrollment_summary — used by the analytics API
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW enrollment_summary AS
SELECT
    r.state_name,
    r.district_name,
    r.region_code,
    DATE_FORMAT(e.enrollment_date, '%Y-%m') AS month,
    e.gender,
    e.age_group,
    e.enrollment_status,
    COUNT(*)                                AS total,
    SUM(e.aadhaar_generated)                AS generated
FROM enrollments e
JOIN regions r ON e.region_id = r.region_id
GROUP BY r.region_id, month, e.gender, e.age_group, e.enrollment_status;
