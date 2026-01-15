"""
Management command to check if a user exists and optionally create them.
Usage: python manage.py check_user <email>
"""
from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = 'Check if a user exists by email and display their info'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to check')
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create the user if they don\'t exist'
        )
        parser.add_argument('--first-name', type=str, default='', help='First name for new user')
        parser.add_argument('--last-name', type=str, default='', help='Last name for new user')
        parser.add_argument('--is-mentor', action='store_true', help='Mark as mentor')
        parser.add_argument('--is-mentee', action='store_true', help='Mark as mentee')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'\n✓ User found: {email}'))
            self.stdout.write(f'  ID: {user.id}')
            self.stdout.write(f'  Name: {user.first_name} {user.last_name}')
            self.stdout.write(f'  Role: {user.role}')
            self.stdout.write(f'  Is Mentor: {user.is_mentor}')
            self.stdout.write(f'  Is Mentee: {user.is_mentee}')
            self.stdout.write(f'  Approval Status: {user.approval_status}')
            self.stdout.write(f'  Date Joined: {user.date_joined}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\n✗ User NOT found: {email}'))
            
            if options['create']:
                self.stdout.write(self.style.WARNING('\nCreating user...'))
                user = User.objects.create_user(
                    email=email,
                    first_name=options['first_name'],
                    last_name=options['last_name'],
                    is_mentor=options['is_mentor'],
                    is_mentee=options['is_mentee'],
                    approval_status='approved',  # Auto-approve for now
                )
                self.stdout.write(self.style.SUCCESS(f'\n✓ User created successfully!'))
                self.stdout.write(f'  ID: {user.id}')
                self.stdout.write(f'  Email: {user.email}')
            else:
                self.stdout.write(self.style.WARNING('\nTo create this user, run:'))
                self.stdout.write(f'  python manage.py check_user "{email}" --create --first-name "First" --last-name "Last" --is-mentee')
