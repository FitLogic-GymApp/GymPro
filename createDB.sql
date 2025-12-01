USE gympro_db;

-- 1. GYM Tablosu [cite: 7, 8]
CREATE TABLE IF NOT EXISTS Gym (
    gym_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    location VARCHAR(255),
    capacity INT CHECK (capacity >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Member Tablosu [cite: 9, 10]
CREATE TABLE IF NOT EXISTS Member (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(250) NOT NULL,
    phone VARCHAR(20),
    gender CHAR(1),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Membership Tablosu [cite: 11, 12]
CREATE TABLE IF NOT EXISTS Membership (
    membership_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    type VARCHAR(10) NOT NULL, -- 'timed' veya 'credit'
    start_date DATE,
    end_date DATE,
    credit_total INT DEFAULT 0,
    credit_used INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE
);

-- 4. Trainer Tablosu [cite: 15, 16]
CREATE TABLE IF NOT EXISTS Trainer (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    specialty VARCHAR(100),
    is_in_gym BOOLEAN DEFAULT FALSE,
    rating_avg DECIMAL(3,2) DEFAULT 0.00
);

-- 5. Turnstile Event Tablosu [cite: 13, 14]
CREATE TABLE IF NOT EXISTS TurnstileEvent (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    trainer_id INT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    direction VARCHAR(3) NOT NULL, -- 'in' veya 'out'
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE SET NULL,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL
);

-- 6. Exercise Tablosu [cite: 17, 18]
CREATE TABLE IF NOT EXISTS Exercise (
    exercise_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    muscle_group VARCHAR(60)
);

-- 7. Fixed Workout Tablosu [cite: 19, 20]
CREATE TABLE IF NOT EXISTS FixedWorkout (
    fixed_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    duration_min INT
);

-- 8. Fixed WorkoutExercise Tablosu [cite: 21, 22]
CREATE TABLE IF NOT EXISTS FixedWorkoutExercise (
    fixed_id INT,
    exercise_id INT,
    order_no INT,
    sets INT,
    reps INT,
    rest_sec INT,
    PRIMARY KEY (fixed_id, exercise_id),
    FOREIGN KEY (fixed_id) REFERENCES FixedWorkout(fixed_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES Exercise(exercise_id) ON DELETE CASCADE
);

-- 9. Custom Routine Tablosu [cite: 23, 24]
CREATE TABLE IF NOT EXISTS CustomRoutine (
    routine_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    title VARCHAR(120),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE
);

-- 10. Custom Routine Exercise Tablosu [cite: 25, 26]
CREATE TABLE IF NOT EXISTS CustomRoutineExercise (
    routine_id INT,
    exercise_id INT,
    order_no INT,
    sets INT,
    reps INT,
    rest_sec INT,
    PRIMARY KEY (routine_id, exercise_id), -- Composite PK mantıklı olabilir
    FOREIGN KEY (routine_id) REFERENCES CustomRoutine(routine_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES Exercise(exercise_id) ON DELETE CASCADE
);