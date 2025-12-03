-- ================================================================
-- GymPro SaaS - Multi-Tenant Veritabanı Şeması
-- ================================================================

USE gympro_db;

-- 1. GYM Tablosu (Spor Salonları)
CREATE TABLE IF NOT EXISTS Gym (
    gym_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    location VARCHAR(255),
    capacity INT CHECK (capacity >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Member Tablosu (Global Kullanıcılar)
CREATE TABLE IF NOT EXISTS Member (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(250) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    gender CHAR(1),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Membership Tablosu (Üye-Salon İlişkisi - Multi-Tenancy)
CREATE TABLE IF NOT EXISTS Membership (
    membership_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    gym_id INT NOT NULL,
    type VARCHAR(10) NOT NULL, -- 'timed' veya 'credit'
    start_date DATE,
    end_date DATE,
    credit_total INT DEFAULT 0,
    credit_used INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE
);

-- 4. Trainer Tablosu (Antrenörler - Salon Bazlı)
-- Trainer'lar da Member olabilir (member_id ile bağlantı)
-- Bu sayede aynı turnike sistemi ile giriş/çıkış yapabilirler
CREATE TABLE IF NOT EXISTS Trainer (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    gym_id INT NOT NULL,
    member_id INT NULL, -- Opsiyonel: Trainer aynı zamanda Member ise
    name VARCHAR(120) NOT NULL,
    specialty VARCHAR(100),
    is_in_gym BOOLEAN DEFAULT FALSE,
    rating_avg DECIMAL(3,2) DEFAULT 0.00,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE SET NULL
);

-- 5. GymAdmin Tablosu (Salon Yöneticileri)
CREATE TABLE IF NOT EXISTS GymAdmin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    gym_id INT NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE
);

-- 6. Turnstile Event Tablosu (Giriş/Çıkış - Salon Bazlı)
CREATE TABLE IF NOT EXISTS TurnstileEvent (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    gym_id INT NOT NULL,
    member_id INT,
    trainer_id INT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    direction VARCHAR(3) NOT NULL, -- 'in' veya 'out'
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE SET NULL,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL
);

-- 7. Exercise Tablosu (Egzersizler - Global)
CREATE TABLE IF NOT EXISTS Exercise (
    exercise_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    muscle_group VARCHAR(60)
);

-- 8. Fixed Workout Tablosu (Sabit Programlar - Global + Salon Özel)
CREATE TABLE IF NOT EXISTS FixedWorkout (
    fixed_id INT AUTO_INCREMENT PRIMARY KEY,
    gym_id INT NULL, -- NULL = Global, değer = Salon Özel
    title VARCHAR(120) NOT NULL,
    duration_min INT,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE
);

-- 9. Fixed WorkoutExercise Tablosu
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

-- 10. Custom Routine Tablosu (Kişisel Rutinler - Üyeye Bağlı)
CREATE TABLE IF NOT EXISTS CustomRoutine (
    routine_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    title VARCHAR(120),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE
);

-- 11. Custom Routine Exercise Tablosu
CREATE TABLE IF NOT EXISTS CustomRoutineExercise (
    routine_id INT,
    exercise_id INT,
    order_no INT,
    sets INT,
    reps INT,
    rest_sec INT,
    PRIMARY KEY (routine_id, exercise_id),
    FOREIGN KEY (routine_id) REFERENCES CustomRoutine(routine_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES Exercise(exercise_id) ON DELETE CASCADE
);

-- ================================================================
-- TEST VERİLERİ
-- ================================================================

-- Test Gym
INSERT IGNORE INTO Gym (gym_id, name, location, capacity) VALUES 
(1, 'FitZone Kadıköy', 'Kadıköy, İstanbul', 100),
(2, 'PowerGym Beşiktaş', 'Beşiktaş, İstanbul', 80);

-- Test Admin (şifre: admin123)
INSERT IGNORE INTO GymAdmin (gym_id, username, password) VALUES 
(1, 'admin', 'admin123'),
(2, 'admin2', 'admin123');

-- Test Üyeler (Trainer'lar da dahil - şifre: 123456)
INSERT IGNORE INTO Member (member_id, name, email, password) VALUES
(1, 'Ahmet Yılmaz', 'ahmet@trainer.com', '123456'),
(2, 'Ayşe Demir', 'ayse@trainer.com', '123456'),
(3, 'Mehmet Kaya', 'mehmet@trainer.com', '123456'),
(4, 'Test Kullanıcı', 'test@test.com', '123456');

-- Trainer'ların üyelikleri (kredisiz - sınırsız giriş için timed tipinde uzun süreli)
INSERT IGNORE INTO Membership (member_id, gym_id, type, start_date, end_date, is_active) VALUES
(1, 1, 'timed', '2025-01-01', '2030-12-31', TRUE),
(2, 1, 'timed', '2025-01-01', '2030-12-31', TRUE),
(3, 2, 'timed', '2025-01-01', '2030-12-31', TRUE),
(4, 1, 'credit', '2025-01-01', NULL, TRUE);

-- Test kullanıcının kredisi
UPDATE Membership SET credit_total = 30, credit_used = 5 WHERE member_id = 4 AND gym_id = 1;

-- Test Antrenörler (member_id ile bağlantılı)
INSERT IGNORE INTO Trainer (gym_id, member_id, name, specialty, is_in_gym, rating_avg) VALUES
(1, 1, 'Ahmet Yılmaz', 'Fitness', FALSE, 4.5),
(1, 2, 'Ayşe Demir', 'Pilates', FALSE, 4.8),
(2, 3, 'Mehmet Kaya', 'CrossFit', FALSE, 4.2);

-- Test Egzersizler
INSERT IGNORE INTO Exercise (exercise_id, name, muscle_group) VALUES
(1, 'Bench Press', 'Göğüs'),
(2, 'Squat', 'Bacak'),
(3, 'Deadlift', 'Sırt'),
(4, 'Shoulder Press', 'Omuz'),
(5, 'Bicep Curl', 'Kol'),
(6, 'Tricep Dips', 'Kol'),
(7, 'Lat Pulldown', 'Sırt'),
(8, 'Leg Press', 'Bacak');