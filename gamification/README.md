# Dokumentasi Lengkap Modul Gamifikasi

## Gambaran Umum

Modul gamifikasi menyediakan sistem komprehensif untuk meningkatkan engagement dan motivasi pengguna melalui elemen-elemen game seperti poin, badge, level, achievement, dan leaderboard. Sistem ini terintegrasi dengan drf-spectacular untuk dokumentasi API yang lengkap dalam bahasa Indonesia.

## Fitur Utama

### 1. Sistem Poin (Points System)

- **Total Points**: Akumulasi poin dari berbagai aktivitas
- **Points Transaction**: Riwayat lengkap semua transaksi poin
- **Automatic Awarding**: Pemberian poin otomatis melalui signals
- **Manual Awarding**: Admin/instructor dapat memberikan poin manual

### 2. Sistem Level (Leveling System)

- **Progressive Levels**: Level berdasarkan total poin
- **Level Perks**: Keuntungan dan privilege di setiap level
- **Automatic Progression**: Naik level otomatis saat mencapai requirement
- **Level Progress Tracking**: Tracking progress menuju level berikutnya

### 3. Sistem Badge (Badge System)

- **Badge Categories**: Learning, Social, Achievement, Instructor, Special
- **Automatic Badge Awards**: Badge diberikan otomatis berdasarkan kriteria
- **Badge Collection**: User dapat mengumpulkan berbagai badge
- **Unique Badge Constraint**: Satu badge hanya bisa earned sekali per user

### 4. Sistem Achievement (Achievement System)

- **Multiple Achievement Types**: Milestone, Speed, Excellence, Social, Consistency
- **Progress Tracking**: Tracking progress menuju achievement
- **Hidden Achievements**: Achievement tersembunyi untuk surprise factor
- **Achievement Rewards**: Poin dan badge rewards

### 5. Sistem Leaderboard (Leaderboard System)

- **Multiple Leaderboard Types**: Overall Points, Monthly Points, Course Completion, dll
- **Real-time Ranking**: Update ranking secara real-time
- **User Position**: Menampilkan posisi user di leaderboard
- **Automatic Updates**: Update otomatis melalui management command

### 6. Sistem Streak (Streak System)

- **Daily Login Streak**: Tracking streak login harian
- **Streak Bonuses**: Bonus poin untuk milestone streak
- **Streak History**: Riwayat streak terpanjang

## Struktur Database

### Models

#### BadgeType

- **name**: Nama badge (unique)
- **description**: Deskripsi badge
- **category**: Kategori badge (learning, social, achievement, instructor, special)
- **points_required**: Poin minimum untuk mendapat badge
- **icon**: Icon badge (optional)
- **is_active**: Status aktif badge

#### UserBadge

- **user**: Foreign key ke User
- **badge_type**: Foreign key ke BadgeType
- **earned_at**: Timestamp ketika badge diperoleh
- **metadata**: Data tambahan (JSON field)

#### PointsTransaction

- **user**: Foreign key ke User
- **points**: Jumlah poin (positif untuk earned, negatif untuk deducted)
- **transaction_type**: Jenis transaksi (lesson_complete, assignment_submit, dll)
- **description**: Deskripsi transaksi
- **course/lesson/assignment**: Foreign key ke objek terkait (optional)
- **metadata**: Data tambahan (JSON field)

#### UserLevel

- **level**: Nomor level (unique)
- **name**: Nama level
- **min_points**: Poin minimum untuk level
- **max_points**: Poin maksimum untuk level
- **perks**: List perks untuk level (JSON field)
- **icon**: Icon level (optional)

#### UserStats

- **user**: One-to-one ke User
- **total_points**: Total poin user
- **current_level**: Foreign key ke UserLevel
- **courses_completed**: Jumlah course selesai
- **lessons_completed**: Jumlah lesson selesai
- **assignments_submitted**: Jumlah assignment submit
- **forum_posts/replies**: Aktivitas forum
- **current_login_streak**: Streak login saat ini
- **longest_login_streak**: Streak login terpanjang

#### Achievement

- **name**: Nama achievement
- **description**: Deskripsi achievement
- **achievement_type**: Jenis achievement (milestone, speed, excellence, dll)
- **requirements**: Requirement untuk achievement (JSON field)
- **points_reward**: Poin reward
- **badge_reward**: Badge reward (optional)
- **is_hidden**: Apakah achievement tersembunyi

#### Leaderboard & LeaderboardEntry

