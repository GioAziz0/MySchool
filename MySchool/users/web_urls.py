from django.urls import path
from .web_views import LoginView, SelectSchoolView, SelectRoleView, LogoutView

urlpatterns = [
    path("login/",         LoginView.as_view(),       name="login"),
    path("logout/",        LogoutView.as_view(),       name="logout"),
    path("select-school/", SelectSchoolView.as_view(), name="select-school"),
    path("select-role/",   SelectRoleView.as_view(),   name="select-role"),
]
