import mysql.connector

# --- AYARLAR ---
DB_CONFIG = {
  'user': 'root',
  'password': '1234',  # Şifreni buraya yaz
  'host': '127.0.0.1',
  'database': 'gympro_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_or_create_exercise_id(cursor, name, muscle_group):
    """Egzersiz varsa ID'sini döner, yoksa oluşturup ID'sini döner."""
    cursor.execute("SELECT exercise_id FROM Exercise WHERE name = %s", (name,))
    res = cursor.fetchone()
    if res:
        return res[0]
    else:
        print(f"   -> Yeni Egzersiz Ekleniyor: {name}")
        cursor.execute("INSERT INTO Exercise (name, muscle_group) VALUES (%s, %s)", (name, muscle_group))
        return cursor.lastrowid

def setup_all_workouts():
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- TÜM PROGRAMLAR LİSTESİ ---
    # Format: (Program Adı, Süre dk, [ (Hareket Adı, Kas Grubu, Set, Tekrar, Dinlenme sn) ])
    all_routines = [
        # 1. BAŞLANGIÇ SEVİYESİ
        ("Full Body Başlangıç", 60, [
            ("Squat", "Legs", 3, 12, 60),
            ("Bench Press", "Chest", 3, 10, 60),
            ("Lat Pulldown", "Back", 3, 12, 45),
            ("Overhead Press", "Shoulders", 3, 10, 45),
            ("Plank", "Core", 3, 60, 30) # 60sn bekleme değil süre
        ]),
        
        # 2. ORTA/İLERİ SEVİYE (UPPER/LOWER)
        ("Upper Body Power", 75, [
            ("Bench Press", "Chest", 4, 6, 120),
            ("Bent Over Row", "Back", 4, 8, 90),
            ("Overhead Press", "Shoulders", 3, 8, 90),
            ("Lat Pulldown", "Back", 3, 10, 60),
            ("Dumbbell Curl", "Arms", 3, 12, 60),
            ("Skullcrusher", "Arms", 3, 12, 60)
        ]),
        ("Lower Body Power", 70, [
            ("Squat", "Legs", 4, 6, 180),
            ("Deadlift", "Back", 3, 5, 180),
            ("Leg Press", "Legs", 3, 10, 90),
            ("Calf Raise", "Legs", 4, 15, 45),
            ("Plank", "Core", 3, 60, 60)
        ]),
        
        # 3. İLERİ SEVİYE (PUSH/PULL/LEGS)
        ("Push Day (İtiş)", 60, [
            ("Incline Bench Press", "Chest", 4, 8, 90),
            ("Overhead Press", "Shoulders", 3, 10, 90),
            ("Lateral Raise", "Shoulders", 4, 15, 45),
            ("Tricep Extension", "Arms", 3, 12, 60),
            ("Dips", "Chest", 3, 10, 60)
        ]),
        ("Pull Day (Çekiş)", 60, [
            ("Pull Up", "Back", 4, 8, 120),
            ("Barbell Row", "Back", 3, 10, 90),
            ("Face Pull", "Shoulders", 3, 15, 60),
            ("Hammer Curl", "Arms", 3, 12, 60),
            ("Preacher Curl", "Arms", 3, 12, 60)
        ]),
        ("Leg Day (Bacak)", 65, [
            ("Squat", "Legs", 4, 8, 120),
            ("Romanian Deadlift", "Legs", 3, 10, 90),
            ("Leg Extension", "Legs", 3, 15, 60),
            ("Leg Curl", "Legs", 3, 15, 60),
            ("Walking Lunge", "Legs", 3, 20, 60)
        ])
    ]

    print("🚀 Antrenman veritabanı senkronize ediliyor...")

    try:
        for title, duration, exercises in all_routines:
            # 1. Program daha önce eklenmiş mi?
            cursor.execute("SELECT fixed_id FROM FixedWorkout WHERE title = %s", (title,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"✅ Zaten Var: {title} (Atlanıyor)")
                continue

            # 2. Program Yoksa Ekle
            cursor.execute("INSERT INTO FixedWorkout (title, duration_min) VALUES (%s, %s)", (title, duration))
            fixed_id = cursor.lastrowid
            print(f"🆕 Eklendi: {title}")

            # 3. İçeriği Doldur
            for order, (ex_name, muscle, sets, reps, rest) in enumerate(exercises, 1):
                ex_id = get_or_create_exercise_id(cursor, ex_name, muscle)
                
                cursor.execute("""
                    INSERT INTO FixedWorkoutExercise (fixed_id, exercise_id, order_no, sets, reps, rest_sec)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fixed_id, ex_id, order, sets, reps, rest))

        conn.commit()
        print("\n🎉 İŞLEM TAMAM! Tüm antrenmanlar hazır.")

    except Exception as e:
        print(f"❌ HATA: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_all_workouts()