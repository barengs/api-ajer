# Generated migration for live_sessions app

import django.db.models.deletion
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
            name='LiveSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('scheduled_start', models.DateTimeField()),
                ('scheduled_end', models.DateTimeField()),
                ('actual_start', models.DateTimeField(blank=True, null=True)),
                ('actual_end', models.DateTimeField(blank=True, null=True)),
                ('platform', models.CharField(choices=[('zoom', 'Zoom'), ('google_meet', 'Google Meet'), ('teams', 'Microsoft Teams'), ('jitsi', 'Jitsi Meet'), ('custom', 'Custom Platform')], max_length=20)),
                ('meeting_url', models.URLField(blank=True)),
                ('meeting_id', models.CharField(blank=True, max_length=100)),
                ('meeting_password', models.CharField(blank=True, max_length=50)),
                ('external_meeting_data', models.JSONField(blank=True, default=dict)),
                ('max_participants', models.IntegerField(blank=True, null=True)),
                ('is_recorded', models.BooleanField(default=True)),
                ('recording_url', models.URLField(blank=True)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('live', 'Live'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='scheduled', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='live_sessions', to='courses.coursebatch')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='live_sessions', to='courses.course')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hosted_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'live_sessions',
                'ordering': ['scheduled_start'],
            },
        ),
        migrations.CreateModel(
            name='SessionAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('registered', 'Registered'), ('joined', 'Joined'), ('completed', 'Completed'), ('missed', 'Missed')], default='registered', max_length=20)),
                ('joined_at', models.DateTimeField(blank=True, null=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('total_duration_minutes', models.IntegerField(default=0)),
                ('questions_asked', models.IntegerField(default=0)),
                ('chat_messages', models.IntegerField(default=0)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='live_sessions.livesession')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_attendances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'session_attendances',
            },
        ),
        migrations.CreateModel(
            name='SessionResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('resource_type', models.CharField(choices=[('presentation', 'Presentation'), ('document', 'Document'), ('video', 'Video'), ('link', 'Link'), ('code', 'Code Sample'), ('other', 'Other')], max_length=20)),
                ('file', models.FileField(blank=True, null=True, upload_to='session_resources/')),
                ('url', models.URLField(blank=True)),
                ('shared_at', models.DateTimeField(auto_now_add=True)),
                ('is_public', models.BooleanField(default=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='live_sessions.livesession')),
                ('shared_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_resources', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'session_resources',
                'ordering': ['shared_at'],
            },
        ),
        migrations.CreateModel(
            name='SessionRecording',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recording_url', models.URLField()),
                ('external_recording_id', models.CharField(blank=True, max_length=100)),
                ('file_size_bytes', models.BigIntegerField(blank=True, null=True)),
                ('duration_minutes', models.IntegerField(blank=True, null=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('processing_status', models.CharField(blank=True, max_length=50)),
                ('download_url', models.URLField(blank=True)),
                ('thumbnail_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recording', to='live_sessions.livesession')),
            ],
            options={
                'db_table': 'session_recordings',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SessionChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('message_type', models.CharField(choices=[('text', 'Text Message'), ('system', 'System Message'), ('question', 'Question'), ('announcement', 'Announcement')], default='text', max_length=20)),
                ('is_private', models.BooleanField(default=False)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('parent_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='live_sessions.sessionchatmessage')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='live_sessions.livesession')),
            ],
            options={
                'db_table': 'session_chat_messages',
                'ordering': ['sent_at'],
            },
        ),
        migrations.CreateModel(
            name='SessionPoll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('poll_type', models.CharField(choices=[('multiple_choice', 'Multiple Choice'), ('single_choice', 'Single Choice'), ('yes_no', 'Yes/No'), ('rating', 'Rating')], max_length=20)),
                ('options', models.JSONField(default=list)),
                ('is_anonymous', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_polls', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polls', to='live_sessions.livesession')),
            ],
            options={
                'db_table': 'session_polls',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SessionPollResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_options', models.JSONField(default=list)),
                ('text_response', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='live_sessions.sessionpoll')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_responses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'session_poll_responses',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='livesession',
            index=models.Index(fields=['course', 'status'], name='live_sessions_course_status_idx'),
        ),
        migrations.AddIndex(
            model_name='livesession',
            index=models.Index(fields=['instructor', 'scheduled_start'], name='live_sessions_instructor_schedule_idx'),
        ),
        migrations.AddIndex(
            model_name='livesession',
            index=models.Index(fields=['scheduled_start', 'status'], name='live_sessions_schedule_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sessionattendance',
            index=models.Index(fields=['session', 'status'], name='session_attendances_session_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sessionattendance',
            index=models.Index(fields=['student', 'status'], name='session_attendances_student_status_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sessionattendance',
            unique_together={('session', 'student')},
        ),
        migrations.AlterUniqueTogether(
            name='sessionpollresponse',
            unique_together={('poll', 'student')},
        ),
    ]