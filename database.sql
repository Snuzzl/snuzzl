-- New Tables -- 
CREATE TABLE rewardType(
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(30) NOT NULL,
    type_desc VARCHAR(100) NOT NULL,
    type_value INT NOT NULL,
    type_badge BOOLEAN NOT NULL
);
CREATE TABLE metType(
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(30) NOT NULL,
    type_desc VARCHAR(100)
);
CREATE TABLE routFreq(
    freq_id SERIAL PRIMARY KEY,
    freq_name VARCHAR(30) NOT NULL,
    freq_desc VARCHAR(100)
);
-- Main Tables -- 
CREATE TABLE users(
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(30) NOT NULL,
    user_fname VARCHAR(20) NOT NULL,
    user_email VARCHAR(100) UNIQUE NOT NULL,
    user_dob DATE NOT NULL
);
CREATE TABLE tasks(
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(20) NOT NULL,
    task_desc VARCHAR(250)
);
CREATE TABLE routines(
    rout_id SERIAL PRIMARY KEY,
    rout_name VARCHAR(20) NOT NULL,
    rout_freq INT NOT NULL,
    FOREIGN KEY (rout_freq) REFERENCES routFreq(freq_id)
);
CREATE TABLE reminders(
    reminder_id SERIAL PRIMARY KEY,
    task_id INT NOT NULL,
    reminder_txt VARCHAR(100),
    remind_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
CREATE TABLE metrics(
    met_id SERIAL PRIMARY KEY,
    met_name VARCHAR(20) NOT NULL,
    met_desc VARCHAR(250) NOT NULL,
    met_type INT NOT NULL,
    FOREIGN KEY (met_type) REFERENCES metType(type_id)
);
CREATE TABLE metricValue(
    metval_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    met_id INT NOT NULL,
    metval_date DATE NOT NULL,
    metval_val SMALLINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (met_id) REFERENCES metrics(met_id)
);
CREATE TABLE libraries(
    libr_id SERIAL PRIMARY KEY,
    libr_name VARCHAR(50) NOT NULL,
    libr_desc VARCHAR(250),
    libr_created_date DATE NOT NULL
);
CREATE TABLE exercises(
    exe_id SERIAL PRIMARY KEY,
    exe_name VARCHAR(50) NOT NULL,
    exe_length INTERVAL NOT NULL, -- Duration in HH:MM:SS format
    exe_kcal INT NOT NULL
);
CREATE TABLE communities(
    comm_id SERIAL PRIMARY KEY,
    comm_name VARCHAR(50) NOT NULL,
    comm_date_created DATE NOT NULL
);
CREATE TABLE challenges(
    chall_id SERIAL PRIMARY KEY,
    chall_name VARCHAR(50) NOT NULL,
    chall_desc VARCHAR(200),
    chall_stime DATE NOT NULL,
    chall_edate DATE NOT NULL
);
CREATE TABLE rewards(
    reward_id SERIAL PRIMARY KEY,
    chall_id INT NOT NULL,
    reward_name VARCHAR(50) NOT NULL,
    reward_type INT NOT NULL,
    FOREIGN KEY (reward_type) REFERENCES rewardType(type_id),
    FOREIGN KEY (chall_id) REFERENCES challenges(chall_id)
);
CREATE TABLE competitions(
    comp_id SERIAL PRIMARY KEY,
    comp_name VARCHAR(50) NOT NULL,
    comp_sdate DATE NOT NULL,
    comp_edate DATE NOT NULL
);
CREATE TABLE friends(
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    friend_status BOOLEAN NOT NULL,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (friend_id) REFERENCES users(user_id),
    CONSTRAINT unique_friendship CHECK (user_id < friend_id)
);

-- Intersection Tables --
CREATE TABLE userRoutine(
    user_id INT NOT NULL,
    rout_id INT NOT NULL,
    PRIMARY KEY (user_id, rout_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (rout_id) REFERENCES routines(rout_id)
);
CREATE TABLE userTask(
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (task_id, user_id),
    task_complete BOOLEAN NOT NULL,
    task_date DATE NOT NULL,
    task_stime TIME NOT NULL,
    task_etime TIME NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE userChallenges(
    user_id INT NOT NULL,
    chall_id INT NOT NULL,
    PRIMARY KEY (user_id, chall_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (chall_id) REFERENCES challenges(chall_id)
);
CREATE TABLE compParticipant(
    user_id INT NOT NULL,
    comp_id INT NOT NULL,
    PRIMARY KEY (user_id, comp_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (comp_id) REFERENCES competitions(comp_id)
);
CREATE TABLE communityMembers(
    user_id INT NOT NULL,
    comm_id INT NOT NULL,
    PRIMARY KEY (user_id, comm_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (comm_id) REFERENCES communities(comm_id)
);
CREATE TABLE userLibrary(
    user_id INT NOT NULL,
    libr_id INT NOT NULL,
    PRIMARY KEY (user_id, libr_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (libr_id) REFERENCES libraries(libr_id)
);
CREATE TABLE exerciseLibrary(
    exe_id INT NOT NULL,
    libr_id INT NOT NULL,
    PRIMARY KEY (exe_id, libr_id),
    FOREIGN KEY (exe_id) REFERENCES exercises(exe_id),
    FOREIGN KEY (libr_id) REFERENCES libraries(libr_id)
);
CREATE TABLE taskChallenges(
    task_id INT NOT NULL,
    chall_id INT NOT NULL,
    PRIMARY KEY (task_id, chall_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (chall_id) REFERENCES challenges(chall_id)
);
CREATE TABLE compChallenges(
    comp_id INT NOT NULL,
    chall_id INT NOT NULL,
    PRIMARY KEY (comp_id, chall_id),
    FOREIGN KEY (comp_id) REFERENCES competitions(comp_id),
    FOREIGN KEY (chall_id) REFERENCES challenges(chall_id)
);
CREATE TABLE taskMetric(
    task_id INT NOT NULL,
    met_id INT NOT NULL,
    PRIMARY KEY (task_id, met_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (met_id) REFERENCES metrics(met_id)
);
