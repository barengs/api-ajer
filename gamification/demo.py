#!/usr/bin/env python
"""
Contoh penggunaan sistem gamifikasi HybridLMS
Script ini mendemonstrasikan bagaimana sistem gamifikasi bekerja
"""

import os
import sys
import django
from datetime import datetime
from typing import TYPE_CHECKING, cast

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.contrib.auth import get_user_model
from gamification.models import *
from gamification.utils import *
from gamification.signals import *

if TYPE_CHECKING:
    from accounts.models import User as UserModel

User = get_user_model()

def demo_gamification_system():
    """Demonstrasi lengkap sistem gamifikasi"""
    
    print("🎮 Demo Sistem Gamifikasi HybridLMS")
    print("=" * 50)
    
    # 1. Setup initial data
    print("\n1. 📊 Setup Data Awal...")
    
    # Buat user contoh
    try:
        user = cast('UserModel', User.objects.get(username='demo_user'))
        print(f"   ✓ User ditemukan: {user.username}")
    except User.DoesNotExist:
        user = cast('UserModel', User.objects.create_user(  # type: ignore
            username='demo_user',
            email='demo@example.com',
            password='demo123',
            first_name='Demo',
            last_name='User'
        ))
        print(f"   ✓ User dibuat: {user.username}")
    
    # Initialize gamification data
    create_default_levels()
    create_default_badges()
    create_default_leaderboards()
    print("   ✓ Default gamification data initialized")
    
    # 2. Simulasi aktivitas pembelajaran
    print("\n2. 📚 Simulasi Aktivitas Pembelajaran...")
    
    # Simulasi menyelesaikan lessons
    for i in range(1, 6):
        award_points(
            user,
            10,
            PointsTransaction.TransactionType.LESSON_COMPLETE,
            f'Menyelesaikan lesson {i}'
        )
        print(f"   ✓ Lesson {i} selesai - earned 10 points")
    
    # Simulasi submit assignment
    award_points(
        user,
        15,
        PointsTransaction.TransactionType.ASSIGNMENT_SUBMIT,
        'Submit assignment pertama'
    )
    print("   ✓ Assignment submitted - earned 15 points")
    
    # Simulasi quiz perfect score
    award_points(
        user,
        20,
        PointsTransaction.TransactionType.PERFECT_SCORE,
        'Perfect score di quiz'
    )
    print("   ✓ Perfect quiz score - earned 20 points")
    
    # 3. Check user progress
    print("\n3. 📈 Progress User Saat Ini...")
    
    stats = get_or_create_user_stats(user)
    stats.refresh_from_db()
    
    print(f"   Total Points: {stats.total_points}")
    print(f"   Current Level: {stats.current_level.name if stats.current_level else 'None'}")
    print(f"   Lessons Completed: {stats.lessons_completed}")
    
    # 4. Check badges earned
    print("\n4. 🏆 Badges yang Diperoleh...")
    
    check_user_badges(user)
    user_badges = UserBadge.objects.filter(user=user)
    
    if user_badges.exists():
        for badge in user_badges:
            print(f"   🏅 {badge.badge_type.name}: {badge.badge_type.description}")
    else:
        print("   Belum ada badge yang diperoleh")
    
    # 5. Simulasi aktivitas forum
    print("\n5. 💬 Simulasi Aktivitas Forum...")
    
    # Simulasi forum posts
    for i in range(3):
        award_points(
            user,
            3,
            PointsTransaction.TransactionType.FORUM_POST,
            f'Forum post {i+1}'
        )
        stats.forum_posts += 1
        stats.save()
        print(f"   ✓ Forum post {i+1} - earned 3 points")
    
    # 6. Simulasi daily login streak
    print("\n6. 📅 Simulasi Daily Login...")
    
    trigger_daily_login(user)
    stats.refresh_from_db()
    print(f"   ✓ Daily login bonus - Current streak: {stats.current_login_streak}")
    
    # 7. Check achievements
    print("\n7. 🏆 Check Achievements...")
    
    check_user_achievements(user)
    user_achievements = UserAchievement.objects.filter(user=user)
    
    if user_achievements.exists():
        for achievement in user_achievements:
            print(f"   🎖️  {achievement.achievement.name}: {achievement.achievement.description}")
    else:
        print("   Belum ada achievement yang di-unlock")
    
    # 8. Level progression
    print("\n8. 🚀 Level Progression...")
    
    progress = get_next_level_progress(user)
    print(f"   Current Level: {progress.get('current_level_name', 'N/A')}")
    print(f"   Current Points: {progress.get('current_points', 0)}")
    print(f"   Next Level: {progress.get('next_level_name', 'Max Level')}")
    print(f"   Points Needed: {progress.get('points_needed', 0)}")
    print(f"   Progress: {progress.get('progress_percentage', 0):.1f}%")
    
    # 9. Leaderboard position
    print("\n9. 🏅 Leaderboard Position...")
    
    update_leaderboards()
    
    overall_rank = get_user_rank(user, Leaderboard.LeaderboardType.OVERALL_POINTS)
    monthly_rank = get_user_rank(user, Leaderboard.LeaderboardType.MONTHLY_POINTS)
    
    print(f"   Overall Ranking: #{overall_rank}" if overall_rank else "   Overall Ranking: Not ranked")
    print(f"   Monthly Ranking: #{monthly_rank}" if monthly_rank else "   Monthly Ranking: Not ranked")
    
    # 10. Transaction history
    print("\n10. 📊 Recent Transaction History...")
    
    recent_transactions = PointsTransaction.objects.filter(user=user).order_by('-created_at')[:5]
    
    for transaction in recent_transactions:
        print(f"   {transaction.created_at.strftime('%Y-%m-%d %H:%M')} | "
              f"{transaction.points:+3d} pts | {transaction.description}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Demo Selesai!")
    stats.refresh_from_db()
    print(f"📊 Final Stats:")
    print(f"   • Total Points: {stats.total_points}")
    print(f"   • Level: {stats.current_level.name if stats.current_level else 'Beginner'}")
    print(f"   • Badges: {UserBadge.objects.filter(user=user).count()}")
    print(f"   • Achievements: {UserAchievement.objects.filter(user=user).count()}")
    print(f"   • Login Streak: {stats.current_login_streak}")
    print(f"   • Forum Posts: {stats.forum_posts}")
    
    print(f"\n✨ User {user.username} berhasil memulai journey gamifikasi!")


