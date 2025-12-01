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

        # --- 4) RUTİNLERİM (LİSTELEME) ---
@app.route('/api/my-routines', methods=['GET'])
def get_my_routines():
    # Test için yine ID=1 varsayıyoruz
    member_id = request.args.get('member_id', 1)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Sadece rutin başlıklarını getir
        cursor.execute("""
            SELECT routine_id, title, created_at 
            FROM CustomRoutine 
            WHERE member_id = %s 
            ORDER BY created_at DESC
        """, (member_id,))
        routines = cursor.fetchall()
        return jsonify(routines)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 4.1) YENİ RUTİN OLUŞTURMA ---
@app.route('/api/my-routines', methods=['POST'])
def create_routine():
    data = request.get_json()
    member_id = data.get('member_id', 1)
    title = data.get('title')
    
    if not title:
        return jsonify({'error': 'Rutin başlığı (title) zorunludur'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO CustomRoutine (member_id, title) VALUES (%s, %s)", 
                       (member_id, title))
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({'message': 'Rutin oluşturuldu', 'routine_id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 4.2) RUTİN DETAYI VE EGZERSİZLERİ ---
@app.route('/api/my-routines/<int:routine_id>', methods=['GET'])
def get_routine_detail(routine_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Rutin başlığını al
        cursor.execute("SELECT * FROM CustomRoutine WHERE routine_id = %s", (routine_id,))
        routine = cursor.fetchone()
        
        if not routine:
            return jsonify({'error': 'Rutin bulunamadı'}), 404

        # 2. Rutindeki egzersizleri al
        cursor.execute("""
            SELECT 
                cre.exercise_id,
                e.name,
                cre.sets, cre.reps, cre.rest_sec, cre.order_no
            FROM CustomRoutineExercise cre
            JOIN Exercise e ON cre.exercise_id = e.exercise_id
            WHERE cre.routine_id = %s
            ORDER BY cre.order_no ASC
        """, (routine_id,))
        exercises = cursor.fetchall()
        
        routine['exercises'] = exercises
        return jsonify(routine)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 4.3) RUTİNE EGZERSİZ EKLEME ---
@app.route('/api/my-routines/<int:routine_id>/add-exercise', methods=['POST'])
def add_exercise_to_routine(routine_id):
    data = request.get_json()
    exercise_id = data.get('exercise_id')
    sets = data.get('sets', 3)
    reps = data.get('reps', 10)
    rest_sec = data.get('rest_sec', 60)
    order_no = data.get('order_no', 1)

    if not exercise_id:
        return jsonify({'error': 'Exercise ID zorunlu'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO CustomRoutineExercise (routine_id, exercise_id, sets, reps, rest_sec, order_no)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (routine_id, exercise_id, sets, reps, rest_sec, order_no))
        conn.commit()
        return jsonify({'message': 'Egzersiz rutine eklendi'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_full_body_workout()