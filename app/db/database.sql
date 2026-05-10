-- New Tables -- 
CREATE TABLE rewardType(
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(30) NOT NULL,
    type_desc VARCHAR(100)
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
CREATE TABLE taskType(
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(20) NOT NULL,
    type_desc VARCHAR(200)
);
-- Main Tables -- 
CREATE TABLE users(
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(30) NOT NULL,
    user_fname VARCHAR(20) NOT NULL,
    user_email VARCHAR(100) UNIQUE NOT NULL,
    user_dob DATE NOT NULL,
    user_password TEXT NOT NULL
);
CREATE TABLE tasks(
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(20) NOT NULL,
    task_desc VARCHAR(250),
    type_id INT NOT NULL,
    FOREIGN KEY (type_id) REFERENCES taskType(type_id)
);
CREATE TABLE customTasks(
    cust_id SERIAL PRIMARY KEY,
    cust_name VARCHAR(20) NOT NULL,
    cust_desc VARCHAR(200),
    type_id INT NOT NULL,
    FOREIGN KEY (type_id) REFERENCES taskType(type_id)
);
CREATE TABLE routines(
    rout_id SERIAL PRIMARY KEY,
    rout_name VARCHAR(20) NOT NULL
);
CREATE TABLE reminders(
    reminder_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT,
    cust_id INT,
    reminder_txt VARCHAR(100),
    remind_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (cust_id) REFERENCES customTasks(cust_id),
    CHECK (
        (task_id IS NULL AND cust_id IS NOT NULL)
        OR
        (task_id IS NOT NULL AND cust_id IS NULL)
    )
);
CREATE TABLE metrics(
    met_id SERIAL PRIMARY KEY,
    met_name VARCHAR(20) NOT NULL,
    met_desc VARCHAR(250) NOT NULL,
    met_type INT NOT NULL,
    met_min SMALLINT NOT NULL,
    met_max SMALLINT NOT NULL,
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
    exe_length SMALLINT NOT NULL,
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
    chall_desc VARCHAR(200)
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
CREATE TYPE friend_stat AS ENUM ('Friends', 'Pending - Sent', 'Pending - Received');
CREATE TABLE friends(
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    friend_status friend_stat NOT NULL,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (friend_id) REFERENCES users(user_id),
    CHECK (user_id <> friend_id)
);
-- Intersection Tables --
CREATE TABLE userRoutine(
    user_id INT NOT NULL,
    rout_id INT NOT NULL,
    rout_freq INT NOT NULL,
    PRIMARY KEY (user_id, rout_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (rout_freq) REFERENCES routFreq(freq_id),
    FOREIGN KEY (rout_id) REFERENCES routines(rout_id)
);
CREATE TABLE userTask(
    usertask_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT,
    cust_id INT,
    task_complete BOOLEAN NOT NULL,
    task_date DATE NOT NULL,
    task_stime TIME NOT NULL,
    task_etime TIME NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (cust_id) REFERENCES customTasks(cust_id),
    CHECK (
    (task_id IS NULL AND cust_id IS NOT NULL)
    OR
    (task_id IS NOT NULL AND cust_id IS NULL)
    )
);
CREATE TABLE userChallenges(
    user_id INT NOT NULL,
    chall_id INT NOT NULL,
    chall_sdate DATE NOT NULL,
    chall_edate DATE NOT NULL,
    PRIMARY KEY (user_id, chall_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (chall_id) REFERENCES challenges(chall_id)
);
CREATE TYPE comp_activity AS ENUM ('Pending', 'In Comp');
CREATE TABLE compParticipant(
    user_id INT NOT NULL,
    comp_id INT NOT NULL,
    comp_status comp_activity NOT NULL,
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
    type_id INT NOT NULL,
    met_id INT NOT NULL,
    PRIMARY KEY (type_id, met_id),
    FOREIGN KEY (type_id) REFERENCES taskType(type_id),
    FOREIGN KEY (met_id) REFERENCES metrics(met_id)
);
CREATE TABLE routineTask(
    routinetask_id SERIAL PRIMARY KEY,
    rout_id INT NOT NULL,
    task_id INT,
    cust_id INT,
    FOREIGN KEY (rout_id) REFERENCES routines(rout_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (cust_id) REFERENCES customTasks(cust_id),
    CHECK (
    (task_id IS NULL AND cust_id IS NOT NULL)
    OR
    (task_id IS NOT NULL AND cust_id IS NULL)
    )
);

CREATE TYPE ur_status AS ENUM('Complete', 'Incomplete');
CREATE TABLE userRewards(
    user_id INT NOT NULL,
    reward_id INT NOT NULL,
    reward_status ur_status NOT NULL,
    PRIMARY KEY(user_id, reward_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (reward_id) REFERENCES rewards(reward_id)
);