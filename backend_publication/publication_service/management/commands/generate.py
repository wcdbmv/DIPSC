import os
import random

import requests

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from faker import Faker

from publication_service.models import Tag, Vote, Publication, Comment


class ServiceUrl:
    SESSION = os.getenv('BLOG_BACKEND_SESSION_URL', 'http://localhost:8082')


fake = Faker()


class Command(BaseCommand):
    help = 'Generates fake data for db'
    users = None
    user_ids = None

    def add_arguments(self, parser):
        parser.add_argument('-t', '--tags', type=int, default=0)
        parser.add_argument('-T', '--max-tags-per-publication', type=int, default=0)
        parser.add_argument('-s', '--max-sentences-per-publication', type=int, default=15)
        parser.add_argument('-p', '--publications', type=int, default=0)
        parser.add_argument('-S', '--max-sentences-per-comment', type=int, default=8)
        parser.add_argument('-c', '--comments', type=int, default=0)
        parser.add_argument('-P', '--max-votes-per-publication', type=int, default=0)
        parser.add_argument('-C', '--max-votes-per-comment', type=int, default=0)

    def get_users(self):
        if self.users is None:
            res = requests.get(ServiceUrl.SESSION + '/api/v1/users/')
            self.users = res.json()
            self.user_ids = [user['id'] for user in self.users]

    @staticmethod
    def create_tags(tags):
        offset_id = Tag.objects.count() + 1
        Tag.objects.bulk_create(
            [
                Tag(
                    name=f'{fake.word()}{offset_id + i}',
                )
                for i in range(tags)
            ]
        )

    @staticmethod
    def fast_randint(mn, mx):
        return int(fake.random.random() * (mx - mn + 1)) + mn

    @staticmethod
    def fast_vote(kindness_coefficient=0.5):
        return 1 if fake.random.random() < kindness_coefficient else -1

    def create_publications(self, publications, max_tags_per_publication, max_sentences_per_publication):
        self.get_users()
        Publication.objects.bulk_create(
            [
                Publication(
                    title=fake.sentence(),
                    body=fake.paragraph(nb_sentences=max_sentences_per_publication),
                    author_uid=random.choice(self.user_ids),
                )
                for i in range(publications)
            ]
        )

        through_model = Publication.tags.through
        tag_ids = list(Tag.objects.values_list('id', flat=True))  # list for sample()
        publication_ids = list(Publication.objects.values_list('id', flat=True))
        through_list = []
        for publication_id in publication_ids:
            n_tags = Command.fast_randint(0, max_tags_per_publication)
            through_list += [
                through_model(
                    publication_id=publication_id,
                    tag_id=tag_id,
                )
                for tag_id in fake.random.sample(tag_ids, n_tags)
            ]
        through_model.objects.bulk_create(through_list)

    def create_comments(self, comments, max_sentences_per_comment):
        self.get_users()
        publication_ids = list(Publication.objects.values_list('id', flat=True))  # list for sample()
        Comment.objects.bulk_create(
            [
                Comment(
                    body=fake.paragraph(nb_sentences=max_sentences_per_comment),
                    author_uid=random.choice(self.user_ids),
                    publication_id=random.choice(publication_ids),
                )
                for i in range(comments)
            ]
        )

    def generate_votes_for_model(self, model_cls, max_votes_per_publication):
        if max_votes_per_publication == 0:
            return

        models = model_cls.objects.all()
        model_type_id = ContentType.objects.get_for_model(model_cls).id

        votes = []
        for model in models:
            n_votes = Command.fast_randint(0, max_votes_per_publication)
            rating = 0
            kindness_coefficient = fake.random.random()
            for user_id in fake.random.sample(self.user_ids, n_votes):
                value = Command.fast_vote(kindness_coefficient)
                rating += value
                votes.append(
                    Vote(
                        value=value,
                        object_id=model.id,
                        content_type_id=model_type_id,
                        user_uid=user_id,
                    )
                )
            model.rating += rating

        Vote.objects.bulk_create(votes)
        model_cls.objects.bulk_update(models, ['rating'])

    def handle(self, *args, **options):
        if (tags := options['tags']) > 0:
            print(f'Generate {tags} tags')
            self.create_tags(tags)
        if (publications := options['publications']) > 0:
            max_tags_per_publication = options['max_tags_per_publication']
            max_sentences_per_publication = options['max_sentences_per_publication']
            print(f'Generate {publications} publications with up to {max_sentences_per_publication} sentences and up to {max_tags_per_publication} tags for each publication')
            self.create_publications(publications, max_tags_per_publication, max_sentences_per_publication)
        if (comments := options['comments']) > 0:
            max_sentences_per_comment = options['max_sentences_per_comment']
            print(f'Generate {comments} comments with up to {max_sentences_per_comment} sentences for each comment')
            self.create_comments(comments, max_sentences_per_comment)
        if (max_votes_per_publication := options["max_votes_per_publication"]) > 0:
            print(f'Generate up to {max_votes_per_publication} votes for each publication')
            self.generate_votes_for_model(Publication, max_votes_per_publication)
        if (max_votes_per_comment := options["max_votes_per_comment"]) > 0:
            print(f'Generate up to {max_votes_per_comment} votes for each comment')
            self.generate_votes_for_model(Comment, max_votes_per_comment)
