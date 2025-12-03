import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta, date

# --- AYARLAR ---
DB_CONFIG = {
  'user': 'root',
  'password': 'password',  # Kendi şifreni buraya yaz
  'host': '127.0.0.1',
  'database': 'gympro_db'
}

fake = Faker('tr_TR')

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def clean_tables(cursor):
    print("🧹 Eski veriler temizleniyor...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    tables = ["TurnstileEvent", "CustomRoutineExercise", "CustomRoutine", 
              "FixedWorkoutExercise", "FixedWorkout", "Membership", 
              "Member", "Trainer", "GymAdmin", "Gym", "Exercise"]
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("✅ Tablolar temizlendi.")

def populate_saas_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_tables(cursor)
    print("🚀 SaaS Veri Yüklemesi Başladı...")

    # ---------------------------------------------------------
    # 1. SPOR SALONLARI (Tenants)
    # ---------------------------------------------------------
    gyms = [
        ("ODTÜ Gym", "ODTÜ Kampüsü, Ankara", 200),
        ("Hacettepe Gym", "Beytepe Kampüsü, Ankara", 150),
        ("IronByte Crossfit", "Çankaya, Ankara", 80)
    ]
    gym_map = {} # {Name: ID} haritası
    
    for name, loc, cap in gyms:
        cursor.execute("INSERT INTO Gym (name, location, capacity) VALUES (%s, %s, %s)", (name, loc, cap))
        gym_map[name] = cursor.lastrowid
    
    print(f"✅ {len(gyms)} Spor Salonu oluşturuldu.")

    # ---------------------------------------------------------
    # 2. GYM ADMINLERİ
    # ---------------------------------------------------------
    admins = [
        (gym_map["ODTÜ Gym"], "odtu_admin", "admin123"),
        (gym_map["Hacettepe Gym"], "hacettepe_admin", "admin123"),
        (gym_map["IronByte Crossfit"], "iron_admin", "admin123")
    ]
    for gid, user, pw in admins:
        cursor.execute("INSERT INTO GymAdmin (gym_id, username, password) VALUES (%s, %s, %s)", (gid, user, pw))
    print("✅ Admin hesapları oluşturuldu.")

    # ---------------------------------------------------------
    # 3. GLOBAL EGZERSİZLER
    # ---------------------------------------------------------
    exercises = [
        ("Bench Press", "Chest"), ("Squat", "Legs"), ("Deadlift", "Back"),
        ("Overhead Press", "Shoulders"), ("Lat Pulldown", "Back"), ("Plank", "Core"),
        ("Bicep Curl", "Arms"), ("Tricep Pushdown", "Arms"), ("Leg Press", "Legs"),
        ("Rowing Machine", "Cardio"), ("Treadmill Run", "Cardio")
    ]
    ex_ids = {} # {Name: ID}
    for name, muscle in exercises:
        cursor.execute("INSERT INTO Exercise (name, muscle_group) VALUES (%s, %s)", (name, muscle))
        ex_ids[name] = cursor.lastrowid
    print("✅ Global egzersiz havuzu oluşturuldu.")

    # ---------------------------------------------------------
    # 4. SABİT ANTRENMANLAR (Hibrit: Global & Local)
    # ---------------------------------------------------------
    # A. Global (Herkes görür)
    cursor.execute("INSERT INTO FixedWorkout (gym_id, title, duration_min) VALUES (NULL, 'Full Body Başlangıç', 60)")
    fw_global_id = cursor.lastrowid
    # İçerik: Squat, Bench, Lat Pulldown
    for eid, order in [(ex_ids["Squat"], 1), (ex_ids["Bench Press"], 2), (ex_ids["Lat Pulldown"], 3)]:
        cursor.execute("INSERT INTO FixedWorkoutExercise VALUES (%s, %s, %s, 3, 10, 60)", (fw_global_id, eid, order))

    # B. ODTÜ Özel (Sadece ODTÜ üyeleri görür)
    cursor.execute("INSERT INTO FixedWorkout (gym_id, title, duration_min) VALUES (%s, 'ODTÜ Kürek Takımı Programı', 90)", (gym_map["ODTÜ Gym"],))
    fw_odtu_id = cursor.lastrowid
    cursor.execute("INSERT INTO FixedWorkoutExercise VALUES (%s, %s, 1, 4, 15, 60)", (fw_odtu_id, ex_ids["Rowing Machine"]))

    print("✅ Hibrit antrenmanlar (Global ve Salon Özel) eklendi.")

    # ---------------------------------------------------------
    # 5. TEST KULLANICISI (Senin İçin)
    # ---------------------------------------------------------
    # Bu kullanıcı ile login olup her şeyi test edebilirsin.
    test_user_email = "test@gympro.com"
    cursor.execute("""
        INSERT INTO Member (name, email, password, phone, gender, birth_date) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ("Ahmet Test", test_user_email, "123456", "5550000000", "M", "2003-01-01"))
    test_member_id = cursor.lastrowid

    # Ahmet'i hem ODTÜ'ye hem Hacettepe'ye üye yapalım (Multi-Membership Testi)
    # ODTÜ: Süreli Üyelik
    cursor.execute("""
        INSERT INTO Membership (gym_id, member_id, type, start_date, end_date, is_active)
        VALUES (%s, %s, 'timed', %s, %s, 1)
    """, (gym_map["ODTÜ Gym"], test_member_id, date.today(), date.today() + timedelta(days=90)))
    
    # Hacettepe: Kontörlü Üyelik
    cursor.execute("""
        INSERT INTO Membership (gym_id, member_id, type, start_date, credit_total, credit_used, is_active)
        VALUES (%s, %s, 'credit', %s, 20, 5, 1)
    """, (gym_map["Hacettepe Gym"], test_member_id, date.today()))

    print(f"✅ Test Kullanıcısı oluşturuldu: {test_user_email} / 123456")

    # ---------------------------------------------------------
    # 6. DİĞER ÜYELER VE TRAFİK
    # ---------------------------------------------------------
    member_ids = [test_member_id]
    
    # 50 Rastgele Üye Oluştur
    for _ in range(50):
        name = fake.name()
        email = f"{random.randint(10000,99999)}{fake.email()}"
        cursor.execute("INSERT INTO Member (name, email, password, gender, birth_date) VALUES (%s, %s, '123456', %s, %s)",
                       (name, email, random.choice(['M', 'F']), fake.date_of_birth(minimum_age=18, maximum_age=30)))
        member_ids.append(cursor.lastrowid)

    # Her Salon için Veri Üret
    for gym_name, gym_id in gym_map.items():
        # A. Hoca Ekle
        for _ in range(3):
            t_name = fake.name()
            cursor.execute("INSERT INTO Trainer (gym_id, name, specialty, is_in_gym, rating_avg) VALUES (%s, %s, 'Fitness', %s, 4.5)",
                           (gym_id, t_name, random.choice([0, 1])))
        
        # B. Üyelik Dağıt (Rastgele 30 kişiyi bu salona üye yap)
        salon_uyeleri = random.sample(member_ids, 30)
        for mid in salon_uyeleri:
            # Zaten üyeliği varsa atla (Test kullanıcısı için çakışma olmasın diye try-catch de olur ama basit tutalım)
            cursor.execute("SELECT membership_id FROM Membership WHERE gym_id=%s AND member_id=%s", (gym_id, mid))
            if cursor.fetchone(): continue

            m_type = random.choice(['timed', 'credit'])
            cursor.execute("""
                INSERT INTO Membership (gym_id, member_id, type, start_date, end_date, credit_total, is_active)
                VALUES (%s, %s, %s, %s, %s, 50, 1)
            """, (gym_id, mid, m_type, date.today()-timedelta(days=30), date.today()+timedelta(days=60)))

            # C. Turnike Verisi (Son 5 gün)
            # Sadece bu salona üye olanların bu salondaki hareketleri
            for day in range(5):
                if random.random() > 0.6: continue
                entry_time = datetime.now() - timedelta(days=day, hours=random.randint(1,10))
                
                cursor.execute("INSERT INTO TurnstileEvent (gym_id, member_id, ts, direction) VALUES (%s, %s, %s, 'in')",
                               (gym_id, mid, entry_time))
                
                # Çıkış
                exit_time = entry_time + timedelta(minutes=random.randint(45, 90))
                if exit_time < datetime.now():
                    cursor.execute("INSERT INTO TurnstileEvent (gym_id, member_id, ts, direction) VALUES (%s, %s, %s, 'out')",
                               (gym_id, mid, exit_time))

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 TÜM VERİLER BAŞARIYLA YÜKLENDİ! SaaS sistemi teste hazır.")

if __name__ == "__main__":
    populate_saas_data()