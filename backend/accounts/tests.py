import io

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Profile


class AccountsTests(TestCase):
    """Автоматические тесты приложения accounts."""

    def setUp(self):
        # Создаём тестового пользователя.
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            username="filip_test",
            password=self.password,
            first_name="Filip",
            email="filip@example.com",
        )

        self.client = APIClient()

    def test_sign_up(self):
        """Регистрация нового пользователя."""
        response = self.client.post(
            "/api/sign-up",
            {
                "name": "Alex",
                "username": "alex_test",
                "password": "SecurePassword2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(username="alex_test").exists()
        )

    def test_duplicate_username(self):
        """Нельзя зарегистрировать одинаковый логин дважды."""
        response = self.client.post(
            "/api/sign-up",
            {
                "name": "Another Filip",
                "username": "filip_test",
                "password": "SecurePassword2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_sign_in(self):
        """Авторизация с правильным паролем."""
        response = self.client.post(
            "/api/sign-in",
            {
                "username": "filip_test",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_sign_in_wrong_password(self):
        """Неверный пароль не позволяет войти."""
        response = self.client.post(
            "/api/sign-in",
            {
                "username": "filip_test",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_sign_out(self):
        """Выход из аккаунта."""
        self.client.force_login(self.user)

        response = self.client.post("/api/sign-out")

        self.assertEqual(response.status_code, 200)

        # После выхода профиль недоступен.
        profile_response = self.client.get("/api/profile")
        self.assertIn(profile_response.status_code, (401, 403))

    def test_profile_requires_authentication(self):
        """Гость не может просматривать профиль."""
        response = self.client.get("/api/profile")

        self.assertIn(response.status_code, (401, 403))

    def test_get_profile(self):
        """Получение профиля авторизованного пользователя."""
        self.client.force_login(self.user)

        response = self.client.get("/api/profile")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["fullName"], "Filip")
        self.assertEqual(response.data["email"], "filip@example.com")

    def test_update_profile(self):
        """Редактирование личных данных."""
        self.client.force_login(self.user)

        response = self.client.post(
            "/api/profile",
            {
                "fullName": "Filip Tataroi",
                "email": "new@example.com",
                "phone": "+37369123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)

        self.assertEqual(self.user.first_name, "Filip Tataroi")
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(profile.phone, "+37369123456")

    def test_change_password(self):
        """Смена пароля с правильным текущим паролем."""
        self.client.force_login(self.user)

        response = self.client.post(
            "/api/profile/password",
            {
                "currentPassword": self.password,
                "newPassword": "NewStrongPassword2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("NewStrongPassword2026!")
        )

        # Авторизация должна сохраниться.
        profile_response = self.client.get("/api/profile")
        self.assertEqual(profile_response.status_code, 200)

    def test_change_password_wrong_current(self):
        """Нельзя сменить пароль, не зная старого."""
        self.client.force_login(self.user)

        response = self.client.post(
            "/api/profile/password",
            {
                "currentPassword": "IncorrectPassword!",
                "newPassword": "NewStrongPassword2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_avatar_requires_file(self):
        """Нельзя загрузить аватар без файла."""
        self.client.force_login(self.user)

        response = self.client.post("/api/profile/avatar", {})

        self.assertEqual(response.status_code, 400)


    def test_upload_avatar(self):
        """Проверяем успешную загрузку аватара."""
        self.client.force_login(self.user)

        # Создаём небольшое тестовое изображение.
        image = Image.new("RGB", (50, 50))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        avatar = SimpleUploadedFile(
            "avatar.png",
            image_bytes.read(),
            content_type="image/png",
        )

        response = self.client.post(
            "/api/profile/avatar",
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar)
        self.assertIn("avatars/", profile.avatar.name)

