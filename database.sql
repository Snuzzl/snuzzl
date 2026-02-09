-- Users ---
CREATE TABLE users(
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    user_fname VARCHAR(30) NOT NULL,
    user_lname VARCHAR(30),
    user_email VARCHAR(255) UNIQUE,
    user_phone VARCHAR(15) UNIQUE,
    user_dob DATE NOT NULL,
    user_password_hash TEXT NOT NULL,
    CONSTRAINT email_or_phone CHECK(
        COALESCE(NULLIF(user_email, ''), NULLIF(user_phone, '')) IS NOT NULL
    )
);
--- Tasks ---
CREATE TABLE tasks(
    task_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    name VARCHAR(20) NOT NULL,
    description VARCHAR(250),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    state BOOLEAN DEFAULT FALSE,
    routine_id INT,
    created_at TIMESTAMP DEFAULT NOW()
);
--- Metrics ---
CREATE TABLE metrics (
    metric_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    name VARCHAR(20) NOT NULL,
    value NUMERIC(4, 1) CHECK (),
    --Range--
    date DATE NOT NULL
);
--- Task Metric Intersection ---
CREATE TABLE task_metrics (
    task_id INT REFERENCES tasks(task_id),
    metric_id INT REFERENCES metrics(metric_id),
    PRIMARY KEY (task_id, metric_id)
);
--- Specialized Tasks ---
CREATE TABLE sleep (
    sleep_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    hours NUMERIC(4, 1) CHECK (
        hours >= 0
        AND hours <= 24
    ),
    quality INT CHECK (
        quality >= 0
        AND quality <= 10
    ),
    date DATE NOT NULL
);
CREATE TABLE steps (
    steps_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    steps INT CHECK (
        steps >= 0
        AND steps <= 100000
    ),
    date DATE NOT NULL
);
CREATE TABLE mood (
    mood_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    feeling VARCHAR(50) NOT NULL,
    date DATE NOT NULL
);
--- Reminders ---
CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    task_id INT REFERENCES tasks(task_id),
    text VARCHAR(100) NOT NULL,
    remind_at TIMESTAMP NOT NULL
);
--- Rewards ---
CREATE TABLE rewards (
    reward_id SERIAL PRIMARY KEY,
    reward_name VARCHAR(50) NOT NULL,
    reward_description VARCHAR(250),
) --- User Rewards Intersection ---
CREATE TABLE user_rewards (
    user_id INT REFERENCES users(user_id),
    reward_id INT REFERENCES rewards(reward_id),
    PRIMARY KEY (user_id, reward_id)
);