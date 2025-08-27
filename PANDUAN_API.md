# Panduan Penggunaan API - Hybrid LMS

## 📋 Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Autentikasi](#autentikasi)
3. [Format Request & Response](#format-request--response)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Endpoint API](#endpoint-api)
7. [Contoh Penggunaan](#contoh-penggunaan)
8. [SDK & Libraries](#sdk--libraries)
9. [Testing API](#testing-api)

## 🚀 Pengenalan

Hybrid LMS API adalah RESTful API yang memungkinkan integrasi dengan platform pembelajaran hibrid yang menggabungkan self-paced learning dan structured classroom learning.

### Base URL

```
Development: http://localhost:8000/api/v1/
Production: https://api.hybridlms.com/v1/
```

### Content Type

Semua request dan response menggunakan `application/json` kecuali untuk upload file yang menggunakan `multipart/form-data`.

### Versioning

API menggunakan URL versioning dengan format `/api/v1/`. Versi saat ini adalah `v1`.

## 🔐 Autentikasi

Hybrid LMS API menggunakan JWT (JSON Web Token) untuk autentikasi.

### Mendapatkan Token

#### 1. Registrasi Pengguna Baru

```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student"
}
```

**Response:**

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "is_email_verified": false
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "verification_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Registration successful. Please check your email to verify your account."
}
```

#### 2. Login dengan Google OAuth

```http
POST /api/v1/oauth/google/
Content-Type: application/json

{
  "access_token": "google_oauth_access_token"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "full_name": "John Doe",
    "role": "student",
    "profile_image": "/media/profiles/image.jpg"
  },
  "is_new_user": false
}
```

#### 3. Login dengan Email dan Password

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Menggunakan Token

Sertakan access token dalam header Authorization untuk setiap request yang memerlukan autentikasi:

```http
GET /api/v1/courses/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Refresh Token

Access token berlaku selama 60 menit. Gunakan refresh token untuk mendapatkan access token baru:

```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 📄 Format Request & Response

### Request Format

#### GET Parameters

```http
GET /api/v1/courses/?category=programming&search=python&page=1&page_size=20
```

#### POST/PUT Body

```json
{
  "title": "Python for Beginners",
  "description": "Learn Python programming from scratch",
  "price": 99.99,
  "category": 1
}
```

#### File Upload

```http
POST /api/v1/courses/
Content-Type: multipart/form-data
Authorization: Bearer <token>

------WebKitFormBoundary
Content-Disposition: form-data; name="title"

Python for Beginners
------WebKitFormBoundary
Content-Disposition: form-data; name="thumbnail"; filename="thumbnail.jpg"
Content-Type: image/jpeg

[binary file data]
------WebKitFormBoundary--
```

### Response Format

#### Success Response

```json
{
  "id": 1,
  "title": "Python for Beginners",
  "description": "Learn Python programming from scratch",
  "price": "99.99",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Paginated Response

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/courses/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Python for Beginners",
      "description": "Learn Python programming"
    }
  ]
}
```

## ❌ Error Handling

### Error Response Format

```json
{
  "error": "Course not found",
  "detail": "Course with ID 999 does not exist",
  "code": "course_not_found"
}
```

### HTTP Status Codes

| Status Code | Meaning               | Description                    |
| ----------- | --------------------- | ------------------------------ |
| 200         | OK                    | Request berhasil               |
| 201         | Created               | Resource berhasil dibuat       |
| 400         | Bad Request           | Data request tidak valid       |
| 401         | Unauthorized          | Token tidak valid atau expired |
| 403         | Forbidden             | Tidak memiliki permission      |
| 404         | Not Found             | Resource tidak ditemukan       |
| 429         | Too Many Requests     | Rate limit exceeded            |
| 500         | Internal Server Error | Server error                   |

### Validation Errors

```json
{
  "email": ["This field is required."],
  "password": ["This password is too common."],
  "price": ["Ensure this value is greater than or equal to 0."]
}
```

## ⏱️ Rate Limiting

| Endpoint Type  | Limit        | Time Window |
| -------------- | ------------ | ----------- |
| Authentication | 5 requests   | Per minute  |
| General API    | 100 requests | Per minute  |
| File Upload    | 10 requests  | Per minute  |
| Email Sending  | 3 requests   | Per minute  |

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 🛠 Endpoint API

### Authentication

| Method | Endpoint                 | Description              | Auth Required |
| ------ | ------------------------ | ------------------------ | ------------- |
| POST   | `/auth/register/`        | Registrasi pengguna baru | ❌            |
| POST   | `/auth/login/`           | Login pengguna           | ❌            |
| POST   | `/auth/refresh/`         | Refresh access token     | ❌            |
| POST   | `/auth/logout/`          | Logout pengguna          | ✅            |
| GET    | `/auth/profile/`         | Get profile pengguna     | ✅            |
| PUT    | `/auth/profile/`         | Update profile pengguna  | ✅            |
| POST   | `/auth/verify-email/`    | Verifikasi email         | ❌            |
| POST   | `/auth/change-password/` | Ubah password            | ✅            |
| POST   | `/auth/reset-password/`  | Reset password           | ❌            |

### Courses

| Method | Endpoint                 | Description        | Auth Required    |
| ------ | ------------------------ | ------------------ | ---------------- |
| GET    | `/courses/`              | List semua kursus  | ❌               |
| POST   | `/courses/`              | Buat kursus baru   | ✅ (Instructor)  |
| GET    | `/courses/{id}/`         | Detail kursus      | ❌               |
| PUT    | `/courses/{id}/`         | Update kursus      | ✅ (Owner/Admin) |
| DELETE | `/courses/{id}/`         | Hapus kursus       | ✅ (Owner/Admin) |
| GET    | `/courses/categories/`   | List kategori      | ❌               |
| GET    | `/courses/featured/`     | Kursus featured    | ❌               |
| POST   | `/courses/{id}/enroll/`  | Enroll kursus      | ✅               |
| GET    | `/courses/{id}/reviews/` | List review kursus | ❌               |
| POST   | `/courses/{id}/reviews/` | Buat review        | ✅               |

### Lessons

| Method | Endpoint                     | Description       | Auth Required   |
| ------ | ---------------------------- | ----------------- | --------------- |
| GET    | `/lessons/`                  | List lessons      | ✅              |
| POST   | `/lessons/`                  | Buat lesson baru  | ✅ (Instructor) |
| GET    | `/lessons/{id}/`             | Detail lesson     | ✅              |
| PUT    | `/lessons/{id}/`             | Update lesson     | ✅ (Owner)      |
| DELETE | `/lessons/{id}/`             | Hapus lesson      | ✅ (Owner)      |
| POST   | `/lessons/{id}/complete/`    | Tandai selesai    | ✅              |
| GET    | `/lessons/{id}/attachments/` | List attachments  | ✅              |
| POST   | `/lessons/{id}/attachments/` | Upload attachment | ✅ (Instructor) |

### Assignments

| Method | Endpoint                               | Description       | Auth Required   |
| ------ | -------------------------------------- | ----------------- | --------------- |
| GET    | `/assignments/`                        | List assignments  | ✅              |
| POST   | `/assignments/`                        | Buat assignment   | ✅ (Instructor) |
| GET    | `/assignments/{id}/`                   | Detail assignment | ✅              |
| PUT    | `/assignments/{id}/`                   | Update assignment | ✅ (Owner)      |
| POST   | `/assignments/{id}/submit/`            | Submit assignment | ✅ (Student)    |
| GET    | `/assignments/{id}/submissions/`       | List submissions  | ✅ (Instructor) |
| PUT    | `/assignments/submissions/{id}/grade/` | Grade submission  | ✅ (Instructor) |

### Forums

| Method | Endpoint                | Description       | Auth Required    |
| ------ | ----------------------- | ----------------- | ---------------- |
| GET    | `/forums/`              | List forum posts  | ❌               |
| POST   | `/forums/`              | Buat forum post   | ✅               |
| GET    | `/forums/{id}/`         | Detail forum post | ❌               |
| PUT    | `/forums/{id}/`         | Update forum post | ✅ (Owner)       |
| DELETE | `/forums/{id}/`         | Hapus forum post  | ✅ (Owner/Admin) |
| GET    | `/forums/{id}/replies/` | List replies      | ❌               |
| POST   | `/forums/{id}/replies/` | Buat reply        | ✅               |

### Payments

| Method | Endpoint                      | Description       | Auth Required |
| ------ | ----------------------------- | ----------------- | ------------- |
| GET    | `/payments/cart/`             | Get shopping cart | ✅            |
| POST   | `/payments/cart/add/`         | Add item to cart  | ✅            |
| DELETE | `/payments/cart/remove/{id}/` | Remove from cart  | ✅            |
| POST   | `/payments/checkout/`         | Checkout cart     | ✅            |
| GET    | `/payments/orders/`           | List orders       | ✅            |
| GET    | `/payments/orders/{id}/`      | Detail order      | ✅            |
| POST   | `/payments/webhook/stripe/`   | Stripe webhook    | ❌            |

## 💡 Contoh Penggunaan

### Skenario 1: Student Mendaftar dan Mengikuti Kursus

#### 1. Registrasi

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePassword123!",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "student"
  }'
```

