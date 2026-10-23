
import json
from http import HTTPStatus

from .models import Profile
from .serializers import ProfileSerializer
from basket.services import merge_guest_basket

from django.contrib.auth import (
    update_session_auth_hash,
    authenticate,
    login,
    logout,
)

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError


@extend_schema(
    methods=["POST"],
    summary="Авторизация пользователя",
    request=inline_serializer(
        name="SignInRequest",
        fields={
            "username": serializers.CharField(),
            "password": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="SignInResponse",
            fields={
                "detail": serializers.CharField(),
            },
        ),
    },
)
class SignIn(APIView):
    """Авторизация пользователя через логин и пароль."""

    permission_classes = [AllowAny]

    def post(self, request):
        # Фронтенд может отправлять JSON без Content-Type: application/json.
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                {"detail": "Некорректный формат JSON"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if not isinstance(data, dict):
            return Response(
                {"detail": "Ожидается JSON-объект"},
                status=HTTPStatus.BAD_REQUEST,
            )

        username = data.get("username")
        password = data.get("password")

        # Проверяем обязательные поля.
        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"detail": "Укажите логин и пароль"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if not username.strip() or not password:
            return Response(
                {"detail": "Логин и пароль не могут быть пустыми"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Проверяем учётные данные пользователя.
        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Неверный логин или пароль"},
                status=HTTPStatus.UNAUTHORIZED,
            )

        # Сохраняем гостевую корзину до изменения сессии.
        guest_basket = request.session.get("basket", {}).copy()

        # Авторизуем пользователя.
        login(request, user)

        # Восстанавливаем гостевую корзину для объединения.
        if guest_basket:
            request.session["basket"] = guest_basket

        # Объединяем товары с корзиной пользователя.
        merge_guest_basket(request, user)

        return Response(
            {"detail": "Авторизация прошла успешно"},
            status=HTTPStatus.OK,
        )


@extend_schema(
    methods=["POST"],
    summary="Регистрация нового пользователя",
    request=inline_serializer(
        name="SignUpRequest",
        fields={
            "name": serializers.CharField(),
            "username": serializers.CharField(),
            "password": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="SignUpResponse",
            fields={
                "detail": serializers.CharField(),
            },
        ),
    },
)
class SignUp(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [AllowAny]

    def post(self, request):
        # Получаем данные регистрации.
        # Поддерживаем JSON и обычные данные формы.
        try:
            if request.content_type == "application/json":
                data = request.data
            else:
                data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = request.data

        if not isinstance(data, dict):
            return Response(
                {"detail": "Некорректные данные регистрации"},
                status=HTTPStatus.BAD_REQUEST,
            )

        name = data.get("name")
        username = data.get("username")
        password = data.get("password")

        # Проверяем обязательные поля.
        if not all(
            isinstance(value, str) and value.strip()
            for value in (name, username, password)
        ):
            return Response(
                {"detail": "Заполните все обязательные поля"},
                status=HTTPStatus.BAD_REQUEST,
            )

        username = username.strip()
        name = name.strip()

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Пользователь с таким логином уже существует"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Проверяем пароль стандартными валидаторами Django.
        try:
            validate_password(password)
        except ValidationError as error:
            return Response(
                {"detail": error.messages},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Создаём пользователя с безопасным хешированием пароля.
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=name,
            )
        except (IntegrityError, ValidationError):
            return Response(
                {"detail": "Не удалось зарегистрировать пользователя"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Авторизуем пользователя после регистрации.
        login(request, user)

        # Переносим гостевую корзину новому пользователю.
        merge_guest_basket(request, user)

        return Response(
            {"detail": "Регистрация прошла успешно"},
            status=HTTPStatus.OK,
        )


@extend_schema(
    methods=["POST"],
    summary="Выход пользователя из аккаунта",
    request=None,
    responses={
        200: inline_serializer(
            name="SignOutResponse",
            fields={
                "detail": serializers.CharField(),
            },
        ),
    },
)
class SignOut(APIView):
    """Выход пользователя из аккаунта."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Завершаем пользовательскую сессию.
        logout(request)

        return Response(
            {"detail": "Вы успешно вышли из аккаунта"},
            status=HTTPStatus.OK,
        )


@extend_schema(
    methods=["GET"],
    summary="Получить профиль пользователя",
    responses=ProfileSerializer,
)
@extend_schema(
    methods=["POST"],
    summary="Обновить профиль пользователя",
    request=inline_serializer(
        name="ProfileUpdateRequest",
        fields={
            "fullName": serializers.CharField(),
            "email": serializers.EmailField(allow_blank=True),
            "phone": serializers.CharField(allow_blank=True),
        },
    ),
    responses=ProfileSerializer,
)
class UserProfile(APIView):
    """Получение профиля пользователя."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Создаём профиль автоматически, если его ещё нет.
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        serializer = ProfileSerializer(profile)

        return Response(
            serializer.data,
            status=HTTPStatus.OK,
        )


    def post(self, request):
        """Обновление данных профиля."""

        # Получаем профиль текущего пользователя.
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        full_name = request.data.get("fullName")
        email = request.data.get("email")
        phone = request.data.get("phone")

        # Проверяем типы перед сохранением.
        if not all(
            isinstance(value, str)
            for value in (full_name, email, phone)
        ):
            return Response(
                {"detail": "Некорректные данные профиля"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Проверяем формат электронной почты.
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError

        if email:
            try:
                validate_email(email)
            except ValidationError:
                return Response(
                    {"detail": "Некорректный email"},
                    status=HTTPStatus.BAD_REQUEST,
                )

        # Сохраняем изменения пользователя.
        user = request.user
        user.first_name = full_name.strip()
        user.email = email.strip()
        user.save(update_fields=["first_name", "email"])

        # Сохраняем номер телефона.
        profile.phone = phone.strip()
        profile.save(update_fields=["phone"])

        serializer = ProfileSerializer(profile)

        return Response(
            serializer.data,
            status=HTTPStatus.OK,
        )



@extend_schema(
    methods=["POST"],
    summary="Изменить пароль пользователя",
    request=inline_serializer(
        name="ChangePasswordRequest",
        fields={
            "currentPassword": serializers.CharField(),
            "newPassword": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="ChangePasswordResponse",
            fields={
                "detail": serializers.CharField(),
            },
        ),
    },
)
class ChangePassword(APIView):
    """Изменение пароля пользователя."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("currentPassword")
        new_password = request.data.get("newPassword")

        # Проверяем наличие паролей.
        if not isinstance(current_password, str) or not isinstance(new_password, str):
            return Response(
                {"detail": "Укажите текущий и новый пароль"},
                status=HTTPStatus.BAD_REQUEST,
            )

        user = request.user

        # Проверяем правильность текущего пароля.
        if not user.check_password(current_password):
            return Response(
                {"detail": "Неверный текущий пароль"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Проверяем новый пароль по правилам Django.
        try:
            validate_password(new_password, user=user)
        except ValidationError as error:
            return Response(
                {"detail": error.messages},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Сохраняем новый пароль.
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Сохраняем авторизацию пользователя.
        update_session_auth_hash(request, user)

        return Response(
            {"detail": "Пароль успешно изменён"},
            status=HTTPStatus.OK,
        )


@extend_schema(
    methods=["POST"],
    summary="Загрузить аватар пользователя",
    request={
        "multipart/form-data": inline_serializer(
            name="ChangeAvatarRequest",
            fields={
                "avatar": serializers.ImageField(),
            },
        ),
    },
    responses={200: ProfileSerializer},
)
class ChangeAvatar(APIView):
    """Загрузка аватара пользователя."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        avatar = request.FILES.get("avatar")

        if avatar is None:
            return Response(
                {"detail": "Выберите изображение"},
                status=HTTPStatus.BAD_REQUEST,
            )

        # Проверяем изображение и ограничиваем размер до 5 МБ.
        from django.core.files.uploadedfile import UploadedFile
        from django.core.files.images import get_image_dimensions

        if not isinstance(avatar, UploadedFile) or avatar.size > 5 * 1024 * 1024:
            return Response(
                {"detail": "Размер изображения не должен превышать 5 МБ"},
                status=HTTPStatus.BAD_REQUEST,
            )

        try:
            width, height = get_image_dimensions(avatar)
            if not width or not height:
                raise ValueError("Invalid image")
            avatar.seek(0)
        except (ValueError, OSError):
            return Response(
                {"detail": "Загрузите корректное изображение"},
                status=HTTPStatus.BAD_REQUEST,
            )

        profile, _ = Profile.objects.get_or_create(user=request.user)

        # Сохраняем новый аватар.
        # Старый файл автоматически удалит django-cleanup.
        profile.avatar = avatar
        profile.save(update_fields=["avatar"])

        return Response(
            ProfileSerializer(profile).data,
            status=HTTPStatus.OK,
        )

