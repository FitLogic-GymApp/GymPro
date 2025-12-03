import mysql.connector
import random
from datetime import datetime, timedelta, date
import os

# --- AYARLAR ---
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Halil_2003'), # Şifreni kontrol et
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'database': os.environ.get('DB_NAME', 'gympro_db')
}

# --- İSİM HAVUZLARI (TÜİK Verilerine Yakın) ---
MALE_NAMES = [
    "Mehmet", "Mustafa", "Ahmet", "Ali", "Hüseyin", "Hasan", "İbrahim", "İsmail", "Osman", "Yusuf",
    "Murat", "Ömer", "Ramazan", "Halil", "Süleyman", "Abdullah", "Mahmut", "Salih", "Recep", "Fatih",
    "Kadir", "Emre", "Hakan", "Adem", "Kemal", "Yaşar", "Bekir", "Musa", "Metin", "Bayram",
    "Serkan", "Orhan", "Burak", "Furkan", "Gökhan", "Uğur", "Yakup", "Muhammed", "Yunus", "Cemal",
    "Mevlüt", "Sinan", "Enes", "Volkan", "İlhan", "Serdar", "Yasin", "Bünyamin", "Arda", "Efe"
]

FEMALE_NAMES = [
    "Fatma", "Ayşe", "Emine", "Hatice", "Zeynep", "Elif", "Meryem", "Şerife", "Sultan", "Zehra",
    "Hanife", "Merve", "Havva", "Zeliha", "Esra", "Fadime", "Özlem", "Hacer", "Yasemin", "Hülya",
    "Cemile", "Sevim", "Gülsüm", "Leyla", "Dilek", "Büşra", "Aysel", "Songül", "Kübra", "Halime",
    "Rabia", "Aynur", "Tuğba", "Arzu", "Sakine", "Melek", "Asiye", "Sibel", "Filiz", "Gülten",
    "Seda", "Seher", "Yeter", "Nermin", "Gülcan", "Kadriye", "Birsen", "Derya", "Ebru", "Gamze"
]

