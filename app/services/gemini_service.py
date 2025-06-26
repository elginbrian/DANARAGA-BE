import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.models.user import UserPublic
from app.models.enums import ExpenseCategory

if not settings.GEMINI_API_KEY:
    print("PERINGATAN: GEMINI_API_KEY tidak diatur. Fungsi-fungsi Gemini tidak akan bekerja.")
    model = None
else:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def _clean_gemini_json_response(raw_text: str) -> str:
    cleaned_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
    return cleaned_text

async def _call_gemini_with_prompt(prompt: str, is_json_output: bool = True) -> Optional[str]:
    if not model:
        return None
    try:
        response = await model.generate_content_async(prompt)
        if is_json_output:
            return _clean_gemini_json_response(response.text)
        return response.text
    except Exception as e:
        print(f"Error saat memanggil Gemini AI: {e}")
        return None

async def generate_facility_filter(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""
    **Persona Anda:** Anda adalah API presisi tinggi yang bertugas mengonversi profil pengguna menjadi kueri filter MongoDB.
    
    **Tujuan:** Menghasilkan sebuah string JSON yang valid untuk kriteria filter dari method `find()`.
    
    **Referensi Schema:**
    - Facility: {{ name: String, type: String, tariff_max: Number, location: GeoJSON, services_offered: [String] }}
    - User/Preferences: {{ max_budget: Number, max_distance_km: Number, facility_type: [String], user_location: {{ latitude: Number, longitude: Number }} }}

    **Aturan (WAJIB DIIKUTI):**
    1.  **Jarak (`location`):** HANYA tambahkan jika `user_location` valid. Gunakan `$near` dengan `$geometry` (koordinat: [longitude, latitude]) dan `$maxDistance` (dalam meter).
    2.  **Anggaran (`tariff_max`):** HANYA tambahkan jika `max_budget` valid. Gunakan `$lte`.
    3.  **Keamanan:** JANGAN PERNAH menyertakan operator seperti `$limit`, `$sort`, atau operator berbahaya (`delete`, `drop`).

    **Data Pengguna untuk Diproses:**
    ```json
    {json.dumps(user_profile, indent=2)}
    ```

    **Spesifikasi Output:** Kembalikan HANYA string JSON yang valid dan telah di-minify. Jika tidak ada kondisi valid, kembalikan objek JSON kosong: `{{}}`.
    """
    
    json_string = await _call_gemini_with_prompt(prompt)
    if not json_string:
        return {}
        
    try:
        query = json.loads(json_string)
        if not isinstance(query, dict): return {}
        return query
    except json.JSONDecodeError:
        print(f"Error: Gemini tidak mengembalikan JSON yang valid. Output: {json_string}")
        return {}

async def process_receipt_with_gemini(image_buffer: bytes, mime_type: str) -> Optional[Dict[str, Any]]:
    if not model: return None

    prompt = f"""
    Anda adalah AI ahli membaca struk medis. Ekstrak informasi dari gambar.
    Format Output WAJIB JSON:
    {{
      "items": [{{"name": "NAMA_ITEM", "quantity": 1, "total_price": 100000, "category": "MEDICATION"}}],
      "overall_total": 100000, "store_name": "NAMA_APOTEK", "transaction_date": "YYYY-MM-DD"
    }}
    Kategori harus salah satu dari: {', '.join([e.value for e in ExpenseCategory])}. Default ke 'OTHER'.
    Jika tidak jelas, kembalikan "items" kosong. Analisis gambar berikut:
    """
    
    image_part = {"mime_type": mime_type, "data": image_buffer}
    
    try:
        response = await model.generate_content_async([prompt, image_part])
        json_string = _clean_gemini_json_response(response.text)
        return json.loads(json_string)
    except (Exception, json.JSONDecodeError) as e:
        print(f"Error saat memproses struk dengan Gemini: {e}")
        return None

async def enrich_facility_data(facility: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    prompt = f"""
    **Tugas:** Anda adalah analis data yang memverifikasi dan memperbarui informasi fasilitas kesehatan.
    
    **Data Saat Ini:**
    ```json
    {json.dumps(facility, indent=2, default=str)}
    ```

    **Instruksi:**
    1.  Lakukan pencarian web untuk fasilitas di atas.
    2.  Fokus untuk menemukan data yang lebih baru atau lebih lengkap (rating, telepon, layanan, URL gambar).
    3.  Kembalikan hasilnya sebagai **SATU OBJEK JSON TUNGGAL** yang valid.
    4.  Jika sebuah field tidak dapat ditemukan, jangan sertakan field itu di JSON balasan.
    
    **Contoh Output JSON:**
    `{{"overall_rating": 4.7, "phone": "(021) 123456", "image_url": "https://example.com/image.jpg"}}`
    
    **PASTIKAN OUTPUT ANDA HANYA OBJEK JSON VALID.**
    """
    json_string = await _call_gemini_with_prompt(prompt)
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return None

async def search_facilities_with_gemini(query: str, user_location: Dict[str, float]) -> List[Dict[str, Any]]:
    prompt = f"""
    **Tugas:** Anda adalah ahli pencarian fasilitas kesehatan. Analisis query pengguna dan temukan fasilitas yang paling relevan.
    
    **User Query:** "{query}"
    **Lokasi Pengguna:** Latitude {user_location.get('latitude')}, Longitude {user_location.get('longitude')}

    **Instruksi:**
    1.  Interpretasikan apa yang dicari pengguna (tipe fasilitas, layanan, lokasi).
    2.  Kembalikan 3-5 fasilitas yang relevan.
    3.  Jika query tidak jelas, sarankan fasilitas umum terdekat.
    
    **Format Output (JSON Array):**
    `[{{"name": "Nama Faskes", "type": "HOSPITAL", "address": "Alamat Lengkap", "latitude": -6.2000, "longitude": 106.8000, ...}}]`
    
    **KEMBALIKAN HANYA JSON ARRAY.**
    """
    json_string = await _call_gemini_with_prompt(prompt)
    if not json_string:
        return []
    try:
        facilities = json.loads(json_string)
        if isinstance(facilities, list):
            return facilities
        return []
    except json.JSONDecodeError:
        return []

async def generate_spending_recommendations(expenses: List[Dict[str, Any]]) -> List[str]:
    if not expenses:
        return [
            "Mulai catat pengeluaran Anda untuk mendapatkan wawasan.",
            "Alokasikan dana darurat khusus untuk kebutuhan kesehatan.",
        ]

    simplified_expenses = [
        {k: v for k, v in exp.items() if k in ['category', 'total_price', 'medicine_name']}
        for exp in expenses[:10]
    ]

    prompt = f"""
    Anda adalah penasihat keuangan pribadi. Berdasarkan data pengeluaran berikut, berikan 3 rekomendasi praktis.
    Fokus pada pola pengeluaran, potensi penghematan, dan tips anggaran.

    **Data:**
    ```json
    {json.dumps(simplified_expenses, indent=2, default=str)}
    ```

    **Format output:** Array JSON berisi 3 string rekomendasi.
    **Contoh:** `["Mengingat pengeluaran obat Anda cukup tinggi, coba diskusikan alternatif generik dengan dokter."]`
    """
    
    json_string = await _call_gemini_with_prompt(prompt)
    if not json_string:
        return ["Gagal mendapatkan rekomendasi saat ini."]
        
    try:
        recommendations = json.loads(json_string)
        if isinstance(recommendations, list) and all(isinstance(item, str) for item in recommendations):
            return recommendations
        return ["Format rekomendasi tidak valid."]
    except json.JSONDecodeError:
        return ["Gagal memproses rekomendasi dari AI."]