import os
import random

import requests

from django.core.management.base import BaseCommand
from faker import Faker

from subscription_service.models import Subscription


class ServiceUrl:
    SESSION = os.getenv('BLOG_BACKEND_SESSION_URL', 'http://localhost:8082')
    PUBLICATION = os.getenv('BLOG_BACKEND_PUBLICATION_URL', 'http://localhost:8083')


fake = Faker()


class Command(BaseCommand):
    help = 'Generates fake data for db'

    users = None
    user_ids = None
    tags = None
    tag_ids = None
    publications = None
    publication_ids = None

    def add_arguments(self, parser):
        parser.add_argument('-a', '--max-subscriptions-per-author', type=int, default=0)
        parser.add_argument('-t', '--max-subscriptions-per-tag', type=int, default=0)

    def get_users(self):
        if self.users is None:
            res = requests.get(f'{ServiceUrl.SESSION}/api/v1/users/')
            self.users = res.json()
            self.user_ids = [user['id'] for user in self.users]

    def get_tags(self):
        if self.tags is None:
            res = requests.get(f'{ServiceUrl.PUBLICATION}/api/v1/tags/')
            self.tags = res.json()
            self.tag_ids = [tag['id'] for tag in self.tags]

    @staticmethod
    def fast_randint(mn, mx):
        return int(fake.random.random() * (mx - mn + 1)) + mn

    def create_authors_subscriptions(self, max_subscriptions_per_author):
        self.get_users()
        for author_id in self.user_ids:
            possible_follower_ids = [uid for uid in self.user_ids if uid != author_id]
            n_subscriptions = Command.fast_randint(0, max_subscriptions_per_author)
            Subscription.objects.bulk_create(
                [
                    Subscription(
                        type='user',
                        follower_uid=random.choice(possible_follower_ids),
                        following_uid=author_id,
                    )
                    for i in range(n_subscriptions)
                ]
            )

    def create_tags_subscriptions(self, max_subscriptions_per_tag):
        self.get_tags()
        self.get_users()
        for tag_id in self.tag_ids:
            n_subscriptions = Command.fast_randint(0, max_subscriptions_per_tag)
            Subscription.objects.bulk_create(
                [
                    Subscription(
                        type='tag',
                        follower_uid=random.choice(self.user_ids),
                        following_uid=tag_id,
                    )
                    for i in range(n_subscriptions)
                ]
            )

    def handle(self, *args, **options):
        if max_subscriptions_per_author := options['max_subscriptions_per_author']:
            print(f'Generate up to {max_subscriptions_per_author} subscriptions per tag')
            self.create_authors_subscriptions(max_subscriptions_per_author)
        if max_subscriptions_per_tag := options['max_subscriptions_per_tag']:
            print(f'Generate up to {max_subscriptions_per_tag} subscriptions per author')
            self.create_tags_subscriptions(max_subscriptions_per_tag)
