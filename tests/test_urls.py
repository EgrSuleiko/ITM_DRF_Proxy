from django.urls import resolve

from proxy_app.views import proxy_request


def test_proxy_catch_all():
    match = resolve('/any/path/here/')
    assert match.url_name == 'proxy'
    assert match.func == proxy_request
