# Sistem Rekomendasi Berbasis AI

## Gambaran Umum

Sistem LMS Hybrid mencakup sistem rekomendasi berbasis AI yang komprehensif yang menyediakan rekomendasi kursus yang dipersonalisasi kepada pengguna berdasarkan riwayat pembelajaran, preferensi, dan interaksi mereka dengan platform.

## Fitur-Fitur

### 1. Algoritma Rekomendasi Multipel

Sistem ini mengimplementasikan beberapa algoritma rekomendasi:

1. **Filter Kolaboratif**: Merekomendasikan kursus berdasarkan preferensi pengguna serupa
2. **Filter Berbasis Konten**: Merekomendasikan kursus berdasarkan preferensi konten pengguna
3. **Berbasis Popularitas**: Merekomendasikan kursus populer dengan pendaftaran dan peringkat tinggi
4. **Berbasis Pengetahuan**: Merekomendasikan kursus berdasarkan aturan eksplisit dan pengetahuan
5. **Pendekatan Hybrid**: Menggabungkan beberapa algoritma untuk rekomendasi yang lebih baik

### 2. Pembuatan Profil Pengguna

Sistem ini membuat profil pengguna yang terperinci meliputi:

- Kategori dan tingkat kesulitan yang disukai
- Riwayat pembelajaran (kursus yang telah diselesaikan dan dilihat)
- Pola interaksi dan preferensi
- Vektor fitur untuk algoritma machine learning

### 3. Pelacakan Interaksi

Melacak berbagai interaksi pengguna:

- Melihat kursus
- Pendaftaran
- Penyelesaian
- Peringkat
- Daftar keinginan
- Pencarian

### 4. Sistem Umpan Balik

Memungkinkan pengguna memberikan umpan balik pada rekomendasi:

- Membantu
- Tidak Membantu
- Tidak Relevan
- Menyesatkan

## Endpoint API

### Rekomendasi

- `GET /api/v1/recommendations/` - Daftar rekomendasi saat ini
- `GET /api/v1/recommendations/{id}/` - Dapatkan rekomendasi spesifik
- `POST /api/v1/recommendations/generate/` - Hasilkan rekomendasi baru
- `POST /api/v1/recommendations/{id}/click/` - Tandai rekomendasi sebagai diklik
- `POST /api/v1/recommendations/{id}/feedback/` - Kirim umpan balik

### Profil Pengguna

- `GET /api/v1/recommendations/profile/` - Dapatkan profil rekomendasi pengguna
- `PUT /api/v1/recommendations/profile/` - Perbarui profil rekomendasi pengguna

### Pelacakan Interaksi

- `POST /api/v1/recommendations/track-interaction/` - Lacak interaksi kursus

### Umpan Balik

- `GET /api/v1/recommendations/feedback/` - Daftar umpan balik

### Pengaturan

- `GET /api/v1/recommendations/settings/` - Dapatkan pengaturan rekomendasi
- `PUT /api/v1/recommendations/settings/` - Perbarui pengaturan rekomendasi

## Perintah Manajemen

- `python manage.py generate_recommendations --all` - Hasilkan rekomendasi untuk semua pengguna
- `python manage.py generate_recommendations --user-id 1` - Hasilkan rekomendasi untuk pengguna spesifik
- `python manage.py generate_recommendations --force` - Paksa penyegaran rekomendasi

## Model-Model

### UserRecommendationProfile

Menyimpan data profil pengguna yang digunakan untuk menghasilkan rekomendasi.

### UserCourseInteraction

Melacak interaksi pengguna dengan kursus untuk algoritma rekomendasi.

### Recommendation

Menyimpan rekomendasi yang dihasilkan untuk pengguna.

### RecommendationFeedback

Menyimpan umpan balik pengguna pada rekomendasi untuk meningkatkan sistem.

### RecommendationSettings

Pengaturan sistem secara keseluruhan untuk mesin rekomendasi.

## Layanan

Kelas `RecommendationService` menyediakan metode untuk:

