from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from typing import Any

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer, 
    NotificationPreferenceSerializer,
    NotificationCreateSerializer,
    NotificationBulkReadSerializer
)
from accounts.models import User


@extend_schema(
    operation_id='notifications_list',
    tags=['Notifications'],
    summary='Daftar Notifikasi User',
    description='''
    Mendapatkan semua notifikasi untuk user yang login.
    
    **Filtering Options:**
    - type: Filter berdasarkan jenis notifikasi
    - read: Filter berdasarkan status baca (true/false)
    - priority: Filter berdasarkan prioritas
    
    **Jenis Notifikasi:**
    - enrollment: Pendaftaran kursus baru
    - review: Ulasan kursus baru
    - assignment: Pengingat tugas
    - course_update: Update kursus
    - payment: Konfirmasi pembayaran
    - certificate: Sertifikat yang diperoleh
    - forum: Aktivitas forum
    - system: Notifikasi sistem
    
    **Status Notifikasi:**
    - Read: Sudah dibaca user
    - Unread: Belum dibaca user
    ''',
    parameters=[
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by notification type'
        ),
        OpenApiParameter(
            name='read',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter by read status'
        ),
        OpenApiParameter(
            name='priority',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filter by priority level'
        ),
    ],
    responses={
        200: {
            'description': 'Daftar notifikasi berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'notifications': [
                            {
                                'id': 1,
                                'title': 'New Student Enrollment',
                                'message': 'John Doe enrolled in your course: Python Programming',
                                'notification_type': 'enrollment',
                                'priority': 2,
                                'is_read': False,
                                'created_at': '2024-01-15T10:30:00Z',
                                'read_at': None
                            }
                        ],
                        'unread_count': 1
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list(request):
    """Get user notifications"""
    user = request.user
    notifications = Notification.objects.filter(user=user)
    
    # Apply filters
    notification_type = request.query_params.get('type')
    read_status = request.query_params.get('read')
    priority = request.query_params.get('priority')
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if read_status is not None:
        if read_status.lower() == 'true':
            notifications = notifications.filter(is_read=True)
        elif read_status.lower() == 'false':
            notifications = notifications.filter(is_read=False)
    
    if priority:
        try:
            priority = int(priority)
            notifications = notifications.filter(priority=priority)
        except ValueError:
            pass
    
    # Serialize notifications
    serializer = NotificationSerializer(notifications, many=True)
    
    # Get unread count
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    return Response({
        'notifications': serializer.data,
        'unread_count': unread_count
    })


@extend_schema(
    operation_id='notifications_retrieve',
    tags=['Notifications'],
    summary='Detail Notifikasi',
    description='''
    Mendapatkan detail notifikasi berdasarkan ID.
    
    **Auto-mark as read:**
    Notifikasi akan otomatis ditandai sebagai sudah dibaca
    ketika detailnya diakses.
    ''',
    parameters=[
        OpenApiParameter(
            name='notification_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID notifikasi'
        )
    ],
    responses={
        200: {
            'description': 'Detail notifikasi berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'title': 'New Student Enrollment',
                        'message': 'John Doe enrolled in your course: Python Programming',
                        'notification_type': 'enrollment',
                        'priority': 2,
                        'is_read': True,
                        'created_at': '2024-01-15T10:30:00Z',
                        'read_at': '2024-01-15T11:00:00Z'
                    }
                }
            }
        },
        404: {
            'description': 'Notifikasi tidak ditemukan'
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_detail(request, notification_id):
    """Get notification detail"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    # Mark as read when accessed
    if not notification.is_read:
        notification.mark_as_read()
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)


@extend_schema(
    tags=['Notifications'],
    summary='Tandai Notifikasi Sudah Dibaca',
    description='''
    Menandai notifikasi sebagai sudah dibaca.
    
    **Efek marking as read:**
    - Status notifikasi berubah menjadi 'read'
    - Unread count berkurang
    - Notifikasi tidak lagi muncul sebagai unread
    ''',
    parameters=[
        OpenApiParameter(
            name='notification_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID notifikasi yang akan ditandai sudah dibaca'
        )
    ],
    responses={
        200: {
            'description': 'Notifikasi berhasil ditandai sudah dibaca',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Notification marked as read'
                    }
                }
            }
        },
        404: {
            'description': 'Notifikasi tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.mark_as_read()
    return Response({'message': 'Notification marked as read'})


@extend_schema(
    tags=['Notifications'],
    summary='Tandai Notifikasi Belum Dibaca',
    description='''
    Menandai notifikasi sebagai belum dibaca.
    
    **Efek marking as unread:**
    - Status notifikasi berubah menjadi 'unread'
    - Unread count bertambah
    - Notifikasi akan muncul sebagai unread
    ''',
    parameters=[
        OpenApiParameter(
            name='notification_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID notifikasi yang akan ditandai belum dibaca'
        )
    ],
    responses={
        200: {
            'description': 'Notifikasi berhasil ditandai belum dibaca',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Notification marked as unread'
                    }
                }
            }
        },
        404: {
            'description': 'Notifikasi tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_unread(request, notification_id):
    """Mark notification as unread"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.mark_as_unread()
    return Response({'message': 'Notification marked as unread'})


@extend_schema(
    tags=['Notifications'],
    summary='Tandai Semua Notifikasi Sudah Dibaca',
    description='''
    Menandai semua notifikasi user sebagai sudah dibaca.
    
    **Efek marking all as read:**
    - Semua notifikasi unread berubah menjadi read
    - Unread count menjadi 0
    ''',
    responses={
        200: {
            'description': 'Semua notifikasi berhasil ditandai sudah dibaca',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'All notifications marked as read',
                        'marked_count': 5
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """Mark all notifications as read"""
    user = request.user
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    )
    
    marked_count = unread_notifications.count()
    
    # Mark all as read
    unread_notifications.update(
        is_read=True,
        read_at=user.date_joined  # Using date_joined as a placeholder
    )
    
    return Response({
        'message': 'All notifications marked as read',
        'marked_count': marked_count
    })


@extend_schema(
    tags=['Notifications'],
    summary='Hapus Notifikasi',
    description='''
    Menghapus notifikasi berdasarkan ID.
    
    **Efek deletion:**
    - Notifikasi dihapus permanen dari database
    - Unread count berkurang jika notifikasi belum dibaca
    ''',
    parameters=[
        OpenApiParameter(
            name='notification_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID notifikasi yang akan dihapus'
        )
    ],
    responses={
        200: {
            'description': 'Notifikasi berhasil dihapus',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Notification deleted successfully'
                    }
                }
            }
        },
        404: {
            'description': 'Notifikasi tidak ditemukan'
        }
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_notification(request, notification_id):
    """Delete notification"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.delete()
    return Response({'message': 'Notification deleted successfully'})


@extend_schema(
    tags=['Notifications'],
    summary='Arsipkan Notifikasi',
    description='''
    Mengarsipkan notifikasi berdasarkan ID.
    
    **Efek archiving:**
    - Notifikasi ditandai sebagai diarsipkan
    - Tidak akan muncul dalam daftar notifikasi default
    - Dapat di-unarchive jika diperlukan
    ''',
    parameters=[
        OpenApiParameter(
            name='notification_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID notifikasi yang akan diarsipkan'
        )
    ],
    responses={
        200: {
            'description': 'Notifikasi berhasil diarsipkan',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Notification archived successfully'
                    }
                }
            }
        },
        404: {
            'description': 'Notifikasi tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def archive_notification(request, notification_id):
    """Archive notification"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.is_archived = True
    notification.save()
    return Response({'message': 'Notification archived successfully'})


@extend_schema(
    tags=['Notifications'],
    summary='Preferensi Notifikasi',
    description='''
    Mendapatkan dan mengupdate preferensi notifikasi user.
    
    **Preference Types:**
    - Email notifications: Kirim notifikasi via email
    - In-app notifications: Tampilkan notifikasi di aplikasi
    - Push notifications: Kirim notifikasi push (mobile)
    
    **Category Preferences:**
    - Course updates
    - Assignments
    - Forum activity
    - Payments
    ''',
    responses={
        200: {
            'description': 'Preferensi notifikasi berhasil diambil/diupdate',
            'content': {
                'application/json': {
                    'example': {
                        'email_notifications': True,
                        'email_course_updates': True,
                        'email_assignments': True,
                        'email_forum_activity': True,
                        'email_payments': True,
                        'in_app_notifications': True,
                        'in_app_course_updates': True,
                        'in_app_assignments': True,
                        'in_app_forum_activity': True,
                        'in_app_payments': True,
                        'push_notifications': True,
                        'push_course_updates': True,
                        'push_assignments': True,
                        'push_forum_activity': True,
                        'push_payments': True,
                        'updated_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        }
    }
)
class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get or update notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self) -> Any:
        # Get or create notification preferences for user
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences


@extend_schema(
    tags=['Notifications'],
    summary='Statistik Notifikasi',
    description='''
    Mendapatkan statistik notifikasi user.
    
    **Metrics Provided:**
    - Total notifications
    - Unread count
    - Read count
    - Archived count
    - Notifications by type
    - Notifications by priority
    ''',
    responses={
        200: {
            'description': 'Statistik notifikasi berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'total': 25,
                        'unread': 5,
                        'read': 20,
                        'archived': 3,
                        'by_type': {
                            'enrollment': 10,
                            'review': 5,
                            'assignment': 7,
                            'system': 3
                        },
                        'by_priority': {
                            '1': 5,
                            '2': 15,
                            '3': 4,
                            '4': 1
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics"""
    user = request.user
    
    # Basic counts
    total = Notification.objects.filter(user=user).count()
    unread = Notification.objects.filter(user=user, is_read=False).count()
    read = total - unread
    archived = Notification.objects.filter(user=user, is_archived=True).count()
    
    # Count by type
    by_type = dict(
        Notification.objects.filter(user=user)
        .values('notification_type')
        .annotate(count=Count('id'))
        .values_list('notification_type', 'count')
    )
    
    # Count by priority
    by_priority = dict(
        Notification.objects.filter(user=user)
        .values('priority')
        .annotate(count=Count('id'))
        .values_list('priority', 'count')
    )
    
    return Response({
        'total': total,
        'unread': unread,
        'read': read,
        'archived': archived,
        'by_type': by_type,
        'by_priority': by_priority
    })


@extend_schema(
    tags=['Notifications'],
    summary='Tandai Banyak Notifikasi Sudah Dibaca',
    description='''
    Menandai beberapa notifikasi sebagai sudah dibaca dalam satu request.
    
    **Request Body:**
    - notification_ids: Array of notification IDs to mark as read
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'notification_ids': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'List of notification IDs to mark as read'
                }
            },
            'required': ['notification_ids']
        }
    },
    examples=[
        OpenApiExample(
            'Bulk Read Request',
            value={
                'notification_ids': [1, 2, 3, 4, 5]
            },
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Notifikasi berhasil ditandai sudah dibaca',
            'content': {
                'application/json': {
                    'example': {
                        'message': '5 notifications marked as read',
                        'marked_count': 5
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Invalid data'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_mark_read(request):
    """Mark multiple notifications as read"""
    serializer = NotificationBulkReadSerializer(data=request.data)
    if serializer.is_valid():
        # Check that validated_data is a dict and has the expected key
        if isinstance(serializer.validated_data, dict) and 'notification_ids' in serializer.validated_data:
            notification_ids = serializer.validated_data['notification_ids']
            
            # Filter to only user's notifications
            notifications = Notification.objects.filter(
                id__in=notification_ids,
                user=request.user,
                is_read=False
            )
            
            marked_count = notifications.count()
            notifications.update(is_read=True, read_at=request.user.date_joined)
            
            return Response({
                'message': f'{marked_count} notifications marked as read',
                'marked_count': marked_count
            })
        else:
            return Response({'error': 'Invalid data structure'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)