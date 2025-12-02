from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from datetime import date
import os

app = Flask(__name__)
# CORS: Frontend (Web/Mobil) uygulamasının bu API'ye erişmesine izin verir.
CORS(app)

# --- VERİTABANI KONFİGÜRASYONU ---
# Ortam değişkenlerinden okur, yoksa varsayılanları kullanır.
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Halil_2003'), # Şifreniz
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'database': os.environ.get('DB_NAME', 'gympro_db')
}

def get_db_connection():
    """Veritabanı bağlantısı oluşturur ve döner."""
    return mysql.connector.connect(**DB_CONFIG)

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
    except mysql.connector.IntegrityError:
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
# 5. ADMIN PANELİ & İŞLETME YÖNETİMİ
# ==================================================================

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

@app.route('/api/admin/add-member', methods=['POST'])
def admin_add_membership():
    """
    SENARYO: Kullanıcı salona gelir. Admin kullanıcının e-postasını girer.
    Sistem kullanıcıyı bulur ve o salona üye yapar (Membership tablosuna kayıt atar).
    """
    data = request.get_json()
    gym_id = data.get('gym_id')
    user_email = data.get('email')
    
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
        cursor.execute("""
            INSERT INTO Membership (gym_id, member_id, type, start_date, is_active, credit_total)
            VALUES (%s, %s, %s, %s, 1, 30)
        """, (gym_id, member['member_id'], data.get('type', 'timed'), date.today()))
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