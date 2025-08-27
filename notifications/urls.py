from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

@extend_schema(
    tags=['Notifications'],
    summary='Daftar Notifikasi User',
    description='''
    Mendapatkan semua notifikasi untuk user yang login.
    
    **Jenis Notifikasi:**
    - Course updates: Update kursus yang diikuti
    - Assignment reminders: Pengingat deadline assignment
    - Forum activity: Reply atau vote pada forum posts
    - Payment confirmations: Konfirmasi pembayaran
    - Certificate awards: Sertifikat yang diperoleh
    
    **Status Notifikasi:**
    - Read: Sudah dibaca user
    - Unread: Belum dibaca user
    
    **Note:** Ini adalah placeholder implementation.
    Sistem notifikasi lengkap akan diimplementasikan
    dengan real-time updates menggunakan WebSocket.
    ''',
    responses={
        200: {
            'description': 'Daftar notifikasi berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'notifications': [],
                        'unread_count': 0,
                        'message': 'Notification system placeholder - ready for implementation'
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """Get user notifications (placeholder)"""
    return Response({
        'notifications': [],
        'unread_count': 0,
        'message': 'Notification system placeholder - ready for implementation'
    })

@extend_schema(
    tags=['Notifications'],
    summary='Tandai Notifikasi Sudah Dibaca',
    description='''
    Menandai notifikasi sebagai sudah dibaca.
    
    **Efek marking as read:**
    - Status notifikasi berubah menjadi 'read'
    - Unread count berkurang
    - Notifikasi tidak lagi muncul sebagai unread
    
    **Real-time Updates:**
    Dalam implementasi lengkap, perubahan status
    akan di-broadcast via WebSocket untuk real-time updates.
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
@permission_classes([IsAuthenticated])
def mark_read(request, notification_id):
    """Mark notification as read (placeholder)"""
    return Response({'message': 'Notification marked as read'})

urlpatterns = [
    path('', notification_list, name='notification_list'),
    path('<int:notification_id>/read/', mark_read, name='mark_notification_read'),
]