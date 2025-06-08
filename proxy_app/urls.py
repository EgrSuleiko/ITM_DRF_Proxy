from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from django_prometheus import exports

from proxy_app.views import proxy_request

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('metrics/', exports.ExportToDjangoView),
    re_path(r'^.*$', proxy_request, name='proxy'),
]