SURNAMES = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
    "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek",
    "Polat", "Özcan", "Korkmaz", "Çakır", "Erdoğan", "Yavuz", "Can", "Acar", "Şen", "Aktaş",
    "Güler", "Yalçın", "Güneş", "Bozkurt", "Bulut", "Keskin", "Ünal", "Turan", "Gül", "Özer",
    "Işık", "Kaplan", "Avcı", "Sarı", "Tekin", "Taş", "Köse", "Yüksel", "Ateş", "Aksoy"
]

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def tr_to_en(text):
    """Türkçe karakterleri İngilizce karşılıklarına çevirir (Email için)"""
    mapping = {
        'ş':'s', 'ı':'i', 'ğ':'g', 'ü':'u', 'ö':'o', 'ç':'c',
        'Ş':'S', 'İ':'I', 'Ğ':'G', 'Ü':'U', 'Ö':'O', 'Ç':'C'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text

def random_date_of_birth(min_age=18, max_age=50):
    today = date.today()
    start_date = today - timedelta(days=max_age*365)
    end_date = today - timedelta(days=min_age*365)
    random_days = random.randint(0, (end_date - start_date).days)
    return start_date + timedelta(days=random_days)

def clean_tables(cursor):
    print("🧹 Eski veriler temizleniyor...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    tables = [
        "TurnstileEvent", "CustomRoutineExercise", "CustomRoutine", 
        "FixedWorkoutExercise", "FixedWorkout", "Membership", 
        "Member", "Trainer", "GymAdmin", "Gym", "Exercise"
    ]
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table}")
        except mysql.connector.Error as err:
            print(f"Uyarı: {table} temizlenemedi: {err}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("✅ Tablolar temizlendi.")

def populate_saas_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        clean_tables(cursor)
        print("🚀 Veri Yükleme Başladı (Gerçekçi İsimler)...")

        # ---------------------------------------------------------
        # 1. SPOR SALONLARI
        # ---------------------------------------------------------
        gyms = [
            ("FitZone Kadıköy", "Kadıköy, İstanbul", 150),
            ("PowerGym Beşiktaş", "Beşiktaş, İstanbul", 120),
            ("IronByte Crossfit", "Çankaya, Ankara", 80),
            ("Ege Fitness", "Bornova, İzmir", 200)
        ]
        gym_map = {} 
        
        for name, loc, cap in gyms:
            cursor.execute("INSERT INTO Gym (name, location, capacity) VALUES (%s, %s, %s)", (name, loc, cap))
            gym_map[name] = cursor.lastrowid
        
        print(f"✅ {len(gyms)} Spor Salonu oluşturuldu.")

        # ---------------------------------------------------------
        # 2. GYM ADMINLERİ
        # ---------------------------------------------------------
        for gym_name, gym_id in gym_map.items():
            username = gym_name.split()[0].lower() + "_admin"
            cursor.execute("INSERT INTO GymAdmin (gym_id, username, password) VALUES (%s, %s, %s)", 
                           (gym_id, username, "admin123"))
        print("✅ Salon Yöneticileri oluşturuldu.")

        # ---------------------------------------------------------
        # 3. GLOBAL EGZERSİZLER
        # ---------------------------------------------------------
        exercises = [
            ("Bench Press", "Chest"), ("Squat", "Legs"), ("Deadlift", "Back"),
            ("Overhead Press", "Shoulders"), ("Lat Pulldown", "Back"), ("Plank", "Core"),
            ("Bicep Curl", "Arms"), ("Tricep Pushdown", "Arms"), ("Leg Press", "Legs"),
            ("Rowing Machine", "Cardio"), ("Treadmill Run", "Cardio"), ("Pull Up", "Back"),
            ("Dips", "Arms"), ("Lunges", "Legs"), ("Face Pull", "Shoulders")
        ]
        ex_ids_list = []
        ex_ids_map = {}
        
        for name, muscle in exercises:
            cursor.execute("INSERT INTO Exercise (name, muscle_group) VALUES (%s, %s)", (name, muscle))
            new_id = cursor.lastrowid
            ex_ids_list.append(new_id)
            ex_ids_map[name] = new_id
            
        print("✅ Egzersiz havuzu oluşturuldu.")

        # ---------------------------------------------------------
        # 4. SABİT ANTRENMANLAR
        # ---------------------------------------------------------
        global_workouts = [
            ("Full Body Beginner", 60, ["Squat", "Bench Press", "Lat Pulldown", "Overhead Press", "Plank"]),
            ("Upper Body Power", 75, ["Bench Press", "Rowing Machine", "Overhead Press", "Bicep Curl", "Tricep Pushdown"])
        ]
        
        for title, duration, ex_list in global_workouts:
            cursor.execute("INSERT INTO FixedWorkout (gym_id, title, duration_min) VALUES (NULL, %s, %s)", (title, duration))
            fw_id = cursor.lastrowid
            for i, ex_name in enumerate(ex_list):
                if ex_name in ex_ids_map:
                    cursor.execute("INSERT INTO FixedWorkoutExercise (fixed_id, exercise_id, order_no, sets, reps, rest_sec) VALUES (%s, %s, %s, 3, 10, 60)", 
                                   (fw_id, ex_ids_map[ex_name], i+1))

        # Local Workout (IronByte)
        iron_id = gym_map.get("IronByte Crossfit")
        if iron_id:
            cursor.execute("INSERT INTO FixedWorkout (gym_id, title, duration_min) VALUES (%s, 'WOD: Murph Prep', 45)", (iron_id,))
            wod_id = cursor.lastrowid
            cursor.execute("INSERT INTO FixedWorkoutExercise (fixed_id, exercise_id, order_no, sets, reps, rest_sec) VALUES (%s, %s, 1, 5, 20, 0)", 
                           (wod_id, ex_ids_map["Pull Up"]))

        print("✅ Sabit Antrenmanlar eklendi.")

        # ---------------------------------------------------------
        # 5. TEST KULLANICISI
        # ---------------------------------------------------------
        test_user_email = "test@test.com"
        cursor.execute("""
            INSERT INTO Member (name, email, password, phone, gender, birth_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("Test Kullanıcı", test_user_email, "123456", "5550000000", "M", "2000-01-01"))
        test_member_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Membership (gym_id, member_id, type, start_date, end_date, is_active)
            VALUES (%s, %s, 'timed', %s, %s, 1)
        """, (gym_map["FitZone Kadıköy"], test_member_id, date.today(), date.today() + timedelta(days=365)))
        
        cursor.execute("""
            INSERT INTO Membership (gym_id, member_id, type, start_date, credit_total, credit_used, is_active)
            VALUES (%s, %s, 'credit', %s, 50, 12, 1)
        """, (gym_map["PowerGym Beşiktaş"], test_member_id, date.today()))

        print(f"✅ Test Kullanıcısı oluşturuldu: {test_user_email} / 123456")

        # ---------------------------------------------------------
        # 6. DİĞER ÜYELER & ÜYELİKLER
        # ---------------------------------------------------------
        member_ids = [test_member_id]
        
        # 120 Rastgele Üye (İsim Havuzundan)
        for _ in range(120):
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                fname = random.choice(MALE_NAMES)
            else:
                fname = random.choice(FEMALE_NAMES)
            lname = random.choice(SURNAMES)
            
            full_name = f"{fname} {lname}"
            # Email oluştur: ahmet.yilmaz.45@example.com gibi
            clean_fname = tr_to_en(fname.lower())
            clean_lname = tr_to_en(lname.lower())
            email = f"{clean_fname}.{clean_lname}.{random.randint(100,999)}@example.com"
            
            phone = f"05{random.choice(['32','33','42','43','55','05','06','07'])}{random.randint(1000000, 9999999)}"
            birth_date = random_date_of_birth()

            # Unique email kontrolü gerekebilir ama random sayı ile ihtimali düşürdük
            try:
                cursor.execute("INSERT INTO Member (name, email, password, phone, gender, birth_date) VALUES (%s, %s, '123456', %s, %s, %s)",
                            (full_name, email, phone, gender, birth_date))
                member_ids.append(cursor.lastrowid)
            except mysql.connector.Error:
                pass # Email çakışırsa atla

        print(f"✅ {len(member_ids)} Üye oluşturuldu.")

        # Üyelikleri dağıt
        for gym_name, gym_id in gym_map.items():
            gym_members = random.sample(member_ids, 40) # Her salona 40 üye
            
            for mid in gym_members:
                cursor.execute("SELECT membership_id FROM Membership WHERE gym_id=%s AND member_id=%s", (gym_id, mid))
                if cursor.fetchone(): continue

                m_type = random.choice(['timed', 'credit'])
                start = date.today() - timedelta(days=random.randint(0, 365))
                
                if m_type == 'timed':
                    end = start + timedelta(days=365)
                    is_active = 1 if end > date.today() else 0
                    cursor.execute("""
                        INSERT INTO Membership (gym_id, member_id, type, start_date, end_date, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (gym_id, mid, m_type, start, end, is_active))
                else:
                    total = random.choice([10, 20, 50, 100])
                    used = random.randint(0, total)
                    is_active = 1 if used < total else 0
                    cursor.execute("""
                        INSERT INTO Membership (gym_id, member_id, type, start_date, credit_total, credit_used, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (gym_id, mid, m_type, start, total, used, is_active))

        print("✅ Üyelikler dağıtıldı.")

        # ---------------------------------------------------------
        # 7. KİŞİSEL RUTİNLER
        # ---------------------------------------------------------
        routine_names = ["Bacak Günü", "Sabah Kardiyosu", "Güç Antrenmanı", "Cuma Programı", "Tatil Programı", "Karın Kası Odaklı"]
        
        for mid in member_ids:
            if random.random() > 0.4:
                title = random.choice(routine_names)
                cursor.execute("INSERT INTO CustomRoutine (member_id, title) VALUES (%s, %s)", (mid, title))
                routine_id = cursor.lastrowid
                
                num_exercises = random.randint(3, 6)
                selected_exercises = random.sample(ex_ids_list, num_exercises)
                
                for i, eid in enumerate(selected_exercises):
                    cursor.execute("""
                        INSERT INTO CustomRoutineExercise (routine_id, exercise_id, order_no, sets, reps, rest_sec)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (routine_id, eid, i+1, 3, 10, 60))
        
        print("✅ Kişisel rutinler oluşturuldu.")

        # ---------------------------------------------------------
        # 8. TRAINERS (İsim Havuzundan)
        # ---------------------------------------------------------
        for gym_name, gym_id in gym_map.items():
            for _ in range(random.randint(3, 5)):
                # Rastgele isim seç
                if random.choice([True, False]):
                    t_name = f"{random.choice(MALE_NAMES)} {random.choice(SURNAMES)}"
                else:
                    t_name = f"{random.choice(FEMALE_NAMES)} {random.choice(SURNAMES)}"

                specialty = random.choice(["Vücut Geliştirme", "Crossfit", "Yoga", "Pilates", "Rehabilitasyon", "Powerlifting"])
                is_in = random.choice([True, False])
                rating = round(random.uniform(3.5, 5.0), 1)
                
                linked_member_id = None
                if random.random() > 0.5:
                    linked_member_id = random.choice(member_ids)

                cursor.execute("""
                    INSERT INTO Trainer (gym_id, member_id, name, specialty, is_in_gym, rating_avg) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (gym_id, linked_member_id, t_name, specialty, is_in, rating))

        print("✅ Antrenörler oluşturuldu.")

        # ---------------------------------------------------------
        # 9. TURNİKE GEÇMİŞİ
        # ---------------------------------------------------------
        print("⏳ Turnike geçmişi oluşturuluyor (biraz sürebilir)...")
        today = datetime.now()
        
        for gym_name, gym_id in gym_map.items():
            cursor.execute("SELECT member_id FROM Membership WHERE gym_id = %s", (gym_id,))
            gym_member_ids = [row[0] for row in cursor.fetchall()]
            
            if not gym_member_ids: continue

            for day_offset in range(30):
                current_day = today - timedelta(days=day_offset)
                daily_entries = random.randint(20, 50)
                
                for _ in range(daily_entries):
                    mid = random.choice(gym_member_ids)
                    hour = random.randint(7, 21)
                    minute = random.randint(0, 59)
                    entry_time = current_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if entry_time > datetime.now(): continue

                    cursor.execute("INSERT INTO TurnstileEvent (gym_id, member_id, ts, direction) VALUES (%s, %s, %s, 'in')",
                                   (gym_id, mid, entry_time))
                    
                    if random.random() > 0.1:
                        duration = random.randint(30, 120)
                        exit_time = entry_time + timedelta(minutes=duration)
                        if exit_time < datetime.now():
                            cursor.execute("INSERT INTO TurnstileEvent (gym_id, member_id, ts, direction) VALUES (%s, %s, %s, 'out')",
                                           (gym_id, mid, exit_time))

        conn.commit()
        print("🎉 İŞLEM TAMAM! Gerçekçi Türk isimleri ile veritabanı hazır.")

    except mysql.connector.Error as err:
        print(f"❌ Hata: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_saas_data()