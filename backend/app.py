from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
from datetime import date
import os

app = Flask(__name__)
# CORS: Frontend (Web/Mobil) uygulamasının bu API'ye erişmesine izin verir.
CORS(app)

# --- VERİTABANI KONFİGÜRASYONU (ODBC) ---
# MySQL ODBC Driver kullanarak bağlantı
DB_CONFIG = {
    'driver': '{MySQL ODBC 9.5 Unicode Driver}',
    'server': os.environ.get('DB_HOST', '127.0.0.1'),
    'database': os.environ.get('DB_NAME', 'gympro_db'),
    'uid': os.environ.get('DB_USER', 'root'),
    'pwd': os.environ.get('DB_PASSWORD', 'Halil_2003')
}

class DictCursor:
    """pyodbc cursor'ı mysql.connector dictionary cursor gibi davranmasını sağlar"""
    def __init__(self, cursor):
        self._cursor = cursor
        self._columns = None
    
    def execute(self, sql, params=None):
        if params:
            # MySQL %s placeholder -> ODBC ? placeholder
            sql = sql.replace('%s', '?')
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        if self._cursor.description:
            self._columns = [column[0] for column in self._cursor.description]
        return self
    
    def fetchone(self):
        row = self._cursor.fetchone()
        if row and self._columns:
            return dict(zip(self._columns, row))
        return row
    
    def fetchall(self):
        rows = self._cursor.fetchall()
        if rows and self._columns:
            return [dict(zip(self._columns, row)) for row in rows]
        return rows
    
    def close(self):
        self._cursor.close()
    
    @property
    def lastrowid(self):
        self._cursor.execute("SELECT @@IDENTITY")
        result = self._cursor.fetchone()
        return result[0] if result else None
    
    @property
    def rowcount(self):
        return self._cursor.rowcount

class ConnectionWrapper:
    """pyodbc connection'ı mysql.connector gibi davranmasını sağlar"""
    def __init__(self, conn):
        self._conn = conn
    
    def cursor(self, dictionary=False):
        cursor = self._conn.cursor()
        if dictionary:
            return DictCursor(cursor)
        return cursor
    
    def commit(self):
        self._conn.commit()
    
    def close(self):
        self._conn.close()

def get_db_connection():
    """ODBC kullanarak veritabanı bağlantısı oluşturur ve döner."""
    connection_string = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['uid']};"
        f"PWD={DB_CONFIG['pwd']}"
    )
    conn = pyodbc.connect(connection_string)
    return ConnectionWrapper(conn)

# IntegrityError için pyodbc exception kullan
IntegrityError = pyodbc.IntegrityError

# ==================================================================
# 1. KİMLİK DOĞRULAMA (AUTHENTICATION) & KAYIT
# ==================================================================

@app.route('/api/register', methods=['POST'])
def register_app_user():
    """
    SENARYO: Kullanıcı mobil uygulamayı indirir ve sisteme 'Global Üye' olarak kaydolur.
    Henüz bir spor salonu üyeliği (Membership) yoktur.
    """
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Member (name, email, password) VALUES (%s, %s, %s)", 
                       (name, email, password))
        conn.commit()
        return jsonify({'message': 'Kullanıcı oluşturuldu. Şimdi bir spor salonuna gidip kaydınızı tamamlayın.'}), 201
    except IntegrityError:
        return jsonify({'error': 'Bu email zaten kayıtlı'}), 409
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """
    Kullanıcı email ve şifre ile giriş yapar. 
    Sistem member_id döner. Bu ID ile diğer işlemler yapılır.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Not: Prodüksiyon ortamında şifreler HASH (SHA-256 vb.) olarak saklanmalıdır.
        cursor.execute("SELECT member_id, name FROM Member WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            return jsonify({
                'message': 'Giriş başarılı',
                'member_id': user['member_id'],
                'name': user['name']
            }), 200
        else:
            return jsonify({'error': 'Hatalı email veya şifre'}), 401
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 2. ÜYELİK VE SALON SEÇİMİ (MULTI-TENANCY)
# ==================================================================

@app.route('/api/my-gyms', methods=['GET'])
def get_my_memberships():
    """
    SENARYO: Bir kullanıcının birden fazla spor salonunda üyeliği olabilir.
    Örn: Hem 'ODTÜ Gym' hem 'Hacettepe Gym'. Bu endpoint aktif üyelikleri listeler.
    """
    member_id = request.args.get('member_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT g.gym_id, g.name, g.location, m.type, m.is_active
            FROM Membership m
            JOIN Gym g ON m.gym_id = g.gym_id
            WHERE m.member_id = %s AND m.is_active = 1
        """, (member_id,))
        gyms = cursor.fetchall()
        return jsonify(gyms)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/gym/<int:gym_id>/dashboard', methods=['GET'])
