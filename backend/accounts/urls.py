from django.urls import path

from .views import (
    SignIn,
    SignOut,
    SignUp,
    UserProfile,
    ChangePassword,
    ChangeAvatar,
)

urlpatterns = [
    path("sign-in", SignIn.as_view(), name="sign-in"),
    path("sign-up", SignUp.as_view(), name="sign-up"),
    path("sign-out", SignOut.as_view(), name="sign-out"),
    path("profile", UserProfile.as_view(), name="profile"),
    path("profile/password", ChangePassword.as_view(), name="profile-password"),
    path("profile/avatar", ChangeAvatar.as_view(), name="profile-avatar"),
]