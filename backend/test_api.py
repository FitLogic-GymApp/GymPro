import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_routine_flow():
    print("--- 1. YENİ RUTİN OLUŞTURULUYOR ---")
    payload = {
        "member_id": 1,
        "title": "Pazartesi Göğüs Günü"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/my-routines", json=payload)
        
        # Önce durum kodunu ve ham veriyi yazdıralım (Hata ayıklamak için)
        print(f"Durum Kodu: {response.status_code}")
        
        if response.status_code != 200 and response.status_code != 201:
            print("HATA! Sunucudan dönen ham veri:")
            print(response.text) # Hatanın ne olduğunu burada göreceğiz
            return

        print("Cevap:", response.json())
        
        routine_id = response.json()['routine_id']
        
        print(f"\n--- 2. RUTİNE EGZERSİZ EKLENİYOR (ID: {routine_id}) ---")
        ex_payload = {
            "exercise_id": 1, 
            "sets": 4,
            "reps": 8,
            "rest_sec": 90,
            "order_no": 1
        }
        res2 = requests.post(f"{BASE_URL}/my-routines/{routine_id}/add-exercise", json=ex_payload)
        print("Ekleme Cevabı:", res2.json())
        
        print(f"\n--- 3. RUTİN DETAYINI GÖRME ---")
        res3 = requests.get(f"{BASE_URL}/my-routines/{routine_id}")
        print("Detay:", json.dumps(res3.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.ConnectionError:
        print("\nKRİTİK HATA: Sunucuya bağlanılamadı!")
        print("Lütfen app.py dosyasının ayrı bir terminalde çalıştığından emin ol.")
    except Exception as e:
        print(f"\nBeklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    test_routine_flow()