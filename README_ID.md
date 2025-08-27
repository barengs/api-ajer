# Hybrid LMS - Sistem Manajemen Pembelajaran Hibrid

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)

## 📖 Deskripsi

Hybrid LMS adalah sistem manajemen pembelajaran modern yang menggabungkan dua pendekatan pembelajaran:

1. **Self-Paced Learning** (Gaya Udemy) - Pembelajaran mandiri dengan video on-demand
2. **Structured Classroom** (Gaya Google Classroom) - Pembelajaran terstruktur dengan jadwal dan batch

Sistem ini dibangun menggunakan Django REST Framework dan dirancang untuk memberikan pengalaman pembelajaran yang fleksibel bagi siswa, instruktur, dan administrator.

## 🚀 Fitur Utama

### 👨‍🎓 Untuk Siswa

- **Pendaftaran dan Profil**: Registrasi akun, manajemen profil lengkap
- **Pencarian Kursus**: Sistem pencarian dan filter yang canggih
- **Pembelajaran Fleksibel**:
  - Kursus self-paced dengan video on-demand
  - Kelas terstruktur dengan jadwal dan batch
- **Pelacakan Progress**: Monitoring kemajuan pembelajaran secara real-time
- **Forum Diskusi**: Interaksi dengan sesama siswa dan instruktur
- **Sistem Review**: Memberikan rating dan review untuk kursus
- **Sertifikat**: Mendapatkan sertifikat setelah menyelesaikan kursus
- **Gamifikasi**: Points, badges, dan leaderboard
- **Wishlist**: Menyimpan kursus yang diminati

### 👨‍🏫 Untuk Instruktur

- **Manajemen Kursus**: Buat dan kelola kursus dengan mudah
- **Content Management**: Upload video, materi, dan assignment
- **Batch Management**: Kelola kelas terstruktur dengan jadwal
- **Live Sessions**: Integrasi dengan Zoom/Google Meet
- **Analytics**: Dashboard analitik performa kursus
- **Revenue Management**: Pelacakan pendapatan dan komisi
- **Student Management**: Monitoring progress siswa
- **Q&A Management**: Menjawab pertanyaan siswa

### 👨‍💼 Untuk Administrator

- **User Management**: Kelola semua pengguna platform
- **Content Moderation**: Review dan approve kursus
- **Financial Management**: Kelola komisi dan pembayaran
- **Platform Analytics**: Dashboard analitik platform
- **Verification System**: Verifikasi instruktur
- **System Configuration**: Pengaturan platform

## 🛠 Teknologi yang Digunakan

### Backend

- **Django 5.2+** - Web framework utama
- **Django REST Framework 3.14+** - API framework
- **PostgreSQL/SQLite** - Database
- **Redis** - Caching dan message broker
- **Celery** - Background tasks
- **JWT** - Authentication

### Integrasi & Tools

- **Stripe** - Payment processing
- **drf-spectacular** - API documentation
- **Django Filters** - Advanced filtering
- **Pillow** - Image processing
- **ReportLab** - PDF generation (sertifikat)
- **boto3** - AWS integration (optional)

### Development Tools

- **pytest** - Testing framework
- **Factory Boy** - Test data generation
- **Django Debug Toolbar** - Development debugging
- **Coverage** - Code coverage testing

## 📋 Persyaratan Sistem

- Python 3.11+
- PostgreSQL 14+ (atau SQLite untuk development)
- Redis 6+ (optional, untuk caching dan background tasks)
- Git

## 🔧 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/your-username/hybrid-lms.git
cd hybrid-lms
```

### 2. Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
cp .env.example .env
# Edit file .env sesuai konfigurasi Anda
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Load Sample Data (Optional)

```bash
python manage.py loaddata fixtures/sample_data.json
```

### 7. Run Development Server

```bash
python manage.py runserver
```

## 🌐 API Endpoints

### Authentication

- `POST /api/v1/auth/register/` - Registrasi pengguna baru
- `POST /api/v1/auth/login/` - Login
- `POST /api/v1/auth/logout/` - Logout
- `POST /api/v1/auth/refresh/` - Refresh token
- `GET /api/v1/auth/profile/` - Profile pengguna

### Courses

- `GET /api/v1/courses/` - List semua kursus
- `POST /api/v1/courses/` - Buat kursus baru (Instruktur)
- `GET /api/v1/courses/{id}/` - Detail kursus
- `PUT /api/v1/courses/{id}/` - Update kursus (Instruktur)
- `DELETE /api/v1/courses/{id}/` - Hapus kursus (Instruktur)

### Lessons

- `GET /api/v1/lessons/` - List lessons
- `POST /api/v1/lessons/` - Buat lesson baru
- `GET /api/v1/lessons/{id}/` - Detail lesson
- `POST /api/v1/lessons/{id}/complete/` - Tandai lesson selesai

### Assignments

- `GET /api/v1/assignments/` - List assignments
- `POST /api/v1/assignments/` - Buat assignment baru
- `GET /api/v1/assignments/{id}/` - Detail assignment
- `POST /api/v1/assignments/{id}/submit/` - Submit assignment

### Payments

- `GET /api/v1/payments/cart/` - Shopping cart
- `POST /api/v1/payments/cart/add/` - Tambah ke cart
- `POST /api/v1/payments/checkout/` - Checkout
- `GET /api/v1/payments/orders/` - History orders

### Forums

- `GET /api/v1/forums/` - List forum
- `POST /api/v1/forums/` - Buat forum post
- `GET /api/v1/forums/{id}/replies/` - Replies forum

## 📚 Dokumentasi API

Akses dokumentasi API interaktif di:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## 🧪 Testing

```bash
# Run semua tests
python manage.py test

# Run dengan coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific test
python manage.py test apps.courses.tests.test_models
```

## 📁 Struktur Proyek

```
hybrid_lms/
├── accounts/           # User management & authentication
├── courses/           # Course management
├── lessons/           # Lesson content management
├── assignments/       # Assignment & quiz system
├── forums/           # Forum & discussion system
├── payments/         # Payment & e-commerce
├── notifications/    # Notification system
├── analytics/        # Analytics & reporting
├── gamification/     # Points, badges, leaderboard
├── live_sessions/    # Live class integration
├── hybrid_lms/       # Project settings
├── static/           # Static files
├── media/            # Media uploads
├── templates/        # HTML templates
├── fixtures/         # Sample data
├── docs/             # Documentation
└── requirements.txt  # Python dependencies
```

## 🚀 Deployment

### Development

```bash
python manage.py runserver 0.0.0.0:8000
```

### Production

Lihat [PANDUAN_DEPLOYMENT.md](PANDUAN_DEPLOYMENT.md) untuk panduan lengkap deployment.

## 🤝 Kontribusi

1. Fork repository ini
2. Buat branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 Lisensi

Project ini menggunakan lisensi MIT. Lihat file [LICENSE](LICENSE) untuk detail.

## 📞 Kontak & Dukungan

- **Email**: support@hybridlms.com
- **GitHub Issues**: [Laporkan Bug](https://github.com/your-username/hybrid-lms/issues)
- **Documentation**: [Wiki](https://github.com/your-username/hybrid-lms/wiki)

## 🔗 Links Penting

- [Panduan Instalasi Lengkap](INSTALASI_LENGKAP.md)
- [Panduan Penggunaan API](PANDUAN_API.md)
- [Arsitektur Sistem](ARSITEKTUR.md)
- [Panduan Deployment](PANDUAN_DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)

---

**Dibuat dengan ❤️ menggunakan Django & Django REST Framework**