- **Leaderboard**: Konfigurasi leaderboard
- **LeaderboardEntry**: Entry user di leaderboard dengan rank dan score

## API Endpoints

### User Endpoints

#### GET /api/v1/gamification/profile/

Mendapatkan profil gamifikasi lengkap user

- Total points dan level saat ini
- Progress ke level berikutnya
- Recent badges dan achievements
- Ranking di leaderboard
- Statistics summary

#### GET /api/v1/gamification/badges/

Mendapatkan badges user

- Filter by category
- Search by name
- Pagination dan ordering

#### GET /api/v1/gamification/achievements/

Mendapatkan achievements user dengan progress

- Show earned/unearned achievements
- Progress calculation
- Filter by type

#### GET /api/v1/gamification/points/history/

Riwayat transaksi poin user

- Filter by transaction type
- Search by description
- Date filtering

#### GET /api/v1/gamification/level/progress/

Detail progress menuju level berikutnya

- Current level info
- Next level requirements
- Progress percentage

#### POST /api/v1/gamification/daily-login/

Claim daily login bonus

- Award daily points
- Update login streak
- Streak bonuses

### Leaderboard Endpoints

#### GET /api/v1/gamification/leaderboards/

List semua leaderboard

#### GET /api/v1/gamification/leaderboards/{type}/

Detail leaderboard dengan ranking

- Top 10 performers
- User's position
- Total participants

### Browse Endpoints

#### GET /api/v1/gamification/browse/badges/

Browse available badge types

- Filter by category
- Show requirements

#### GET /api/v1/gamification/browse/achievements/

Browse available achievements

- Filter by type
- Show/hide hidden achievements

#### GET /api/v1/gamification/browse/levels/

List semua user levels

- Points requirements
- Perks dan benefits

### Admin Endpoints

#### POST /api/v1/gamification/admin/award-points/

Award poin ke user (Admin/Instructor only)

- Manual point awarding
- Link to course/lesson/assignment
- Custom metadata

#### POST /api/v1/gamification/admin/award-badge/

Award badge ke user (Admin only)

- Manual badge awarding
- Custom metadata

#### GET /api/v1/gamification/stats/

Platform gamification statistics (Admin only)

- Total points awarded
- Badge statistics
- Top earners
- Leaderboard stats

## Utility Functions

### Core Functions

#### `get_or_create_user_stats(user)`

Mendapatkan atau membuat UserStats untuk user

#### `award_points(user, points, transaction_type, description, **kwargs)`

Award poin ke user dengan otomatis:

- Membuat PointsTransaction
- Update UserStats
- Check level progression
- Trigger badge/achievement checks

#### `check_user_badges(user)`

Check dan award badge yang baru earned

#### `check_user_achievements(user)`

Check dan award achievement yang baru earned

#### `get_next_level_progress(user)`

Hitung progress menuju level berikutnya

#### `get_user_rank(user, leaderboard_type)`

Dapatkan ranking user di leaderboard tertentu

#### `update_leaderboards()`

Update semua leaderboard (untuk management command)

### Default Data Creation

#### `create_default_levels()`

Buat default user levels

#### `create_default_badges()`

Buat default badge types

#### `create_default_leaderboards()`

Buat default leaderboards

## Signal Integration

### Automatic Point Awarding

Sistem menggunakan signals untuk automatically award poin:

- **Lesson Completion**: 10 poin
- **Assignment Submission**: 15 poin
- **Quiz Pass**: 5-20 poin (based on score)
- **Course Completion**: 50 poin
- **Forum Post**: 3 poin
- **Forum Reply**: 2 poin
- **Daily Login**: 2 poin + streak bonuses

### Signal Functions

#### `trigger_lesson_complete(user, lesson, score=None)`

#### `trigger_assignment_submit(user, assignment, score=None)`

#### `trigger_course_complete(user, course)`

#### `trigger_forum_post(user, post)`

#### `trigger_forum_reply(user, reply)`

#### `trigger_daily_login(user)`

## Management Commands

### `python manage.py init_gamification`

Initialize gamification system dengan default data:

- User levels (1-20)
- Badge types (berbagai kategori)
- Default leaderboards
- Sample achievements

### `python manage.py update_leaderboards`

Update semua leaderboard rankings:

- Calculate scores berdasarkan tipe leaderboard
- Update rankings
- Handle ties

## Konfigurasi Points

