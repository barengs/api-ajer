# Generated migration for analytics app

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('total_users', models.IntegerField(default=0)),
                ('new_users', models.IntegerField(default=0)),
                ('active_users', models.IntegerField(default=0)),
                ('total_courses', models.IntegerField(default=0)),
                ('new_courses', models.IntegerField(default=0)),
                ('published_courses', models.IntegerField(default=0)),
                ('total_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('daily_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('refunds', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_enrollments', models.IntegerField(default=0)),
                ('new_enrollments', models.IntegerField(default=0)),
                ('completed_courses', models.IntegerField(default=0)),
                ('forum_posts', models.IntegerField(default=0)),
                ('lesson_completions', models.IntegerField(default=0)),
                ('assignment_submissions', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'platform_metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='AnalyticsSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot_type', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], max_length=20)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('platform_data', models.JSONField(default=dict)),
                ('instructor_data', models.JSONField(default=dict)),
                ('course_data', models.JSONField(default=dict)),
                ('student_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'analytics_snapshots',
                'ordering': ['-period_end'],
            },
        ),
        migrations.CreateModel(
            name='StudentMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('courses_enrolled', models.IntegerField(default=0)),
                ('courses_completed', models.IntegerField(default=0)),
                ('courses_in_progress', models.IntegerField(default=0)),
                ('lessons_completed', models.IntegerField(default=0)),
                ('assignments_submitted', models.IntegerField(default=0)),
                ('quizzes_taken', models.IntegerField(default=0)),
                ('forum_posts', models.IntegerField(default=0)),
                ('total_study_time_minutes', models.IntegerField(default=0)),
                ('daily_study_time_minutes', models.IntegerField(default=0)),
                ('login_streak', models.IntegerField(default=0)),
                ('average_quiz_score', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('completion_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('total_points', models.IntegerField(default=0)),
                ('badges_earned', models.IntegerField(default=0)),
                ('achievements_unlocked', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'student_metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='InstructorMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_courses', models.IntegerField(default=0)),
                ('published_courses', models.IntegerField(default=0)),
                ('draft_courses', models.IntegerField(default=0)),
                ('total_students', models.IntegerField(default=0)),
                ('new_students', models.IntegerField(default=0)),
                ('active_students', models.IntegerField(default=0)),
                ('total_earnings', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('daily_earnings', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('average_rating', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=3)),
                ('total_reviews', models.IntegerField(default=0)),
                ('completion_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('forum_interactions', models.IntegerField(default=0)),
                ('student_questions', models.IntegerField(default=0)),
                ('response_time_hours', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instructor_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'instructor_metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='CourseMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_enrollments', models.IntegerField(default=0)),
                ('new_enrollments', models.IntegerField(default=0)),
                ('active_students', models.IntegerField(default=0)),
                ('completed_students', models.IntegerField(default=0)),
                ('average_progress', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('completion_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('dropout_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('daily_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('lesson_views', models.IntegerField(default=0)),
                ('assignment_submissions', models.IntegerField(default=0)),
                ('forum_posts', models.IntegerField(default=0)),
                ('quiz_attempts', models.IntegerField(default=0)),
                ('average_rating', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=3)),
                ('total_reviews', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_metrics', to='courses.course')),
            ],
            options={
                'db_table': 'course_metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.AddIndex(
            model_name='platformmetrics',
            index=models.Index(fields=['date'], name='platform_me_date_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='platformmetrics',
            index=models.Index(fields=['-date'], name='platform_me_date_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='studentmetrics',
            index=models.Index(fields=['student', 'date'], name='student_met_student_b02db0_idx'),
        ),
        migrations.AddIndex(
            model_name='studentmetrics',
            index=models.Index(fields=['date'], name='student_met_date_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='instructormetrics',
            index=models.Index(fields=['instructor', 'date'], name='instructor__instruc_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='instructormetrics',
            index=models.Index(fields=['date'], name='instructor__date_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='coursemetrics',
            index=models.Index(fields=['course', 'date'], name='course_metr_course__b02db0_idx'),
        ),
        migrations.AddIndex(
            model_name='coursemetrics',
            index=models.Index(fields=['date'], name='course_metr_date_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='analyticssnapshot',
            index=models.Index(fields=['snapshot_type', 'period_end'], name='analytics_s_snapsho_9393e2_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='studentmetrics',
            unique_together={('student', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='instructormetrics',
            unique_together={('instructor', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='coursemetrics',
            unique_together={('course', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='analyticssnapshot',
            unique_together={('snapshot_type', 'period_start', 'period_end')},
        ),
    ]