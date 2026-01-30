from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import api_views

from rest_framework.routers import DefaultRouter

#router = DefaultRouter()
#router.register(r'permissions/manage', api_views.PermessoViewSet, basename='permissions-manage')

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Permissions
    path('permissions/me/', api_views.MyPermissionsView.as_view(), name='my_permissions'),
#    path('', include(router.urls)),
    path('permissions/user/<str:username>/', api_views.UserPermissionsView.as_view(), name='user-permissions'),
    path('permissions/user/<str:username>/<str:perm_name>/', api_views.ManagePermissionsView.as_view(), name='permissions-manage'),
]