def demo_admin_functions():
    """Demo fungsi admin untuk award manual"""
    
    print("\n🔧 Demo Admin Functions")
    print("=" * 30)
    
    try:
        user = cast('UserModel', User.objects.get(username='demo_user'))
    except User.DoesNotExist:
        print("❌ Demo user tidak ditemukan. Jalankan demo_gamification_system() dulu.")
        return
    
    # Award bonus points
    print("\n1. 💎 Award Bonus Points...")
    award_points(
        user,
        100,
        PointsTransaction.TransactionType.BONUS,
        'Admin bonus untuk user aktif'
    )
    print("   ✓ 100 bonus points awarded")
    
    # Award special badge
    print("\n2. 🏅 Award Special Badge...")
    try:
        special_badge = BadgeType.objects.get(name='Special Contributor')
        UserBadge.objects.create(
            user=user,
            badge_type=special_badge,
            metadata={'reason': 'Outstanding contribution to community'}
        )
        print("   ✓ Special badge awarded")
    except BadgeType.DoesNotExist:
        print("   ⚠️  Special badge type not found")
    
    # Check final stats
    stats = UserStats.objects.get(user=user)
    print(f"\n📈 Updated Stats:")
    print(f"   Total Points: {stats.total_points}")
    print(f"   Level: {stats.current_level.name if stats.current_level else 'Beginner'}")


if __name__ == '__main__':
    try:
        print("🚀 Memulai demo sistem gamifikasi...\n")
        
        # Run main demo
        demo_gamification_system()
        
        # Ask for admin demo
        run_admin = input("\n❓ Jalankan demo admin functions? (y/n): ").lower()
        if run_admin == 'y':
            demo_admin_functions()
        
        print("\n✅ Demo berhasil dijalankan!")
        print("💡 Tip: Lihat Django admin untuk melihat data yang dibuat")
        print("🌐 Akses API endpoints di /api/docs/ untuk testing")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Pastikan database sudah di-migrate dan Django settings sudah benar")