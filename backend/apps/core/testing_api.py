"""Helpers for API tests: a JSON client and ready-made accounts."""

import json

from django.test import Client

from .testing import make_user

PASSWORD = "una-clave-segura-123"


class ApiClient(Client):
    def _json(self, method, path, data=None, **extra):
        body = json.dumps(data) if data is not None else None
        return getattr(super(), method)(path, body, content_type="application/json", **extra)

    def get_json(self, path, **params):
        return self.get(path, params)

    def post_json(self, path, data=None):
        return self._json("post", path, data if data is not None else {})

    def patch_json(self, path, data):
        return self._json("patch", path, data)

    def put_json(self, path, data):
        return self._json("put", path, data)


def signed_in(role="worker", **person):
    user = make_user(role=role, password=PASSWORD, **person)
    client = ApiClient()
    assert client.login(username=user.person.email, password=PASSWORD)
    return client, user
