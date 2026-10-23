
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from catalog.models import Category, Product
from django.contrib.auth.models import User
from basket.models import BasketItem
from basket.cart import Cart


class BasketAPITests(TestCase):
    """Проверка работы корзины интернет-магазина."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("basket")

        self.category = Category.objects.create(
            title="Электроника",
        )

        self.product = Product.objects.create(
            category=self.category,
            title="Видеокарта",
            price=Decimal("500.00"),
            count=10,
        )

    def test_empty_basket(self):
        """Новая корзина должна быть пустой."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_clear_guest_basket(self):
        """Метод Cart.clear() очищает гостевую корзину."""

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.assertEqual(
            len(self.client.get(self.url).data), 1
        )

        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        request.session = self.client.session

        cart = Cart(request)
        cart.clear()

        # Сохраняем изменения сессии для следующего запроса.
        request.session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])



    def test_add_product(self):
        """Добавление товара в корзину."""
        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.product.id)
        self.assertEqual(response.data[0]["count"], 2)
        self.assertEqual(response.data[0]["price"], 500.0)

    def test_add_product_twice(self):
        """Повторное добавление увеличивает количество."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": 3},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["count"], 5)
        self.assertEqual(response.data[0]["price"], 500.0)

    def test_remove_part_of_product(self):
        """Удаление части количества товара."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 5},
            format="json",
        )

        response = self.client.delete(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["count"], 3)

    def test_remove_product_completely(self):
        """Полное удаление товара из корзины."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.delete(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_not_enough_stock(self):
        """Нельзя добавить больше товара, чем есть на складе."""
        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": 11},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_quantity(self):
        """Количество должно быть положительным целым числом."""
        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": -1},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_unknown_product(self):
        """Несуществующий товар нельзя добавить."""
        response = self.client.post(
            self.url,
            {"id": 999999, "count": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_basket_persists_in_session(self):
        """Корзина сохраняется между запросами."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["count"], 2)

    def test_basket_without_login(self):
        """Гость может пользоваться корзиной."""
        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 200)



class AuthenticatedBasketTests(TestCase):
    """Проверка корзины авторизованного пользователя."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("basket")

        self.user = User.objects.create_user(
            username="basket_user",
            password="StrongPassword123!",
        )

        self.category = Category.objects.create(
            title="Электроника",
        )

        self.product = Product.objects.create(
            category=self.category,
            title="Видеокарта",
            price=Decimal("500.00"),
            count=10,
        )

    def test_authenticated_basket_saved_to_database(self):
        """Товары авторизованного пользователя сохраняются в БД."""
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"id": self.product.id, "count": 3},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        item = BasketItem.objects.get(
            user=self.user,
            product=self.product,
        )
        self.assertEqual(item.count, 3)

    def test_basket_persists_after_logout(self):
        """Корзина сохраняется после выхода и повторного входа."""
        self.client.force_login(self.user)

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.client.logout()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["count"], 2)

    def test_authenticated_basket_remove_product(self):
        """Удаление товара обновляет корзину в БД."""
        self.client.force_login(self.user)

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 5},
            format="json",
        )

        self.client.delete(
            self.url,
            {"id": self.product.id, "count": 3},
            format="json",
        )

        item = BasketItem.objects.get(
            user=self.user,
            product=self.product,
        )
        self.assertEqual(item.count, 2)

    def test_guest_basket_merges_on_login(self):
        """При входе гостевая корзина объединяется с корзиной пользователя."""
        BasketItem.objects.create(
            user=self.user,
            product=self.product,
            count=3,
        )

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            reverse("sign-in"),
            {
                "username": "basket_user",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        item = BasketItem.objects.get(
            user=self.user,
            product=self.product,
        )
        self.assertEqual(item.count, 5)

    def test_guest_basket_cleared_after_login(self):
        """После объединения гостевая корзина очищается."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            reverse("sign-in"),
            {
                "username": "basket_user",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("basket", self.client.session)

    def test_merge_respects_stock_limit(self):
        """Объединение не превышает остаток на складе."""
        BasketItem.objects.create(
            user=self.user,
            product=self.product,
            count=8,
        )

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 5},
            format="json",
        )

        response = self.client.post(
            reverse("sign-in"),
            {
                "username": "basket_user",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        item = BasketItem.objects.get(
            user=self.user,
            product=self.product,
        )
        self.assertEqual(item.count, 10)




    def test_guest_basket_merges_on_signup(self):
        """После регистрации гостевая корзина переносится в БД."""
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 3},
            format="json",
        )

        response = self.client.post(
            reverse("sign-up"),
            {
                "name": "Новый пользователь",
                "username": "new_basket_user",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="new_basket_user")
        item = BasketItem.objects.get(
            user=new_user,
            product=self.product,
        )

        self.assertEqual(item.count, 3)
        self.assertNotIn("basket", self.client.session)

    def test_different_users_have_separate_baskets(self):
        """Корзины разных пользователей не смешиваются."""
        second_user = User.objects.create_user(
            username="second_basket_user",
            password="StrongPassword123!",
        )

        self.client.force_login(self.user)
        self.client.post(
            self.url,
            {"id": self.product.id, "count": 2},
            format="json",
        )

        self.client.logout()
        self.client.force_login(second_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        self.client.post(
            self.url,
            {"id": self.product.id, "count": 4},
            format="json",
        )

        self.assertEqual(
            BasketItem.objects.get(
                user=self.user,
                product=self.product,
            ).count,
            2,
        )

        self.assertEqual(
            BasketItem.objects.get(
                user=second_user,
                product=self.product,
            ).count,
            4,
        )



    def test_clear_authenticated_basket(self):
        """Cart.clear() удаляет товары пользователя из базы данных."""

        BasketItem.objects.create(
            user=self.user,
            product=self.product,
            count=2,
        )

        self.assertEqual(
            BasketItem.objects.filter(user=self.user).count(),
            1,
        )

        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.user
        request.session = self.client.session

        cart = Cart(request)
        cart.clear()

        self.assertFalse(
            BasketItem.objects.filter(user=self.user).exists()
        )

