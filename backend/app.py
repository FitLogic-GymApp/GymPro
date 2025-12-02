from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from datetime import date
import os

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Halil_2003'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'database': os.environ.get('DB_NAME', 'gympro_db')
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- 1) ANA SAYFA API ---
@app.route('/api/home', methods=['GET'])
def home():
    # Test için varsayılan olarak ID'si 1 olan üyeyi baz alalım
    # Gerçek uygulamada bu bilgi giriş yapmış kullanıcıdan (session/token) gelir.
    member_id = request.args.get('member_id', 1) 
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Sonuçları sözlük (dict) olarak almak için
    
    response_data = {}

    try:
        # A. DOLULUK HESAPLAMA 
        # Önce kapasiteyi al
        cursor.execute("SELECT capacity FROM Gym LIMIT 1")
        capacity = cursor.fetchone()['capacity']

        # İçerideki kişi sayısı: (Girenler - Çıkanlar)
        # Not: Gerçek hayatta bu sorgu daha karmaşık olabilir (bugünün tarihi vb.)
        # Şimdilik toplam 'in' ve 'out' farkına bakıyoruz.
        cursor.execute("SELECT count(*) as cnt FROM TurnstileEvent WHERE direction='in'")
        total_in = cursor.fetchone()['cnt']
        
        cursor.execute("SELECT count(*) as cnt FROM TurnstileEvent WHERE direction='out'")
        total_out = cursor.fetchone()['cnt']
        
        people_inside = total_in - total_out
        # Eksiye düşerse 0 yap (Veri tutarsızlığı önlemi)
        people_inside = max(0, people_inside)
        
        occupancy_rate = 0
        if capacity > 0:
            occupancy_rate = (people_inside / capacity) * 100

        response_data['gym_status'] = {
            'people_inside': people_inside,
            'capacity': capacity,
            'occupancy_percentage': round(occupancy_rate, 1)
        }

        # B. SALONDAKİ HOCALAR 
        # is_in_gym = True olanları getir
        cursor.execute("SELECT name, specialty FROM Trainer WHERE is_in_gym = 1")
        active_trainers = cursor.fetchall()
        response_data['active_trainers'] = active_trainers

        # C. ÜYELİK ÖZETİ 
        # Bu üyenin aktif üyeliğini bul
        cursor.execute("""
            SELECT type, start_date, end_date, credit_total, credit_used 
            FROM Membership 
            WHERE member_id = %s AND is_active = 1 
            ORDER BY created_at DESC LIMIT 1
        """, (member_id,))
        
        membership = cursor.fetchone()
        
        if membership:
            summary = {}
            summary['type'] = membership['type']
            
            if membership['type'] == 'timed':
                # Kalan gün hesapla
                remaining_days = (membership['end_date'] - date.today()).days
                summary['info_text'] = f"{remaining_days} gün kaldı"
                summary['remaining'] = remaining_days
            else:
                # Kalan kontör hesapla
                remaining_credits = membership['credit_total'] - membership['credit_used']
                summary['info_text'] = f"{remaining_credits} giriş hakkı kaldı"
                summary['remaining'] = remaining_credits
            
            response_data['my_membership'] = summary
        else:
            response_data['my_membership'] = {'info_text': 'Aktif üyelik bulunamadı'}

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(response_data)

    # --- 2) HOCALAR MENÜSÜ ---
@app.route('/api/trainers', methods=['GET'])
def get_trainers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Tüm hocaları listele, puana göre sırala
        # is_in_gym bilgisini de frontend'de "Şu an salonda" etiketi için kullanacağız.
        cursor.execute("""
            SELECT trainer_id, name, specialty, is_in_gym, rating_avg 
            FROM Trainer 
            ORDER BY is_in_gym DESC, rating_avg DESC
        """)
        trainers = cursor.fetchall()
        return jsonify(trainers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 3) SABİT ANTRENMANLAR (LİSTE) ---
@app.route('/api/fixed-workouts', methods=['GET'])
def get_fixed_workouts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Sadece başlık ve süre bilgisini çekiyoruz (Listeleme ekranı için)
        cursor.execute("SELECT fixed_id, title, duration_min FROM FixedWorkout")
        workouts = cursor.fetchall()
        return jsonify(workouts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 3.1) SABİT ANTRENMAN DETAYI ---
@app.route('/api/fixed-workouts/<int:fixed_id>', methods=['GET'])
def get_fixed_workout_detail(fixed_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Önce antrenmanın temel bilgilerini al
        cursor.execute("SELECT * FROM FixedWorkout WHERE fixed_id = %s", (fixed_id,))
        workout = cursor.fetchone()
        
        if not workout:
            return jsonify({'error': 'Antrenman bulunamadı'}), 404
            
        # Şimdi bu antrenmana ait egzersizleri JOIN ile çek
        # FixedWorkoutExercise tablosunu Exercise tablosu ile birleştiriyoruz.
        sql_query = """
            SELECT 
                e.name as exercise_name, 
                e.muscle_group,
                fe.sets, 
                fe.reps, 
                fe.rest_sec, 
                fe.order_no
            FROM FixedWorkoutExercise fe
            JOIN Exercise e ON fe.exercise_id = e.exercise_id
            WHERE fe.fixed_id = %s
            ORDER BY fe.order_no ASC
        """
        cursor.execute(sql_query, (fixed_id,))
        exercises = cursor.fetchall()
        
        workout['exercises'] = exercises
        return jsonify(workout)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
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
        return jsonify({'message': 'Exercise added to routine'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/my-routines/<int:routine_id>/remove-exercise/<int:exercise_id>', methods=['DELETE'])
def remove_exercise_from_routine(routine_id, exercise_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM CustomRoutineExercise 
            WHERE routine_id = %s AND exercise_id = %s
        """, (routine_id, exercise_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Exercise not found in routine'}), 404
            
        return jsonify({'message': 'Exercise removed from routine'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/my-routines/<int:routine_id>', methods=['PUT'])
def update_routine(routine_id):
    data = request.get_json()
    title = data.get('title')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE CustomRoutine SET title = %s WHERE routine_id = %s
        """, (title, routine_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Routine not found'}), 404
            
        return jsonify({'message': 'Routine updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/my-routines/<int:routine_id>', methods=['DELETE'])
def delete_routine(routine_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM CustomRoutineExercise WHERE routine_id = %s", (routine_id,))
        cursor.execute("DELETE FROM CustomRoutine WHERE routine_id = %s", (routine_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Routine not found'}), 404
            
        return jsonify({'message': 'Routine deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    muscle_group = request.args.get('muscle_group')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if muscle_group:
            cursor.execute("""
                SELECT exercise_id, name, muscle_group 
                FROM Exercise 
                WHERE muscle_group = %s
                ORDER BY name
            """, (muscle_group,))
        else:
            cursor.execute("""
                SELECT exercise_id, name, muscle_group 
                FROM Exercise 
                ORDER BY muscle_group, name
            """)
        exercises = cursor.fetchall()
        return jsonify(exercises)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/muscle-groups', methods=['GET'])
def get_muscle_groups():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT muscle_group FROM Exercise ORDER BY muscle_group")
        groups = [row[0] for row in cursor.fetchall()]
        return jsonify(groups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)