import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta, time

# --- AYARLAR ---
DB_CONFIG = {
  'user': 'root',
  'password': '1234',  # Şifreni gir
  'host': '127.0.0.1',
  'database': 'gympro_db'
}

fake = Faker('tr_TR')  # Türkçe isimler üretmesi için

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def clean_tables(cursor):
    print("🧹 Eski veriler temizleniyor...")
    # Foreign Key kısıtlamalarını geçici olarak kapatıyoruz ki rahat silelim
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    tables = ["TurnstileEvent", "CustomRoutineExercise", "CustomRoutine", 
              "Membership", "Member", "Trainer", "Gym"]
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("✅ Tablolar temizlendi.")

def create_gym_and_trainers(cursor):
    print("🏋️ Salon ve Hocalar oluşturuluyor...")
    # Gym
    cursor.execute("INSERT INTO Gym (name, location, capacity) VALUES (%s, %s, %s)", 
                   ("IronByte Gym", "ODTÜ Teknokent", 100))
    
    # Trainers
    trainers = [
        ("Berkay Hoca", "Powerlifting", True),
        ("Halil Hoca", "Crossfit", True),
        ("Selin Yılmaz", "Yoga/Pilates", False),
        ("Mert Demir", "Bodybuilding", True),
        ("Ayşe Kaya", "Rehabilitation", False)
    ]
    for name, spec, is_in in trainers:
        rating = round(random.uniform(4.0, 5.0), 2)
        cursor.execute("INSERT INTO Trainer (name, specialty, is_in_gym, rating_avg) VALUES (%s, %s, %s, %s)",
                       (name, spec, is_in, rating))

def create_members_and_memberships(cursor, count=50):
    print(f"👥 {count} adet üye ve üyelik oluşturuluyor (Modern İsimlerle)...")
    member_ids = []
    
    # 1. MODERN İSİM HAVUZU (Üniversite/Genç kitleye uygun)
    male_names = ["Berk","Mete", "Yusuf", "Yasin", "Can","Berkay", "Halil", "Ahmet", "Yağız", "Mert", "Burak", "Emre", "Kaan", "Arda", "Kerem", "Alp", "Ege", "Yiğit", "Onur", "Cem", "Umut", "Tolga", "Bora", "Efe", "Sarp", "Ozan", "Deniz"]
    female_names = ["Zeynep","Betül", "Neva", "Şevval", "Ceren",  "Selin", "Elif", "Melis", "Damla", "Ece", "İrem", "Gamze", "Gizem", "Buse", "Duygu", "Pelin", "Aslı", "Begüm", "Ceren", "Defne", "Ezgi", "İlayda", "Simge", "Deniz"]
    last_names = ["Yılmaz", "Kaya","Keskin", "Avan", "Demir", "Çelik", "Şahin", "Yıldız", "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek", "Polat"]

    for _ in range(count):
        # Rastgele cinsiyet ve isim seçimi
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            fname = random.choice(male_names)
        else:
            fname = random.choice(female_names)
            
        lname = random.choice(last_names)
        full_name = f"{fname} {lname}"
        
        # E-posta oluştur (Türkçe karakterleri temizleyerek)
        clean_fname = fname.lower().replace('ş','s').replace('ç','c').replace('ö','o').replace('ü','u').replace('ı','i').replace('ğ','g')
        clean_lname = lname.lower().replace('ş','s').replace('ç','c').replace('ö','o').replace('ü','u').replace('ı','i').replace('ğ','g')
        email = f"{clean_fname}.{clean_lname}@{random.choice(['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com'])}"
        
        # Telefon
        phone = f"05{random.choice(['32','33','42','43','55','05','06','07'])}{random.randint(1000000, 9999999)}"
        
        # Doğum tarihi (18-35 yaş arası genç kitle)
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=35)
        
        # Üye Ekleme
        cursor.execute("INSERT INTO Member (name, email, phone, gender, birth_date) VALUES (%s, %s, %s, %s, %s)",
                       (full_name, email, phone, gender, birth_date))
        member_id = cursor.lastrowid
        member_ids.append(member_id)
        
        # Üyelik Ekleme (Membership)
        m_type = random.choice(['timed', 'credit'])
        start_date = fake.date_between(start_date='-120d', end_date='today')
        
        if m_type == 'timed':
            duration = random.choice([30, 90, 180, 365])
            end_date = start_date + timedelta(days=duration)
            cursor.execute("""
                INSERT INTO Membership (member_id, type, start_date, end_date, is_active) 
                VALUES (%s, %s, %s, %s, %s)
            """, (member_id, m_type, start_date, end_date, True))
        else:
            total = random.choice([10, 20, 50])
            used = random.randint(0, int(total * 0.8)) # En fazla %80'ini kullanmış olsun
            cursor.execute("""
                INSERT INTO Membership (member_id, type, credit_total, credit_used, is_active) 
                VALUES (%s, %s, %s, %s, %s)
            """, (member_id, m_type, total, used, True))
            
    return member_ids

