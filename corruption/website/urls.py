from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.user_login, name="login"),
    path("register/", views.user_signup, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path(
        "submit-text-complaint/",
        views.submit_text_complaint,
        name="submit_text_complaint",
    ),
    path(
        "submit_audio_complaint/",
        views.submit_audio_complaint,
        name="submit_audio_complaint",
    ),
    path("chatbot/api/", views.chatbot_api, name="chatbot_api"),
    path("about/", views.about, name="about")
]