#### 2. Verifikasi Email

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "verification-token-from-email"
  }'
```

#### 3. Browse Kursus

```bash
curl -X GET "http://localhost:8000/api/v1/courses/?search=python&category=programming"
```

#### 4. Enroll Kursus

```bash
curl -X POST http://localhost:8000/api/v1/courses/1/enroll/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Skenario 2: Instructor Membuat Kursus

#### 1. Login sebagai Instructor

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "instructor@example.com",
    "password": "InstructorPassword123!"
  }'
```

#### 2. Buat Kursus Baru

```bash
curl -X POST http://localhost:8000/api/v1/courses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=Advanced Python Programming" \
  -F "description=Learn advanced Python concepts" \
  -F "price=149.99" \
  -F "category=1" \
  -F "course_type=self_paced" \
  -F "difficulty_level=advanced" \
  -F "thumbnail=@course_thumbnail.jpg"
```

#### 3. Tambah Lesson

```bash
curl -X POST http://localhost:8000/api/v1/lessons/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course": 1,
    "title": "Introduction to Advanced Concepts",
    "description": "Overview of what we will cover",
    "lesson_type": "video",
    "duration_minutes": 15,
    "sort_order": 1
  }'
```

### Skenario 3: Menggunakan Filter dan Search

#### Filter Kursus

```bash
# Filter berdasarkan kategori dan level
curl -X GET "http://localhost:8000/api/v1/courses/?category=programming&difficulty_level=beginner&is_free=true"

