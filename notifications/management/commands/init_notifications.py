from django.core.management.base import BaseCommand
from notifications.models import EmailTemplate


class Command(BaseCommand):
    help = 'Initialize default email templates for notifications'
    
    def handle(self, *args, **options):
        # Define default templates
        templates = [
            {
                'name': 'Welcome Email',
                'template_type': EmailTemplate.TemplateType.WELCOME,
                'subject': 'Welcome to Our Platform',
                'body': '''Hello {user_name},

Welcome to our learning platform! We're excited to have you join our community.

Start exploring our courses and begin your learning journey today.

Best regards,
The Team'''
            },
            {
                'name': 'Course Enrollment',
                'template_type': EmailTemplate.TemplateType.COURSE_ENROLLMENT,
                'subject': 'New Enrollment in {title}',
                'body': '''Hello {user_name},

Good news! A new student has enrolled in your course "{title}".

Student: {user_name}
Course: {title}

Keep up the great work creating valuable content!

Best regards,
The Team'''
            },
            {
                'name': 'Course Review',
                'template_type': EmailTemplate.TemplateType.COURSE_REVIEW,
                'subject': 'New Review for {title}',
                'body': '''Hello {user_name},

A student has left a review for your course "{title}".

Review: {message}

Thank you for being part of our teaching community!

Best regards,
The Team'''
            },
            {
                'name': 'Assignment Due Reminder',
                'template_type': EmailTemplate.TemplateType.ASSIGNMENT_DUE,
                'subject': 'Assignment Due Soon',
                'body': '''Hello {user_name},

This is a reminder that your assignment for "{title}" is due soon.

Please make sure to submit your work on time.

Best regards,
The Team'''
            },
            {
                'name': 'Payment Confirmation',
                'template_type': EmailTemplate.TemplateType.PAYMENT_CONFIRMATION,
                'subject': 'Payment Confirmation',
                'body': '''Hello {user_name},

Thank you for your payment. This email confirms your payment has been processed successfully.

Details:
{message}

If you have any questions, please contact our support team.

Best regards,
The Team'''
            },
            {
                'name': 'Certificate Awarded',
                'template_type': EmailTemplate.TemplateType.CERTIFICATE_AWARDED,
                'subject': 'Certificate Awarded',
                'body': '''Hello {user_name},

Congratulations! You have been awarded a certificate for completing "{title}".

You can view and download your certificate from your profile.

Best regards,
The Team'''
            },
            {
                'name': 'Forum Reply',
                'template_type': EmailTemplate.TemplateType.FORUM_REPLY,
                'subject': 'New Reply in Forum',
                'body': '''Hello {user_name},

Someone has replied to your forum post in "{title}".

Message: {message}

Best regards,
The Team'''
            },
            {
                'name': 'Password Reset',
                'template_type': EmailTemplate.TemplateType.PASSWORD_RESET,
                'subject': 'Password Reset Request',
                'body': '''Hello {user_name},

You have requested to reset your password. Click the link below to reset your password:

{message}

If you did not request this, please ignore this email.

Best regards,
The Team'''
            }
        ]
        
        # Create templates
        created_count = 0
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created template: {template_data["name"]}'
                    )
                )
            else:
                self.stdout.write(
                    f'Template already exists: {template_data["name"]}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized {created_count} email templates'
            )
        )