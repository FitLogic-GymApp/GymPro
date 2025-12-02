import mysql.connector
import random
from datetime import date, datetime, timedelta

# --- AYARLAR ---

DB_CONFIG = {
  'user': 'root',
  'password': 'Halil_2003',  # Kendi şifreni buraya yaz
  'host': '127.0.0.1',
  'database': 'gympro_db'
}

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def populate_data():
    conn = connect_db()
    cursor = conn.cursor()
    print("Veritabanına bağlanıldı, veriler yükleniyor...")

    # 1. GYM EKLEME
    cursor.execute("SELECT count(*) FROM Gym")
    if cursor.fetchone()[0] == 0:
        print("Gym ekleniyor...")
        sql = "INSERT INTO Gym (name, location, capacity) VALUES (%s, %s, %s)"
        cursor.execute(sql, ("GymPro Merkez", "Kampüs İçi", 50))
        gym_id = cursor.lastrowid
    else:
        print("Gym zaten var, atlanıyor.")

    # 2. EGZERSİZLERİ EKLEME (Sabit liste)
    exercises = [
        ("Bench Press", "Chest"), ("Squat", "Legs"), ("Deadlift", "Back"),
        ("Overhead Press", "Shoulders"), ("Bicep Curl", "Arms"), ("Tricep Extension", "Arms"),
        ("Leg Press", "Legs"), ("Lat Pulldown", "Back"), ("Plank", "Core")
    ]
    
    print("Egzersizler kontrol ediliyor...")
    for name, muscle in exercises:
        cursor.execute("SELECT count(*) FROM Exercise WHERE name = %s", (name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Exercise (name, muscle_group) VALUES (%s, %s)", (name, muscle))

    # 3. HOCALARI EKLEME
    trainers = [
        ("Ahmet Yılmaz", "Strength"), ("Ayşe Demir", "Mobility"), 
        ("Mehmet Öz", "Cardio"), ("Zeynep Kaya", "Pilates"), ("Can Yıldız", "Crossfit")
    ]
    
    print("Hocalar ekleniyor...")
    for name, spec in trainers:
        cursor.execute("SELECT count(*) FROM Trainer WHERE name = %s", (name,))
        if cursor.fetchone()[0] == 0:
            is_in = random.choice([True, False])
            rating = round(random.uniform(3.5, 5.0), 2)
            cursor.execute("INSERT INTO Trainer (name, specialty, is_in_gym, rating_avg) VALUES (%s, %s, %s, %s)", 
                           (name, spec, is_in, rating))

    # 4. ÜYELERİ VE ÜYELİKLERİ EKLEME
    print("Üyeler ve üyelikler oluşturuluyor...")
    # Rastgele isim listesi
    first_names = ["Ali", "Veli", "Ayşe", "Fatma", "Berkay", "Halil", "Selin", "Mert", "Deniz", "Burak"]
    last_names = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Koç", "Öztürk", "Arslan", "Doğan", "Kılıç"]
    
    for _ in range(20): # 20 Üye ekleyelim
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        full_name = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}@example.com"
        
        # Üye var mı kontrol et (basitçe email ile)
        cursor.execute("SELECT member_id FROM Member WHERE email = %s", (email,))
        existing = cursor.fetchone()
        
        if not existing:
            # Üye ekle
            cursor.execute("INSERT INTO Member (name, email, phone, gender, birth_date) VALUES (%s, %s, %s, %s, %s)",
                           (full_name, email, "5551234567", random.choice(['M', 'F']), "1998-05-19"))
            member_id = cursor.lastrowid
            
            # Üyelik ekle (Membership)
            m_type = random.choice(['timed', 'credit'])
            start_date = date.today() - timedelta(days=random.randint(0, 30))
            
            if m_type == 'timed':
                end_date = start_date + timedelta(days=90) # 3 aylık
                cursor.execute("""
                    INSERT INTO Membership (member_id, type, start_date, end_date, is_active) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (member_id, m_type, start_date, end_date, True))
            else:
                cursor.execute("""
                    INSERT INTO Membership (member_id, type, credit_total, credit_used, is_active) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (member_id, m_type, 50, random.randint(0, 10), True))
                
            # 5. TURNİKE HAREKETLERİ (Turnstile Events)
            # Doluluk testi için bazılarını içeri sokalım ('in') ama çıkarmayalım ('out' yok)
            if random.choice([True, False]):
                cursor.execute("INSERT INTO TurnstileEvent (member_id, direction) VALUES (%s, 'in')", (member_id,))

    conn.commit()
    cursor.close()
    conn.close()
    print("\nHarika! Test verileri başarıyla yüklendi.")

if __name__ == "__main__":
    populate_data()