```python
POINTS_CONFIG = {
    'LESSON_COMPLETE': 10,
    'ASSIGNMENT_SUBMIT': 15,
    'QUIZ_PASS_BASE': 5,
    'QUIZ_PERFECT': 20,
    'COURSE_COMPLETE': 50,
    'FORUM_POST': 3,
    'FORUM_REPLY': 2,
    'DAILY_LOGIN': 2,
    'STREAK_7_BONUS': 7,
    'STREAK_30_BONUS': 30,
    'STREAK_100_BONUS': 100,
}
```

## Badge Categories dan Examples

### Learning Badges

- **First Steps**: Complete first lesson
- **Course Finisher**: Complete first course
- **Speed Learner**: Complete course in < 7 days
- **Bookworm**: Complete 10 courses

### Social Badges

- **Conversationalist**: Make 10 forum posts
- **Helper**: Get 5 helpful votes
- **Community Leader**: Top 10 in forum activity

### Achievement Badges

- **Perfectionist**: Get 10 perfect quiz scores
- **Point Collector**: Earn 1000 points
- **Streak Master**: 30-day login streak

### Instructor Badges

- **Course Creator**: Create first course
- **Popular Instructor**: Course with 100+ enrollments

### Special Badges

- **Early Bird**: Join platform in first month
- **Beta Tester**: Participate in beta features

## Integration dengan Modul Lain

### Courses Module

- Course completion triggers
- Progress tracking
- Enrollment-based access

### Lessons Module

- Lesson completion points
- Progress calculation
- Time-based achievements

### Assignments Module

- Submission points
- Grade-based bonuses
- Deadline achievements

### Forums Module

- Post/reply points
- Helpful vote tracking
- Community achievements

### Accounts Module

- User profile integration
- Role-based permissions
- Login streak tracking

## Security dan Permissions

### User Permissions

- Users dapat view own gamification data
- Users dapat claim daily bonuses
- Users dapat browse public data

### Instructor Permissions

- Award points to their students
- View student progress
- Access course-related stats

### Admin Permissions

- Full access to all features
- Award points/badges to any user
- Manage badge types dan achievements
- View platform statistics

## Performance Considerations

### Database Optimizations

- Indexed fields untuk frequent queries
- Select_related dan prefetch_related untuk relationships
- Pagination untuk large datasets

### Caching Strategies

- Cache leaderboard data
- Cache user stats
- Cache badge/achievement progress

### Async Processing

- Background tasks untuk heavy calculations
- Celery integration untuk leaderboard updates
- Queue-based point awarding

## Testing

### Test Coverage

- Model tests untuk business logic
- API tests untuk endpoints
- Integration tests untuk complete workflows
- Signal tests untuk automatic triggers

### Test Data

- Factory classes untuk test objects
- Mock data untuk external dependencies
- Comprehensive test scenarios

## Deployment Notes

### Migration Strategy

```bash
python manage.py makemigrations gamification
python manage.py migrate
python manage.py init_gamification
```

### Production Setup

- Setup periodic tasks untuk leaderboard updates
- Configure media serving untuk badge/level icons
- Setup monitoring untuk point transactions

### Maintenance Tasks

- Regular leaderboard updates (daily/hourly)
- Badge/achievement audits
- Performance monitoring

## Future Enhancements

### Planned Features

- Team/group competitions
- Seasonal events dan challenges
- Custom badge creation
- Advanced analytics dashboard
- Mobile app integration
- Social sharing features

### API Extensions

- Webhook notifications
- Real-time updates via WebSocket
- GraphQL API
- Bulk operations API

## Troubleshooting

### Common Issues

- **Points tidak awarded**: Check signal connections
- **Level tidak update**: Verify UserStats.add_points() calls
- **Badge tidak earned**: Check badge requirements
- **Leaderboard tidak accurate**: Run update_leaderboards command

### Debug Tools

- Admin interface untuk manual operations
- Management commands untuk data verification
- Logging untuk point transactions
- Debug endpoints untuk development

## Kesimpulan

Modul gamifikasi menyediakan sistem lengkap untuk meningkatkan user engagement melalui elemen-elemen game. Dengan integrasi yang kuat dengan modul lain dan dokumentasi API yang komprehensif, sistem ini siap untuk production dan dapat dengan mudah dikembangkan sesuai kebutuhan masa depan.

Semua endpoint telah didokumentasikan dengan drf-spectacular dalam bahasa Indonesia sesuai permintaan, dengan contoh request/response yang lengkap dan jelas.
