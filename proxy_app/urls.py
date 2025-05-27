from django.urls import path, re_path
from proxy_app.views import proxy_request

urlpatterns = [
    # path('', ProxyView.as_view(), name='proxy'),
    # re_path(r'^.*$', ProxyView.as_view(), name='proxy'),
    re_path(r'^.*$', proxy_request, name='proxy'),
]