- Menghasilkan profil pengguna
- Membuat rekomendasi menggunakan algoritma yang berbeda
- Melacak interaksi pengguna
- Menangani umpan balik
- Menggabungkan dan memberi peringkat rekomendasi

## Antarmuka Admin

Sistem ini mencakup antarmuka admin yang komprehensif untuk mengelola:

- Profil rekomendasi pengguna
- Interaksi kursus pengguna
- Rekomendasi
- Umpan balik
- Pengaturan

## Peningkatan Mendatang

1. **Model Deep Learning**: Mengimplementasikan filter kolaboratif neural
2. **Rekomendasi Real-time**: Menghasilkan rekomendasi secara real-time
3. **Pengujian A/B**: Menguji algoritma rekomendasi yang berbeda
4. **Analitik Lanjutan**: Memberikan wawasan tentang kinerja rekomendasi
5. **Kampanye Email yang Dipersonalisasi**: Mengirim rekomendasi kursus yang dipersonalisasi melalui email

# Dokumentasi Teknis Sistem Rekomendasi

## Arsitektur Sistem

Sistem rekomendasi dibangun dengan arsitektur berlapis yang mencakup:

1. **Lapisan Model**: Mewakili struktur data untuk profil pengguna, interaksi, rekomendasi, dan umpan balik
2. **Lapisan Layanan**: Berisi logika bisnis untuk menghasilkan rekomendasi menggunakan berbagai algoritma
3. **Lapisan API**: Menyediakan endpoint RESTful untuk mengakses fungsionalitas rekomendasi
4. **Lapisan Admin**: Antarmuka Django admin untuk manajemen data
5. **Lapisan Manajemen**: Perintah CLI untuk operasi batch

## Detail Model

### UserRecommendationProfile

Model ini menyimpan informasi profil pengguna yang digunakan untuk menghasilkan rekomendasi:

- **preferred_categories**: Daftar ID kategori yang disukai pengguna
- **preferred_difficulty_levels**: Tingkat kesulitan yang disukai (pemula, menengah, lanjutan)
- **preferred_learning_styles**: Gaya belajar yang disukai (video, teks, interaktif, dll.)
- **completed_courses**: Kursus yang telah diselesaikan oleh pengguna
- **viewed_courses**: Kursus yang telah dilihat oleh pengguna
- **last_active**: Waktu terakhir pengguna aktif
- **total_learning_time**: Total waktu yang dihabiskan untuk belajar dalam menit
- **feature_vector**: Vektor fitur pengguna untuk algoritma machine learning

### UserCourseInteraction

Model ini melacak interaksi pengguna dengan kursus:

- **interaction_type**: Jenis interaksi (dilihat, terdaftar, selesai, diberi peringkat, diinginkan, dicari)
- **rating**: Peringkat yang diberikan pengguna (1-5)
- **time_spent**: Waktu yang dihabiskan pada kursus dalam menit
- **interaction_date**: Tanggal interaksi
- **metadata**: Konteks tambahan tentang interaksi

### Recommendation

Model ini menyimpan rekomendasi yang dihasilkan:

- **recommendation_type**: Jenis rekomendasi (kursus, pelajaran, instruktur, kategori, pengguna serupa)
- **course**: Kursus yang direkomendasikan
- **recommended_item_id**: ID item yang direkomendasikan (untuk rekomendasi non-kursus)
- **algorithm_used**: Algoritma yang digunakan untuk menghasilkan rekomendasi
- **score**: Skor rekomendasi/tingkat kepercayaan (0.0 - 1.0)
- **reason**: Penjelasan mengapa rekomendasi ini dibuat
- **reason_data**: Data terstruktur yang menjelaskan rekomendasi
- **generated_at**: Kapan rekomendasi dihasilkan
- **expires_at**: Kapan rekomendasi ini kedaluwarsa
- **is_clicked**: Apakah rekomendasi telah diklik
- **clicked_at**: Kapan rekomendasi diklik
- **is_dismissed**: Apakah rekomendasi telah ditutup
- **dismissed_at**: Kapan rekomendasi ditutup