def generate_traffic_history(cursor, member_ids):
    print("📈 Son 30 günün giriş-çıkış verisi (Time-Series) oluşturuluyor...")
    # Veri bilimi projesi gibi düşün: Hafta içi akşamları (17:00-20:00) yoğun olsun.
    
    today = datetime.now()
    
    for day_offset in range(30, -1, -1): # Son 30 günden bugüne
        current_date = today - timedelta(days=day_offset)
        
        # O gün kaç kişi gelsin? (Haftasonu az, hafta içi çok)
        is_weekend = current_date.weekday() >= 5
        daily_visitors = random.randint(10, 20) if is_weekend else random.randint(20, 40)
        
        todays_visitors = random.sample(member_ids, k=min(len(member_ids), daily_visitors))
        
        for mid in todays_visitors:
            # Giriş saati belirle (Gaussian dağılımı gibi: 18:00 civarı yoğun)
            hour = int(random.gauss(18, 3)) 
            hour = max(7, min(22, hour)) # 07:00 - 22:00 arası sınırla
            minute = random.randint(0, 59)
            
            entry_time = current_date.replace(hour=hour, minute=minute, second=0)
            
            # İçeride kalma süresi (45 dk - 120 dk)
            duration_min = random.randint(45, 120)
            exit_time = entry_time + timedelta(minutes=duration_min)
            
            # Giriş Kaydı
            cursor.execute("INSERT INTO TurnstileEvent (member_id, ts, direction) VALUES (%s, %s, 'in')",
                           (mid, entry_time))
            
            # Çıkış Kaydı (Eğer çıkış saati şu andan önceyse. Şu an içeride kalsın istiyorsak çıkış eklemeyiz)
            if exit_time < datetime.now():
                cursor.execute("INSERT INTO TurnstileEvent (member_id, ts, direction) VALUES (%s, %s, 'out')",
                               (mid, exit_time))

def assign_routines(cursor, member_ids):
    print("📋 Bazı üyelere rutinler atanıyor...")
    # Örnek antrenmanlar
    templates = [
        ("Hypertrophy - Upper", [1, 2, 4]), # Bench, Squat(yok), Overhead
        ("Leg Day from Hell", [3, 1]), # Squat, Deadlift(varsa)
        ("Morning Cardio", [5]) # Plank vb
    ]
    
    # Üyelerin %60'ına rutin verelim
    for mid in member_ids:
        if random.random() > 0.4: 
            template_name, ex_ids = random.choice(templates)
            
            # Rutin Başlığı
            cursor.execute("INSERT INTO CustomRoutine (member_id, title) VALUES (%s, %s)",
                           (mid, template_name))
            routine_id = cursor.lastrowid
            
            # Egzersizler
            for i, eid in enumerate(ex_ids):
                # Egzersizin var olup olmadığını kontrol etmeye gerek duymuyoruz çünkü populate_db.py'de eklemiştik
                # Ama hata almamak için basit try/except ile geçebiliriz veya varsayabiliriz.
                # Burada populate_db'deki ID'lerin 1,2,3... olduğunu varsayıyoruz.
                try:
                    cursor.execute("""
                        INSERT INTO CustomRoutineExercise (routine_id, exercise_id, order_no, sets, reps, rest_sec)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (routine_id, eid, i+1, 3, 12, 60))
                except:
                    pass # Egzersiz ID yoksa geç

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        clean_tables(cursor)
        create_gym_and_trainers(cursor)
        
        # Sabit egzersizlerin silinmediğinden emin olmak için populate_db'yi çağırmak yerine
        # burada hızlıca tekrar ekleyebiliriz veya truncate listesinden 'Exercise'ı çıkarırız.
        # Yukarıda Exercise tablosunu TRUNCATE listesine almadım, o yüzden eski egzersizler duruyor.
        
        member_ids = create_members_and_memberships(cursor, count=50)
        generate_traffic_history(cursor, member_ids)
        assign_routines(cursor, member_ids)
        
        conn.commit()
        print("\n🚀 VERİTABANI BAŞARIYLA YENİLENDİ! Veriler artık çok daha gerçekçi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()