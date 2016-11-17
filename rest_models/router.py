# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from rest_models.backend.base import DatabaseWrapper

logger = logging.getLogger(__name__)


class RestModelRouter(object):

    def __init__(self):
        self._api_database_name = None
        self.cache = {}

    @staticmethod
    def is_restmodel_database(db_settings):
        db_module = import_module(db_settings['ENGINE'] + '.base')
        return issubclass(db_module.DatabaseWrapper, DatabaseWrapper)

    @property
    def api_database_name(self):
        if self._api_database_name is None:
            for db_name, db_settings in settings.DATABASES.items():

                if self.is_restmodel_database(db_settings):
                    if self._api_database_name is None:
                        self._api_database_name = db_name
                    else:
                        raise ImproperlyConfigured("too many Api Database found (%s and %s). you must specify "
                                                   "the database to use in each model.APIMeta.db_name")
            if self._api_database_name is None:
                raise ImproperlyConfigured("no Api Database found in settings.DATABASE. you can't use a model with "
                                           "APIMeta in INSTALLED_APPS application")
        return self._api_database_name

    @staticmethod
    def is_api_model(model):
        return hasattr(model, 'APIMeta')

    def get_api_database(self, model):
        try:
            return self.cache[model]
        except KeyError:
            if self.is_api_model(model):
                if hasattr(model.APIMeta, 'db_name'):
                    result = model.APIMeta.db_name
                else:
                    result = self.api_database_name
            else:
                result = None
            self.cache[model] = result
            return result

    def db_for_read(self, model, **hints):
        return self.get_api_database(model)

    def db_for_write(self, model, **hints):
        return self.get_api_database(model)

    def allow_relation(self, obj1, obj2, **hints):
        if self.is_api_model(obj1) or self.is_api_model(obj2):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if self.is_restmodel_database(settings.DATABASES[db]):
            return False  # no migration for our database

        if model_name is None:
            return None  # we are model specific
        # all our models must not being created in other databases
        model = apps.get_model(app_label, model_name)
        if self.is_api_model(model):
            return False
        return None