### RecommendationFeedback

Model ini menyimpan umpan balik pengguna pada rekomendasi:

- **feedback_type**: Jenis umpan balik (membantu, tidak membantu, tidak relevan, menyesatkan)
- **comment**: Komentar pengguna tentang rekomendasi
- **created_at**: Kapan umpan balik dibuat

### RecommendationSettings

Model ini menyimpan pengaturan sistem untuk mesin rekomendasi:

- **default_algorithm**: Algoritma default yang digunakan
- **max_recommendations_per_user**: Jumlah maksimum rekomendasi per pengguna
- **recommendation_expiry_days**: Jumlah hari sebelum rekomendasi kedaluwarsa
- **auto_refresh_enabled**: Apakah rekomendasi otomatis diperbarui
- **refresh_interval_hours**: Interval jam antara penyegaran rekomendasi
- **exclude_completed_courses**: Kecualikan kursus yang telah diselesaikan
- **exclude_enrolled_courses**: Kecualikan kursus yang sedang diikuti

## Algoritma Rekomendasi

### Filter Kolaboratif

Algoritma ini merekomendasikan kursus berdasarkan pola interaksi pengguna serupa. Ini bekerja dengan:

1. Mengidentifikasi pengguna dengan pola interaksi serupa menggunakan kesamaan Jaccard
2. Menemukan kursus yang disukai pengguna serupa tetapi belum diinteraksikan oleh pengguna saat ini
3. Memberikan skor berdasarkan tingkat kesamaan dan peringkat yang diberikan pengguna serupa

### Filter Berbasis Konten

Algoritma ini merekomendasikan kursus berdasarkan preferensi konten pengguna:

1. Mengidentifikasi kategori yang disukai berdasarkan interaksi sebelumnya
2. Merekomendasikan kursus dari kategori yang disukai yang belum diinteraksikan
3. Memberikan skor berdasarkan peringkat rata-rata kursus

### Berbasis Popularitas

Algoritma ini merekomendasikan kursus populer:

1. Menghitung skor popularitas berdasarkan jumlah pendaftaran dan peringkat rata-rata
2. Merekomendasikan kursus dengan skor popularitas tertinggi
3. Memberikan skor berdasarkan posisi peringkat

### Berbasis Pengetahuan

Algoritma ini merekomendasikan kursus berdasarkan aturan eksplisit:

1. Merekomendasikan kursus lanjutan dalam kategori yang sama dengan kursus yang telah diselesaikan
2. Merekomendasikan kursus tren baru
3. Memberikan skor tinggi untuk rekomendasi yang didasarkan pada pengetahuan domain

### Pendekatan Hybrid

Pendekatan ini menggabungkan semua algoritma di atas:

1. Menghasilkan rekomendasi menggunakan setiap algoritma
2. Menggabungkan rekomendasi berdasarkan kursus yang sama
3. Memberikan bobot berbeda untuk setiap algoritma
4. Memberikan peringkat akhir berdasarkan skor gabungan

## Penggunaan API

### Mendapatkan Rekomendasi

```
GET /api/v1/recommendations/
Authorization: Bearer <token>

Respons:
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Nama Pengguna"
      },
      "recommendation_type": "course",
      "course": {
        "id": 5,
        "title": "Pengantar Machine Learning",
        "description": "Kursus tentang konsep dasar machine learning",
        "instructor": "Dr. Budi",
        "category": "Data Science",
        "difficulty_level": "intermediate",
        "duration": 120,
        "rating": 4.5,
        "enrollment_count": 1200
      },
      "algorithm_used": "collaborative",
      "score": 0.85,
      "reason": "Pengguna dengan minat serupa sangat merekomendasikan kursus ini",
      "generated_at": "2023-06-15T10:30:00Z",
      "expires_at": "2023-06-22T10:30:00Z"
    }
  ]
}
```

### Menghasilkan Rekomendasi Baru

```
POST /api/v1/recommendations/generate/
Authorization: Bearer <token>

Respons:
{
  "message": "Rekomendasi berhasil dihasilkan",
  "recommendations": [
    // Array rekomendasi
  ]
}
```