# Search dengan pagination
curl -X GET "http://localhost:8000/api/v1/courses/?search=javascript&page=2&page_size=10"

# Filter berdasarkan rating
curl -X GET "http://localhost:8000/api/v1/courses/?min_rating=4.5&sort=created_at"
```

### Skenario 4: Upload File dan Media

#### Upload Thumbnail Kursus

```bash
curl -X PUT http://localhost:8000/api/v1/courses/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "thumbnail=@new_thumbnail.jpg"
```

#### Upload Video Lesson

```bash
curl -X POST http://localhost:8000/api/v1/lessons/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "course=1" \
  -F "title=Video Lesson 1" \
  -F "description=First video lesson" \
  -F "lesson_type=video" \
  -F "video_file=@lesson_video.mp4" \
  -F "duration_minutes=30"
```

## 📚 SDK & Libraries

### JavaScript/TypeScript

```typescript
// Install: npm install axios

import axios from "axios";

class HybridLMSClient {
  private baseURL = "http://localhost:8000/api/v1";
  private accessToken: string | null = null;

  async login(email: string, password: string) {
    const response = await axios.post(`${this.baseURL}/auth/login/`, {
      email,
      password,
    });
    this.accessToken = response.data.access;
    return response.data;
  }

  async getCourses(params?: any) {
    const response = await axios.get(`${this.baseURL}/courses/`, {
      params,
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  private getAuthHeaders() {
    return this.accessToken
      ? {
          Authorization: `Bearer ${this.accessToken}`,
        }
      : {};
  }
}

// Usage
const client = new HybridLMSClient();
await client.login("user@example.com", "password");
const courses = await client.getCourses({ search: "python" });
```

### Python

```python
# Install: pip install requests

import requests
from typing import Optional, Dict, Any

class HybridLMSClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = self.session.post(f"{self.base_url}/auth/login/", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        return data

    def get_courses(self, **params) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/courses/", params=params)
        response.raise_for_status()
        return response.json()

    def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(f"{self.base_url}/courses/", json=course_data)
        response.raise_for_status()
        return response.json()

# Usage
client = HybridLMSClient()
client.login("instructor@example.com", "password")
courses = client.get_courses(search="python", category="programming")
```

### PHP

```
<?php
// Install: composer require guzzlehttp/guzzle

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

class HybridLMSClient {
    private $client;
    private $baseUrl;
    private $accessToken;

    public function __construct($baseUrl = 'http://localhost:8000/api/v1') {
        $this->baseUrl = $baseUrl;
        $this->client = new Client([
            'base_uri' => $baseUrl,
            'timeout' => 30.0,
        ]);
    }

    public function login($email, $password) {
        try {
            $response = $this->client->post('/auth/login/', [
                'json' => [
                    'email' => $email,
                    'password' => $password
                ]
            ]);

            $data = json_decode($response->getBody(), true);
            $this->accessToken = $data['access'];
            return $data;
        } catch (RequestException $e) {
            throw new Exception('Login failed: ' . $e->getMessage());
        }
    }

    public function getCourses($params = []) {
        $response = $this->client->get('/courses/', [
            'query' => $params,
            'headers' => $this->getAuthHeaders()
        ]);

        return json_decode($response->getBody(), true);
    }

    private function getAuthHeaders() {
        return $this->accessToken ? [
            'Authorization' => 'Bearer ' . $this->accessToken
        ] : [];
    }
}

// Usage
$client = new HybridLMSClient();
$client->login('user@example.com', 'password');
$courses = $client->getCourses(['search' => 'python']);
?>
```

## 🧪 Testing API

### Menggunakan cURL

#### Test Authentication

```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPassword123!", "first_name": "Test", "last_name": "User", "role": "student"}' \
  -v

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPassword123!"}' \
  -v
```

### Menggunakan Postman

#### 1. Import Collection

Download Postman collection dari `/docs/postman/hybrid_lms_api.json`

#### 2. Setup Environment

```json
{
  "base_url": "http://localhost:8000/api/v1",
  "access_token": "{{access_token}}",
  "refresh_token": "{{refresh_token}}"
}
```

#### 3. Pre-request Script untuk Auto Token Refresh

```javascript
// Pre-request script untuk endpoints yang memerlukan auth
if (!pm.globals.get("access_token") || isTokenExpired()) {
  // Refresh token jika expired
  refreshAccessToken();
}

function isTokenExpired() {
  const token = pm.globals.get("access_token");
  if (!token) return true;

  const payload = JSON.parse(atob(token.split(".")[1]));
  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

function refreshAccessToken() {
  const refreshToken = pm.globals.get("refresh_token");

  pm.sendRequest(
    {
      url: pm.globals.get("base_url") + "/auth/refresh/",
      method: "POST",
      header: {
        "Content-Type": "application/json",
      },
      body: {
        mode: "raw",
        raw: JSON.stringify({
          refresh: refreshToken,
        }),
      },
    },
    function (err, response) {
      if (!err && response.code === 200) {
        const data = response.json();
        pm.globals.set("access_token", data.access);
      }
    }
  );
}
```

### Unit Testing dengan Python

```python
import unittest
import requests
from typing import Dict, Any

class TestHybridLMSAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_user = {
            "email": "test_user@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "student"
        }
        self.access_token = None

    def test_user_registration(self):
        response = requests.post(f"{self.base_url}/auth/register/", json=self.test_user)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIn("user", data)
        self.assertIn("tokens", data)
        self.access_token = data["tokens"]["access"]

    def test_user_login(self):
        # First register
        requests.post(f"{self.base_url}/auth/register/", json=self.test_user)

        # Then login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        response = requests.post(f"{self.base_url}/auth/login/", json=login_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_get_courses_without_auth(self):
        response = requests.get(f"{self.base_url}/courses/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)

    def test_get_profile_with_auth(self):
        # Login first
        login_response = requests.post(f"{self.base_url}/auth/login/", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        access_token = login_response.json()["access"]

        # Get profile
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{self.base_url}/auth/profile/", headers=headers)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
```

### Performance Testing dengan Apache Bench

```bash
# Test endpoint login
ab -n 100 -c 10 -p login_data.json -T "application/json" \
  http://localhost:8000/api/v1/auth/login/

# Test endpoint courses (GET)
ab -n 1000 -c 50 http://localhost:8000/api/v1/courses/

# Test dengan authentication header
ab -n 500 -c 25 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/auth/profile/
```

## 📊 Monitoring dan Logging

### Response Headers untuk Monitoring

```http
X-Response-Time: 150ms
X-Request-ID: req_abc123def456
X-RateLimit-Remaining: 95
X-API-Version: 1.0.0
```

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123def456",
  "method": "POST",
  "path": "/api/v1/courses/",
  "status_code": 201,
  "response_time": 150,
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

---

**🎯 Tips untuk Developer:**

1. **Selalu gunakan HTTPS** di production
2. **Simpan refresh token dengan aman** (HttpOnly cookies recommended)
3. **Implement proper error handling** untuk semua API calls
4. **Gunakan rate limiting** untuk mencegah abuse
5. **Monitor API performance** secara regular
6. **Test API dengan berbagai scenarios** sebelum deployment
7. **Dokumentasi selalu up-to-date** dengan kode

Untuk dokumentasi interaktif lengkap, kunjungi:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
