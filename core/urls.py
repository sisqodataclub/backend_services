from django.urls import path
from . import views

urlpatterns = [
    path("register/",        views.register,        name="register"),
    path("login/",           views.login,            name="login"),
    path("token/refresh/",   views.refresh_token,   name="token-refresh"),
    path("me/",              views.me,               name="me"),
    path("change-password/", views.change_password, name="change-password"),
]