def gym_dashboard(gym_id):
    """
    SEÇİLEN SALONUN DETAYLARI:
    Kullanıcı spesifik bir salona (gym_id) girdiğinde, sadece O SALONA AİT
    veriler (doluluk, oradaki hocalar, oradaki üyelik durumu) gösterilir.
    """
    member_id = request.args.get('member_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    response_data = {}

    try:
        # A. DOLULUK HESAPLAMA (Şube Bazlı Filtreleme: WHERE gym_id = ...)
        cursor.execute("SELECT capacity FROM Gym WHERE gym_id = %s", (gym_id,))
        gym_data = cursor.fetchone()
        
        if not gym_data:
            return jsonify({'error': 'Gym bulunamadı'}), 404
            
        capacity = gym_data['capacity']

        # Sadece seçilen şubenin turnike verilerini say
        cursor.execute("SELECT count(*) as cnt FROM TurnstileEvent WHERE gym_id = %s AND direction='in'", (gym_id,))
        total_in = cursor.fetchone()['cnt']
        
        cursor.execute("SELECT count(*) as cnt FROM TurnstileEvent WHERE gym_id = %s AND direction='out'", (gym_id,))
        total_out = cursor.fetchone()['cnt']
        
        people_inside = max(0, total_in - total_out)
        occupancy_rate = (people_inside / capacity) * 100 if capacity > 0 else 0

        response_data['gym_status'] = {
            'people_inside': people_inside,
            'capacity': capacity,
            'occupancy_percentage': round(occupancy_rate, 1)
        }

        # B. SALONDAKİ HOCALAR (Sadece o şubede çalışanlar)
        cursor.execute("""
            SELECT name, specialty, rating_avg 
            FROM Trainer 
            WHERE gym_id = %s AND is_in_gym = 1
        """, (gym_id,))
        response_data['active_trainers'] = cursor.fetchall()

        # C. KULLANICININ O ŞUBEDEKİ ÜYELİĞİ
        cursor.execute("""
            SELECT type, start_date, end_date, credit_total, credit_used 
            FROM Membership 
            WHERE member_id = %s AND gym_id = %s AND is_active = 1 
            LIMIT 1
        """, (member_id, gym_id))
        
        membership = cursor.fetchone()
        if membership:
            summary = {'type': membership['type']}
            if membership['type'] == 'timed':
                remaining = (membership['end_date'] - date.today()).days
                summary['info_text'] = f"{remaining} gün kaldı"
            else:
                remaining = membership['credit_total'] - membership['credit_used']
                summary['info_text'] = f"{remaining} giriş hakkı kaldı"
            response_data['my_membership'] = summary
        
        return jsonify(response_data)
        
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 3. ANTRENMAN YÖNETİMİ (HİBRİT İÇERİK MODELİ)
# ==================================================================

@app.route('/api/fixed-workouts', methods=['GET'])
def get_fixed_workouts():
    """
    SaaS MODELİ İÇERİK MANTIĞI:
    1. Global İçerik: gym_id IS NULL (Tüm salonlarda görünür)
    2. Local İçerik: gym_id = X (Sadece X salonunun üyeleri görür)
    """
    gym_id = request.args.get('gym_id') 
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if gym_id:
            # Hem globalleri hem de o salona özelleri getir
            query = "SELECT fixed_id, title, duration_min FROM FixedWorkout WHERE gym_id IS NULL OR gym_id = %s"
            cursor.execute(query, (gym_id,))
        else:
            # Salon seçilmediyse sadece globalleri getir
            cursor.execute("SELECT fixed_id, title, duration_min FROM FixedWorkout WHERE gym_id IS NULL")
            
        workouts = cursor.fetchall()
        return jsonify(workouts)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/fixed-workouts/<int:fixed_id>', methods=['GET'])
def get_fixed_workout_detail(fixed_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM FixedWorkout WHERE fixed_id = %s", (fixed_id,))
        workout = cursor.fetchone()
        if not workout: return jsonify({'error': 'Bulunamadı'}), 404

        # Programın egzersizlerini çek
        sql_query = """
            SELECT e.name, e.muscle_group, fe.sets, fe.reps, fe.rest_sec, fe.order_no
            FROM FixedWorkoutExercise fe
            JOIN Exercise e ON fe.exercise_id = e.exercise_id
            WHERE fe.fixed_id = %s ORDER BY fe.order_no ASC
        """
        cursor.execute(sql_query, (fixed_id,))
        workout['exercises'] = cursor.fetchall()
        return jsonify(workout)
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 4. KİŞİSEL RUTİNLER (ÜYEYE BAĞLI - PORTABLE DATA)
# ==================================================================

@app.route('/api/my-routines', methods=['GET'])
def get_my_routines():
    """Kullanıcının kendi oluşturduğu rutinleri listeler."""
    member_id = request.args.get('member_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT routine_id, title, created_at FROM CustomRoutine WHERE member_id = %s ORDER BY created_at DESC", (member_id,))
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines', methods=['POST'])
def create_routine():
    """Yeni kişisel rutin başlığı oluşturur."""
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO CustomRoutine (member_id, title) VALUES (%s, %s)", (data.get('member_id'), data.get('title')))
        conn.commit()
        return jsonify({'message': 'Rutin oluşturuldu', 'routine_id': cursor.lastrowid}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines/<int:routine_id>/add-exercise', methods=['POST'])
def add_exercise_to_routine(routine_id):
    """Rutine egzersiz ekler."""
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO CustomRoutineExercise (routine_id, exercise_id, sets, reps, rest_sec, order_no)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (routine_id, data.get('exercise_id'), data.get('sets'), data.get('reps'), data.get('rest_sec'), data.get('order_no')))
        conn.commit()
        return jsonify({'message': 'Egzersiz eklendi'}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines/<int:routine_id>', methods=['GET'])
def get_routine_detail(routine_id):
    """Kişisel rutinin detayını ve egzersizlerini getirir."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM CustomRoutine WHERE routine_id = %s", (routine_id,))
        routine = cursor.fetchone()
        if not routine: return jsonify({'error': 'Bulunamadı'}), 404
        
        cursor.execute("""
            SELECT e.name, cre.sets, cre.reps, cre.rest_sec, cre.order_no
            FROM CustomRoutineExercise cre
            JOIN Exercise e ON cre.exercise_id = e.exercise_id
            WHERE cre.routine_id = %s ORDER BY cre.order_no ASC
        """, (routine_id,))
        routine['exercises'] = cursor.fetchall()
        return jsonify(routine)
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 4.5 ANTRENÖR VE EGZERSİZ YÖNETİMİ
# ==================================================================

@app.route('/api/trainers', methods=['GET'])
def get_trainers():
    """
    Belirli bir salona ait antrenörleri listeler.
    gym_id parametresi ile filtrelenir.
    """
    gym_id = request.args.get('gym_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if gym_id:
            cursor.execute("""
                SELECT t.trainer_id, t.name, t.specialty, t.rating_avg, t.is_in_gym, t.member_id,
                       m.email as member_email
                FROM Trainer t
                LEFT JOIN Member m ON t.member_id = m.member_id
                WHERE t.gym_id = %s
                ORDER BY t.rating_avg DESC
            """, (gym_id,))
        else:
            # gym_id yoksa tüm antrenörleri getir (admin kullanımı için)
            cursor.execute("""
                SELECT t.trainer_id, t.name, t.specialty, t.rating_avg, t.is_in_gym, t.member_id,
                       g.name as gym_name, m.email as member_email
                FROM Trainer t
                LEFT JOIN Gym g ON t.gym_id = g.gym_id
                LEFT JOIN Member m ON t.member_id = m.member_id
                ORDER BY t.rating_avg DESC
            """)
        
        trainers = cursor.fetchall()
        return jsonify(trainers)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """
    Tüm egzersizleri listeler.
    muscle_group parametresi ile filtrelenebilir.
    """
    muscle_group = request.args.get('muscle_group')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if muscle_group:
            cursor.execute("""
                SELECT exercise_id, name, muscle_group  
                FROM Exercise 
                WHERE muscle_group = %s
                ORDER BY name ASC
            """, (muscle_group,))
        else:
            cursor.execute("""
                SELECT exercise_id, name, muscle_group  
                FROM Exercise 
                ORDER BY muscle_group, name ASC
            """)
        
        exercises = cursor.fetchall()
        return jsonify(exercises)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/muscle-groups', methods=['GET'])
def get_muscle_groups():
    """
    Sistemdeki tüm kas gruplarını listeler.
    Egzersiz ekleme/filtreleme ekranlarında kullanılır.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT muscle_group FROM Exercise ORDER BY muscle_group")
        muscle_groups = [row[0] for row in cursor.fetchall()]
        return jsonify(muscle_groups)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines/<int:routine_id>', methods=['PUT'])
def update_routine(routine_id):
    """Kişisel rutinin başlığını günceller."""
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE CustomRoutine SET title = %s WHERE routine_id = %s", 
                       (data.get('title'), routine_id))
        conn.commit()
        return jsonify({'message': 'Rutin güncellendi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines/<int:routine_id>', methods=['DELETE'])
def delete_routine(routine_id):
    """Kişisel rutini siler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Önce rutine ait egzersizleri sil
        cursor.execute("DELETE FROM CustomRoutineExercise WHERE routine_id = %s", (routine_id,))
        # Sonra rutini sil
        cursor.execute("DELETE FROM CustomRoutine WHERE routine_id = %s", (routine_id,))
        conn.commit()
        return jsonify({'message': 'Rutin silindi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my-routines/<int:routine_id>/remove-exercise/<int:exercise_id>', methods=['DELETE'])
def remove_exercise_from_routine(routine_id, exercise_id):
    """Rutinden egzersiz çıkarır."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM CustomRoutineExercise WHERE routine_id = %s AND exercise_id = %s", 
                       (routine_id, exercise_id))
        conn.commit()
        return jsonify({'message': 'Egzersiz kaldırıldı'})
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 5. ADMIN PANELİ & İŞLETME YÖNETİMİ
# ==================================================================

@app.route('/api/gyms/<int:gym_id>', methods=['GET'])
def get_gym_info(gym_id):
    """Salon bilgilerini getirir."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT gym_id, name, location, capacity FROM Gym WHERE gym_id = %s", (gym_id,))
        gym = cursor.fetchone()
        if not gym:
            return jsonify({'error': 'Salon bulunamadı'}), 404
        return jsonify(gym)
    finally:
        cursor.close()
        conn.close()

# ==================================================================
# 6. TURNİKE YÖNETİMİ (GİRİŞ/ÇIKIŞ)
# ==================================================================

@app.route('/api/turnstile/checkin', methods=['POST'])
def turnstile_checkin():
    """
    Salona giriş kaydı oluşturur.
    Turnike QR okutulduğunda çağrılır.
    Eğer üye aynı zamanda trainer ise, trainer'ın is_in_gym durumunu da günceller.
    """
    data = request.get_json()
    member_id = data.get('member_id')
    gym_id = data.get('gym_id')
    
    if not member_id or not gym_id:
        return jsonify({'error': 'member_id ve gym_id zorunludur'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Üyelik kontrolü
        cursor.execute("""
            SELECT membership_id, type, credit_total, credit_used 
            FROM Membership 
            WHERE member_id = %s AND gym_id = %s AND is_active = 1
        """, (member_id, gym_id))
        membership = cursor.fetchone()
        
        if not membership:
            return jsonify({'error': 'Aktif üyelik bulunamadı'}), 403
        
        # Kredili üyelikse kontrol et
        if membership['type'] == 'credit':
            remaining = membership['credit_total'] - membership['credit_used']
            if remaining <= 0:
                return jsonify({'error': 'Giriş hakkınız kalmadı'}), 403
            
            # Kredi kullan
            cursor.execute("""
                UPDATE Membership SET credit_used = credit_used + 1 
                WHERE membership_id = %s
            """, (membership['membership_id'],))
        
        # Giriş kaydı oluştur
        cursor.execute("""
            INSERT INTO TurnstileEvent (gym_id, member_id, direction, event_time)
            VALUES (%s, %s, 'in', NOW())
        """, (gym_id, member_id))
        
        # Üye aynı zamanda trainer mı kontrol et ve is_in_gym güncelle
        cursor.execute("""
            SELECT trainer_id FROM Trainer 
            WHERE member_id = %s AND gym_id = %s
        """, (member_id, gym_id))
        trainer = cursor.fetchone()
        
        is_trainer = False
        if trainer:
            is_trainer = True
            cursor.execute("""
                UPDATE Trainer SET is_in_gym = TRUE 
                WHERE trainer_id = %s
            """, (trainer['trainer_id'],))
        
        conn.commit()
        
        if is_trainer:
            return jsonify({'message': 'Giriş başarılı! Hoş geldiniz, Antrenör!', 'is_trainer': True}), 201
        return jsonify({'message': 'Giriş başarılı! Hoş geldiniz.', 'is_trainer': False}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/turnstile/checkout', methods=['POST'])
def turnstile_checkout():
    """
    Salondan çıkış kaydı oluşturur.
    Turnike QR okutulduğunda çağrılır.
    Eğer üye aynı zamanda trainer ise, trainer'ın is_in_gym durumunu da günceller.
    """
    data = request.get_json()
    member_id = data.get('member_id')
    gym_id = data.get('gym_id')
    
    if not member_id or not gym_id:
        return jsonify({'error': 'member_id ve gym_id zorunludur'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Çıkış kaydı oluştur
        cursor.execute("""
            INSERT INTO TurnstileEvent (gym_id, member_id, direction, event_time)
            VALUES (%s, %s, 'out', NOW())
        """, (gym_id, member_id))
        
        # Üye aynı zamanda trainer mı kontrol et ve is_in_gym güncelle
        cursor.execute("""
            SELECT trainer_id FROM Trainer 
            WHERE member_id = %s AND gym_id = %s
        """, (member_id, gym_id))
        trainer = cursor.fetchone()
        
        is_trainer = False
        if trainer:
            is_trainer = True
            cursor.execute("""
                UPDATE Trainer SET is_in_gym = FALSE 
                WHERE trainer_id = %s
            """, (trainer['trainer_id'],))
        
        conn.commit()
        
        if is_trainer:
            return jsonify({'message': 'Çıkış başarılı! Görüşmek üzere, Antrenör!', 'is_trainer': True}), 201
        return jsonify({'message': 'Çıkış başarılı! Görüşmek üzere.', 'is_trainer': False}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/gym/<int:gym_id>/stats', methods=['GET'])
def get_gym_stats(gym_id):
    """
    Admin Dashboard için salon istatistiklerini döner.
    Toplam üye, aktif üye, içerideki kişi sayısı, doluluk oranı.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Salon kapasitesi
        cursor.execute("SELECT capacity FROM Gym WHERE gym_id = %s", (gym_id,))
        gym = cursor.fetchone()
        if not gym:
            return jsonify({'error': 'Salon bulunamadı'}), 404
        capacity = gym['capacity']

        # Toplam üye sayısı (bu salona kayıtlı)
        cursor.execute("SELECT COUNT(*) as cnt FROM Membership WHERE gym_id = %s", (gym_id,))
        total_members = cursor.fetchone()['cnt']

        # Aktif üye sayısı
        cursor.execute("SELECT COUNT(*) as cnt FROM Membership WHERE gym_id = %s AND is_active = 1", (gym_id,))
        active_members = cursor.fetchone()['cnt']

        # İçerideki kişi sayısı (turnike verileri)
        cursor.execute("SELECT COUNT(*) as cnt FROM TurnstileEvent WHERE gym_id = %s AND direction = 'in'", (gym_id,))
        total_in = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM TurnstileEvent WHERE gym_id = %s AND direction = 'out'", (gym_id,))
        total_out = cursor.fetchone()['cnt']
        people_inside = max(0, total_in - total_out)

        # Doluluk oranı
        occupancy_percentage = round((people_inside / capacity) * 100, 1) if capacity > 0 else 0

        return jsonify({
            'total_members': total_members,
            'active_members': active_members,
            'people_inside': people_inside,
            'capacity': capacity,
            'occupancy_percentage': occupancy_percentage
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/gym/<int:gym_id>/members', methods=['GET'])
def get_gym_members(gym_id):
    """
    Salona kayıtlı tüm üyeleri listeler.
    Üyelik bilgileri ve kalan süre/bakiye ile birlikte.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                m.member_id, m.name, m.email,
                ms.membership_id, ms.type, ms.is_active,
                ms.start_date, ms.end_date,
                ms.credit_total, ms.credit_used,
                CASE 
                    WHEN ms.type = 'timed' THEN DATEDIFF(ms.end_date, CURDATE())
                    ELSE NULL
                END as remaining_days,
                CASE 
                    WHEN ms.type = 'credit' THEN (ms.credit_total - ms.credit_used)
                    ELSE NULL
                END as remaining_credits
            FROM Membership ms
            JOIN Member m ON ms.member_id = m.member_id
            WHERE ms.gym_id = %s
            ORDER BY ms.start_date DESC
        """, (gym_id,))
        members = cursor.fetchall()
        return jsonify(members)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/membership/<int:membership_id>/add-credit', methods=['POST'])
def add_credit_to_membership(membership_id):
    """
    Üyeliğe bakiye veya süre ekler.
    Süreli üyelik için gün, kredili üyelik için giriş hakkı eklenir.
    """
    data = request.get_json()
    amount = data.get('amount', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Üyelik bilgisini al
        cursor.execute("SELECT type, end_date, credit_total FROM Membership WHERE membership_id = %s", (membership_id,))
        membership = cursor.fetchone()
        
        if not membership:
            return jsonify({'error': 'Üyelik bulunamadı'}), 404
        
        if membership['type'] == 'timed':
            # Süreli üyelik: end_date'e gün ekle
            cursor.execute("""
                UPDATE Membership 
                SET end_date = DATE_ADD(COALESCE(end_date, CURDATE()), INTERVAL %s DAY),
                    is_active = 1
                WHERE membership_id = %s
            """, (amount, membership_id))
        else:
            # Kredili üyelik: credit_total'a ekle
            cursor.execute("""
                UPDATE Membership 
                SET credit_total = credit_total + %s,
                    is_active = 1
                WHERE membership_id = %s
            """, (amount, membership_id))
        
        conn.commit()
        return jsonify({'message': f'{amount} birim eklendi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """
    Spor Salonu Yöneticisi Girişi.
    Her salonun kendi admin hesabı vardır (GymAdmin tablosu).
    """
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT admin_id, gym_id FROM GymAdmin WHERE username=%s AND password=%s", 
                       (data.get('username'), data.get('password')))
        admin = cursor.fetchone()
        if admin:
            return jsonify({'message': 'Admin girişi başarılı', 'gym_id': admin['gym_id']})
        return jsonify({'error': 'Yetkisiz erişim'}), 401
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/membership/<int:membership_id>', methods=['PUT'])
def update_membership(membership_id):
    """
    Üyelik bilgilerini günceller.
    Üyelik tipi, aktiflik durumu, süre veya kredi güncellenebilir.
    """
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Mevcut üyeliği kontrol et
        cursor.execute("SELECT * FROM Membership WHERE membership_id = %s", (membership_id,))
        membership = cursor.fetchone()
        if not membership:
            return jsonify({'error': 'Üyelik bulunamadı'}), 404
        
        # Güncellenecek alanlar
        membership_type = data.get('type', membership['type'])
        is_active = data.get('is_active', membership['is_active'])
        
        if membership_type == 'timed':
            days = data.get('days')
            if days:
                from datetime import timedelta
                end_date = date.today() + timedelta(days=int(days))
                cursor.execute("""
                    UPDATE Membership 
                    SET type = %s, is_active = %s, end_date = %s
                    WHERE membership_id = %s
                """, (membership_type, is_active, end_date, membership_id))
            else:
                cursor.execute("""
                    UPDATE Membership 
                    SET type = %s, is_active = %s
                    WHERE membership_id = %s
                """, (membership_type, is_active, membership_id))
        else:
            credits = data.get('credits')
            if credits:
                cursor.execute("""
                    UPDATE Membership 
                    SET type = %s, is_active = %s, credit_total = %s
                    WHERE membership_id = %s
                """, (membership_type, is_active, credits, membership_id))
            else:
                cursor.execute("""
                    UPDATE Membership 
                    SET type = %s, is_active = %s
                    WHERE membership_id = %s
                """, (membership_type, is_active, membership_id))
        
        conn.commit()
        return jsonify({'message': 'Üyelik güncellendi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/membership/<int:membership_id>', methods=['DELETE'])
def delete_membership(membership_id):
    """
    Üyeliği siler.
    Dikkat: Bu işlem geri alınamaz.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Membership WHERE membership_id = %s", (membership_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Üyelik bulunamadı'}), 404
        return jsonify({'message': 'Üyelik silindi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/trainers', methods=['POST'])
def add_trainer():
    """
    Salona yeni antrenör ekler.
    member_id verilirse mevcut bir üyeyi trainer yapar.
    """
    data = request.get_json()
    gym_id = data.get('gym_id')
    name = data.get('name')
    specialty = data.get('specialty')
    member_id = data.get('member_id')  # Opsiyonel - mevcut üyeyi trainer yapmak için
    
    if not gym_id or not name:
        return jsonify({'error': 'gym_id ve name zorunludur'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # member_id verildiyse, bu üyenin var olduğunu kontrol et
        if member_id:
            cursor.execute("""
                SELECT m.member_id, m.name FROM Member m
                JOIN Membership ms ON m.member_id = ms.member_id
                WHERE m.member_id = %s AND ms.gym_id = %s AND ms.is_active = 1
            """, (member_id, gym_id))
            member = cursor.fetchone()
            if not member:
                return jsonify({'error': 'Bu salonda aktif üyeliği olan bir üye bulunamadı'}), 404
            
            # Zaten trainer mı kontrol et
            cursor.execute("""
                SELECT trainer_id FROM Trainer WHERE member_id = %s AND gym_id = %s
            """, (member_id, gym_id))
            existing = cursor.fetchone()
            if existing:
                return jsonify({'error': 'Bu üye zaten bu salonda antrenör'}), 400
        
        cursor.execute("""
            INSERT INTO Trainer (gym_id, member_id, name, specialty, rating_avg, is_in_gym)
            VALUES (%s, %s, %s, %s, 0.0, 0)
        """, (gym_id, member_id, name, specialty))
        conn.commit()
        return jsonify({'message': 'Antrenör eklendi', 'trainer_id': cursor.lastrowid}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/trainers/<int:trainer_id>', methods=['PUT'])
def update_trainer(trainer_id):
    """
    Antrenör bilgilerini günceller.
    member_id ile üye bağlantısını da güncelleyebilir.
    """
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Trainer WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        if not trainer:
            return jsonify({'error': 'Antrenör bulunamadı'}), 404
        
        name = data.get('name', trainer['name'])
        specialty = data.get('specialty', trainer['specialty'])
        is_in_gym = data.get('is_in_gym', trainer['is_in_gym'])
        member_id = data.get('member_id', trainer['member_id'])
        
        # member_id değiştirildiyse ve None değilse, üyeyi kontrol et
        if member_id and member_id != trainer['member_id']:
            cursor.execute("""
                SELECT m.member_id FROM Member m
                JOIN Membership ms ON m.member_id = ms.member_id
                WHERE m.member_id = %s AND ms.gym_id = %s AND ms.is_active = 1
            """, (member_id, trainer['gym_id']))
            member = cursor.fetchone()
            if not member:
                return jsonify({'error': 'Bu salonda aktif üyeliği olan bir üye bulunamadı'}), 404
        
        cursor.execute("""
            UPDATE Trainer 
            SET name = %s, specialty = %s, is_in_gym = %s, member_id = %s
            WHERE trainer_id = %s
        """, (name, specialty, is_in_gym, member_id, trainer_id))
        conn.commit()
        return jsonify({'message': 'Antrenör güncellendi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/trainers/<int:trainer_id>', methods=['DELETE'])
def delete_trainer(trainer_id):
    """
    Antrenörü siler.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Trainer WHERE trainer_id = %s", (trainer_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Antrenör bulunamadı'}), 404
        return jsonify({'message': 'Antrenör silindi'})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/trainers/<int:trainer_id>/toggle', methods=['PUT'])
def toggle_trainer_status(trainer_id):
    """
    Antrenörün salonda olup olmadığını değiştirir.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT is_in_gym FROM Trainer WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        if not trainer:
            return jsonify({'error': 'Antrenör bulunamadı'}), 404
        
        new_status = 0 if trainer['is_in_gym'] == 1 else 1
        cursor.execute("UPDATE Trainer SET is_in_gym = %s WHERE trainer_id = %s", (new_status, trainer_id))
        conn.commit()
        return jsonify({'message': 'Durum güncellendi', 'is_in_gym': new_status})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/add-member', methods=['POST'])
def admin_add_membership():
    """
    SENARYO: Kullanıcı salona gelir. Admin kullanıcının e-postasını girer.
    Sistem kullanıcıyı bulur ve o salona üye yapar (Membership tablosuna kayıt atar).
    """
    data = request.get_json()
    gym_id = data.get('gym_id')
    user_email = data.get('email')
    membership_type = data.get('type', 'timed')
    days = data.get('days', 30)  # Varsayılan 30 gün
    credits = data.get('credits', 30)  # Varsayılan 30 giriş
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Kullanıcı var mı?
        cursor.execute("SELECT member_id FROM Member WHERE email = %s", (user_email,))
        member = cursor.fetchone()
        if not member:
            return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen önce uygulamadan kayıt olun.'}), 404
            
        # 2. Zaten üye mi?
        cursor.execute("SELECT membership_id FROM Membership WHERE member_id=%s AND gym_id=%s AND is_active=1", (member['member_id'], gym_id))
        if cursor.fetchone():
             return jsonify({'error': 'Kullanıcı zaten salonunuza üye.'}), 409

        # 3. Üyeliği Ekle
        if membership_type == 'timed':
            from datetime import timedelta
            end_date = date.today() + timedelta(days=days)
            cursor.execute("""
                INSERT INTO Membership (gym_id, member_id, type, start_date, end_date, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (gym_id, member['member_id'], 'timed', date.today(), end_date))
        else:
            cursor.execute("""
                INSERT INTO Membership (gym_id, member_id, type, start_date, is_active, credit_total, credit_used)
                VALUES (%s, %s, %s, %s, 1, %s, 0)
            """, (gym_id, member['member_id'], 'credit', date.today(), credits))
        
        conn.commit()
        return jsonify({'message': f'{user_email} başarıyla kaydedildi.'}), 201
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    """
    1. Proje Vizyonu: GymPro SaaS Platformu
Bu proje, tek bir spor salonunu yönetmek yerine, Software as a Service (SaaS) modeliyle çalışan, çok şubeli ve merkezi bir fitness yönetim platformudur. Geleneksel "her salonun kendi veritabanı olsun" mantığı yerine, Multi-Tenant (Çok Kiracılı) veritabanı mimarisi kullanılmıştır.

2. Temel Aktörler ve Roller
Global Member (Uygulama Kullanıcısı): Platformda tek bir hesabı vardır. Bu hesapla hem Ankara'daki ODTÜ Gym'e hem de İstanbul'daki başka bir Gym'e üye olabilir. Verileri (rutinleri) onunla beraber taşınır.

Gym Admin (Salon Yöneticisi): Bir spor salonunun yetkilisidir. Sadece kendi şubesine ait verileri (kendi üyeleri, kendi doluluk oranı, kendi cirosu) görebilir. Diğer salonların verilerine erişemez.

3. Kritik Kullanım Senaryoları
A. Kayıt ve Üyelik Akışı (Onboarding Flow)

Kullanıcı: Uygulamayı indirir, email/password ile kayıt olur (/api/register). Şu an hiçbir salonun üyesi değildir, "Free User" modundadır.

Etkileşim: Kullanıcı fiziksel olarak bir salona (Örn: ODTÜ Gym) gider.

Admin: Gym Admin paneline girer, kullanıcının mail adresini sisteme yazar (/api/admin/add-member).

Sonuç: Sistem, Membership tablosunda o kullanıcı ile o salonu birbirine bağlar. Kullanıcının uygulamasında "ODTÜ Gym" sekmesi aktif olur.

B. Hibrit İçerik Yönetimi (Global vs. Local Content) Sistem, antrenman programlarını akıllı bir şekilde filtreler:

Global İçerik: Sistem tarafından sunulan standart programlar (Örn: Full Body, PPL). Bunlar FixedWorkout tablosunda gym_id = NULL olarak saklanır ve herkese açıktır.

Local İçerik: Salonların kendi üyelerine özel hazırladığı programlar (Örn: "ODTÜ Kürek Takımı Programı"). Bunlar gym_id = 1 olarak saklanır.

Algoritma: Kullanıcı antrenman listesini açtığında sistem şu sorguyu çalıştırır: "Herkese açık olanları GETİR + Benim üye olduğum salonunkileri GETİR."

C. Veri İzolasyonu ve Doluluk Takibi Turnike sistemi (TurnstileEvent), veriyi kaydederken mutlaka gym_id etiketini kullanır.

Ahmet ODTÜ Gym'e girdiğinde, bu sadece ODTÜ Gym'in doluluk oranını artırır.

Bu sayede sistem, binlerce salonu tek bir veritabanında yönetirken verilerin birbirine karışmasını engeller.

4. Teknik Mimari
Backend: Python Flask (REST API)

Database: MySQL (İlişkisel Yapı + Foreign Key Constraints)

Özellikler:

Data Integrity: Bir salon silindiğinde (CASCADE), ona ait üyeliklerin ve logların nasıl yönetileceği veritabanı seviyesinde planlanmıştır.

Scalability: Yeni bir şube açıldığında kod değiştirmeye gerek yoktur; sadece Gym tablosuna bir satır eklenir.
    """
    app.run(host='0.0.0.0', port=5000, debug=True)