# -*- coding: utf-8 -*-
import logging
import os
from uuid import uuid4

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from testapi import models as apimodels
from testapp import models as clientmodels

logger = logging.getLogger(__name__)

image_test = open(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'okami.jpg'), 'rb').read()


class TestUploadDRF(TestCase):
    fixtures = ['user.json']
    port = 8081

    def setUp(self):
        self.img_name = str(uuid4()) + '.png'
        self.img_name2 = str(uuid4()) + '.png'
        self.unlinkimg(self.img_name)
        self.unlinkimg(self.img_name2)

    def tearDown(self):
        self.unlinkimg(self.img_name)
        self.unlinkimg(self.img_name2)

    def unlinkimg(self, img_name):
        path = os.path.join(settings.MEDIA_ROOT, img_name)
        if os.path.exists(path):
            os.unlink(path)

    def test_image_size(self):
        assert len(image_test) == 284975

    def test_null_value(self):
        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=None,
        )
        self.assertEqual(review_api.comment, 'coucou')
        self.assertFalse(review_api.photo)
        self.assertFalse(review_api.photo.name)
        review_api.refresh_from_db()
        self.assertEqual(review_api.comment, 'coucou')
        self.assertFalse(review_api.photo)
        self.assertFalse(review_api.photo.name)

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)
        self.assertEqual(review_client.comment, 'coucou')
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)

    def test_null_value_client(self):
        review_client = clientmodels.Review.objects.create(
            comment="coucou",
            photo=None,
        )
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)
        review_client.refresh_from_db()
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)

        review_api = apimodels.Review.objects.get(pk=review_client.pk)
        self.assertFalse(review_api.photo)
        self.assertFalse(review_api.photo.name)

    def test_url_files(self):

        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, image_test, 'image/png'),
        )
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, '/media/%s' % self.img_name)
        review_api.refresh_from_db()
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, '/media/%s' % self.img_name)

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)

        self.assertEqual(review_client.photo.name, self.img_name)

    def test_upload_files(self):

        review_client = clientmodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, image_test, 'image/png'),
        )

        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.name, self.img_name)
        self.assertEqual(review_client.comment, 'coucou')
        review_client.refresh_from_db()
        self.assertEqual(review_client.comment, 'coucou')
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.name, self.img_name)

        review_api = clientmodels.Review.objects.get(pk=review_client.pk)
        self.assertEqual(review_api.comment, 'coucou')
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, 'http://testserver/media/%s' % self.img_name)

    def test_open_from_api(self):
        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, image_test, 'image/png'),
        )
        self.assertEqual(review_api.photo.file.read(), image_test)
        review_api.refresh_from_db()
        self.assertEqual(review_api.photo.file.read(), image_test)

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.file.read(), image_test)

    def test_open_from_client(self):
        review_client = clientmodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, image_test, 'image/png'),
        )
        self.assertEqual(review_client.photo.file.read(), image_test)
        review_client.refresh_from_db()
        self.assertEqual(review_client.photo.file.read(), image_test)

        review_api = apimodels.Review.objects.get(pk=review_client.pk)
        image_from_review = review_api.photo.file.read()
        self.assertEqual(len(image_from_review), 284975)
        self.assertEqual(image_from_review, image_test)

    def test_null_value_update_from_client(self):
        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=None,
        )
        self.assertFalse(review_api.photo)
        self.assertFalse(review_api.photo.name)
        self.assertEqual(review_api.comment, 'coucou')

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)

        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)
        self.assertEqual(review_client.comment, 'coucou')
        review_client.comment = 'comment'
        review_client.save()
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)
        self.assertEqual(review_client.comment, 'comment')

        review_client.photo = SimpleUploadedFile(self.img_name, image_test, 'image/png')
        review_client.save()
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        review_client.refresh_from_db()
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.file.read(), image_test)

        review_client.photo = None
        review_client.save()
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)
        self.assertEqual(review_client.comment, 'comment')

        review_client.refresh_from_db()
        self.assertFalse(review_client.photo)
        self.assertFalse(review_client.photo.name)
        review_api.refresh_from_db()
        self.assertFalse(review_api.photo)
        self.assertFalse(review_api.photo.name)
        self.assertEqual(review_api.comment, 'comment')

        review_client.photo = SimpleUploadedFile(self.img_name2, image_test, 'image/png')
        review_client.save()
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name2)
        review_client.refresh_from_db()
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name2)
        self.assertEqual(review_client.photo.file.read(), image_test)
        self.assertEqual(review_client.comment, 'comment')
