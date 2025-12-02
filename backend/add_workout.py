import mysql.connector

# --- AYARLAR ---
DB_CONFIG = {
  'user': 'root',
  'password': '1234',  # Kendi şifreni buraya yaz
  'host': '127.0.0.1',
  'database': 'gympro_db'
}

def add_full_body_workout():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("1. 'Full Body' antrenmanı oluşturuluyor...")
        # Önce antrenman başlığını ekle
        cursor.execute("INSERT INTO FixedWorkout (title, duration_min) VALUES (%s, %s)", 
                       ("Full Body Başlangıç", 60))
        fixed_id = cursor.lastrowid
        print(f"   Antrenman eklendi. ID: {fixed_id}")

        # 2. Egzersizlerin ID'lerini bulalım
        # İsimlerine göre ID'leri çekiyoruz
        exercise_names = ["Squat", "Bench Press", "Lat Pulldown", "Overhead Press", "Plank"]
        exercise_ids = {}
        
        for name in exercise_names:
            cursor.execute("SELECT exercise_id FROM Exercise WHERE name = %s", (name,))
            result = cursor.fetchone()
            if result:
                exercise_ids[name] = result[0]
            else:
                print(f"   UYARI: {name} bulunamadı, bu egzersiz atlanacak.")

        # 3. Antrenman detaylarını (Set/Tekrar) ekleyelim
        # (fixed_id, exercise_id, order_no, sets, reps, rest_sec)
        workout_plan = [
            (fixed_id, exercise_ids.get("Squat"), 1, 3, 12, 60),
            (fixed_id, exercise_ids.get("Bench Press"), 2, 3, 10, 60),
            (fixed_id, exercise_ids.get("Lat Pulldown"), 3, 3, 12, 45),
            (fixed_id, exercise_ids.get("Overhead Press"), 4, 3, 10, 45),
            (fixed_id, exercise_ids.get("Plank"), 5, 3, 1, 30) # 1 tekrar (sn bazlı düşünülebilir)
        ]

        print("2. Egzersizler plana ekleniyor...")
        for item in workout_plan:
            # Eğer egzersiz ID'si bulunduysa ekle
            if item[1] is not None:
                cursor.execute("""
                    INSERT INTO FixedWorkoutExercise (fixed_id, exercise_id, order_no, sets, reps, rest_sec)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, item)

        conn.commit()
        print("\nBAŞARILI! 'Full Body Başlangıç' antrenmanı veritabanına işlendi.")
        
    except mysql.connector.Error as err:
        print(f"HATA: {err}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    add_full_body_workout()