from django.urls import path
from .views import LoginView, LoginTokenView, RefreshView, LogoutView

urlpatterns = [
    path("login/",        LoginView.as_view(),      name="auth-login"),
    path("login/token/",  LoginTokenView.as_view(), name="auth-login-token"),
    path("refresh/",      RefreshView.as_view(),     name="auth-refresh"),
    path("logout/",       LogoutView.as_view(),      name="auth-logout"),
]
