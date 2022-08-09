from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from faker import Faker

from session_service.models import UuidUser


fake = Faker()


class Command(BaseCommand):
    help = 'Generates fake data for db'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--superuser', action='store_true')
        parser.add_argument('-u', '--users', type=int, default=0)

    @staticmethod
    def create_superuser():
        UuidUser.objects.create_superuser('admin', 'admin@example.com', 'admin')

    @staticmethod
    def create_users(n_users):
        offset_id = UuidUser.objects.count() + 1
        UuidUser.objects.bulk_create(
            [
                UuidUser(
                    first_name=(first_name := fake.first_name()),
                    last_name=(last_name := fake.last_name()),
                    username=(username := f'{first_name}{last_name}{offset_id + i}'),
                    password=make_password(f'{username}password'),
                    email=f'{username}@example.com',
                )
                for i in range(n_users)
            ]
        )

    def handle(self, *args, **options):
        if options['superuser']:
            print(f'Generate superuser')
            self.create_superuser()
        if (users := options['users']) > 0:
            print(f'Generate {users} users')
            self.create_users(users)