### Memberikan Umpan Balik

```
POST /api/v1/recommendations/{id}/feedback/
Authorization: Bearer <token>
Content-Type: application/json

{
  "feedback_type": "helpful",
  "comment": "Rekomendasi ini sangat membantu untuk karir saya"
}

Respons:
{
  "message": "Umpan balik berhasil dikirim",
  "feedback": {
    "id": 1,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "Nama Pengguna"
    },
    "recommendation": 1,
    "feedback_type": "helpful",
    "comment": "Rekomendasi ini sangat membantu untuk karir saya",
    "created_at": "2023-06-15T10:30:00Z"
  }
}
```

## Perintah CLI

### Menghasilkan Rekomendasi untuk Semua Pengguna

```bash
python manage.py generate_recommendations --all
```

### Menghasilkan Rekomendasi untuk Pengguna Spesifik

```bash
python manage.py generate_recommendations --user-id 1
```

### Memaksa Penyegaran Rekomendasi

```bash
python manage.py generate_recommendations --force
```

## Konfigurasi

Pengaturan sistem rekomendasi dapat dikonfigurasi melalui antarmuka admin atau dengan membuat instance `RecommendationSettings` secara langsung. Pengaturan default mencakup:

- Algoritma default: Hybrid
- Maksimum rekomendasi per pengguna: 10
- Hari kedaluwarsa rekomendasi: 7
- Penyegaran otomatis: Diaktifkan
- Interval penyegaran: 24 jam
- Mengecualikan kursus yang telah diselesaikan: Diaktifkan
- Mengecualikan kursus yang sedang diikuti: Diaktifkan

## Pemeliharaan

### Menangani Masalah Migrasi

Jika terjadi masalah dengan migrasi database, gunakan perintah:

```bash
python manage.py migrate recommendations
```

Atau untuk memperbaiki masalah migrasi:

```bash
python manage.py migrate recommendations --fake
```

### Memantau Kinerja

Untuk memantau kinerja sistem rekomendasi:

1. Periksa log aplikasi untuk kesalahan
2. Gunakan Django admin untuk melihat statistik penggunaan
3. Pantau waktu respons API
4. Periksa penggunaan memori dan CPU

## Pengujian

Sistem rekomendasi telah diuji secara menyeluruh dengan:

1. Unit test untuk setiap komponen
2. Integration test untuk alur kerja lengkap
3. Pengujian kinerja untuk memastikan skalabilitas
4. Pengujian beban untuk memastikan stabilitas

Untuk menjalankan pengujian:

```bash
python manage.py test recommendations
```

## Troubleshooting

### Masalah Umum

1. **Rekomendasi tidak muncul**: Pastikan pengguna memiliki interaksi yang cukup dan sistem telah menghasilkan rekomendasi
2. **Rekomendasi tidak relevan**: Periksa pengaturan algoritma dan berikan umpan balik untuk meningkatkan akurasi
3. **Kesalahan API**: Periksa log untuk detail kesalahan dan pastikan token autentikasi valid

### Logging

Sistem menggunakan logging Django standar. Untuk mengaktifkan logging verbose, tambahkan ke settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'recommendations.log',
        },
    },
    'loggers': {
        'recommendations': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Pengembangan Lebih Lanjut

### Menambahkan Algoritma Baru

Untuk menambahkan algoritma rekomendasi baru:

1. Tambahkan jenis algoritma baru ke `RecommendationAlgorithm` di models.py
2. Implementasikan metode baru di `RecommendationService`
3. Tambahkan bobot untuk algoritma baru di metode `_get_algorithm_weight`
4. Perbarui dokumentasi dan pengujian

### Mengoptimalkan Kinerja

Untuk mengoptimalkan kinerja sistem rekomendasi:

1. Gunakan caching untuk hasil rekomendasi
2. Optimalkan query database dengan indexing yang tepat
3. Implementasikan pemrosesan batch untuk rekomendasi
4. Gunakan sistem antrian untuk tugas berat
