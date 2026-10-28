
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";
SET NAMES utf8mb4;


CREATE TABLE users (
    id                  INT NOT NULL AUTO_INCREMENT,
    first_name          VARCHAR(50)  NOT NULL,
    last_name           VARCHAR(50)  NOT NULL,
    username            VARCHAR(50)  NOT NULL,
    password            VARCHAR(500) NOT NULL,

    user_type           VARCHAR(20)  NOT NULL DEFAULT 'sales', 
    lock_status         VARCHAR(20)  NOT NULL DEFAULT 'active',
    resign_status       VARCHAR(20)  NOT NULL DEFAULT 'active',
    about_me            TEXT         NOT NULL,
    employment_date     DATE         NOT NULL,
    resign_date         DATE         NULL,
    profile_picture     VARCHAR(500) NOT NULL DEFAULT '',
    position            VARCHAR(50)  NOT NULL DEFAULT '',

    failed_attempts     INT          DEFAULT 0,
    last_failed_login   DATETIME     NULL,
    locked_until        DATETIME     NULL,
    phone               VARCHAR(20)  NULL,
    mfa_secret          VARCHAR(64)  NULL,
    mfa_enabled         TINYINT(1)   NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE login_attempts (
    id            INT NOT NULL AUTO_INCREMENT,
    ip_address    VARCHAR(45) NOT NULL,
    attempts      INT NOT NULL DEFAULT 0,
    last_attempt  DATETIME DEFAULT CURRENT_TIMESTAMP,
    locked_until  DATETIME NULL,
    PRIMARY KEY (id),
    KEY idx_login_attempts_ip (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE projects (
    id                 INT NOT NULL AUTO_INCREMENT,
    title              VARCHAR(255) DEFAULT NULL,
    location           VARCHAR(255) DEFAULT NULL,
    description        TEXT DEFAULT NULL,
    price              DECIMAL(12,2) DEFAULT NULL,   
    discount_price     DECIMAL(12,2) DEFAULT NULL,
    discount_reason    VARCHAR(255) DEFAULT NULL,
    image_path         VARCHAR(255) DEFAULT NULL,    
    google_map         TEXT DEFAULT NULL,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE project_images (
    id           INT NOT NULL AUTO_INCREMENT,
    project_id   INT NOT NULL,
    image_path   VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_project_images_project (project_id),
    CONSTRAINT fk_project_images_project
        FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE inquiries (
    id             INT NOT NULL AUTO_INCREMENT,
    project_id     INT DEFAULT NULL,
    name           VARCHAR(255) DEFAULT NULL,
    phone          VARCHAR(50) DEFAULT NULL,
    message        TEXT DEFAULT NULL,   
    inquiry_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_inquiries_project (project_id),
    CONSTRAINT fk_inquiries_project
        FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE contact_messages (
    id             INT NOT NULL AUTO_INCREMENT,
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(100) NOT NULL,
    phone          VARCHAR(50) DEFAULT NULL,
    message        TEXT NOT NULL,
    submitted_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE reviews (
    id           INT NOT NULL AUTO_INCREMENT,
    project_id   INT NOT NULL,
    name         VARCHAR(100) DEFAULT NULL,
    rating       TINYINT DEFAULT NULL,
    comment      TEXT DEFAULT NULL,  
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_reviews_project (project_id),
    CONSTRAINT fk_reviews_project
        FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE leads (
    id                 INT NOT NULL AUTO_INCREMENT,
    customer_name      VARCHAR(50) NOT NULL,
    phone              VARCHAR(50) NOT NULL,
    status             VARCHAR(20) NOT NULL DEFAULT 'new', 
    interest           VARCHAR(20) DEFAULT NULL,
    remark             TEXT DEFAULT NULL,
    history            TEXT DEFAULT NULL,
    agent_id           INT NOT NULL,
    registration_date  DATE DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_leads_agent (agent_id),
    CONSTRAINT fk_leads_agent
        FOREIGN KEY (agent_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE subscribers (
    id              INT NOT NULL AUTO_INCREMENT,
    email           VARCHAR(255) NOT NULL,
    subscribed_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE audit_log (
    id               INT NOT NULL AUTO_INCREMENT,
    actor_user_id    INT NULL,
    actor_username   VARCHAR(50) NULL,
    action           VARCHAR(50) NOT NULL,
    target_type      VARCHAR(50) NULL,
    target_id        INT NULL,
    before_state     TEXT NULL,
    after_state      TEXT NULL,
    ip_address       VARCHAR(45) NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_audit_actor (actor_user_id),
    KEY idx_audit_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO users
    (first_name, last_name, username, password, user_type, lock_status, resign_status,
     about_me, employment_date, resign_date, profile_picture, position)
VALUES
    ('Admin', 'User', 'admin', MD5('Password123!'), 'admin', 'active', 'active',
     'System administrator', '2023-01-01', NULL, '', 'Administrator'),
    ('Alice', 'Agent', 'alice', MD5('Password123!'), 'sales', 'active', 'active',
     'Sales agent', '2023-02-01', NULL, '', 'Sales Agent'),
    ('Bob', 'Broker', 'bob', MD5('Password123!'), 'sales', 'active', 'active',
     'Sales agent', '2023-03-01', NULL, '', 'Sales Agent');

INSERT INTO projects (title, location, description, price, discount_price, image_path)
VALUES
    ('Sunrise Villas', 'Addis Ababa, Bole', 'Modern 3-bedroom villas.', 4500000.00, NULL, ''),
    ('Green Park Apartments', 'Addis Ababa, CMC', '2-bedroom apartments near the park.', 2800000.00, 2600000.00, '');

INSERT INTO leads (customer_name, phone, status, interest, remark, history, agent_id, registration_date)
VALUES
    ('Customer One', '0911000001', 'new', 'Sunrise Villas', 'Interested, requested a viewing.', '', 2, CURDATE()),
    ('Customer Two', '0911000002', 'follow_up', 'Green Park Apartments', 'Waiting on financing decision.', '', 3, CURDATE());
