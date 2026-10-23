from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from catalog.models import Category, Product
from orders.models import Order, OrderItem
from .models import DeliverySettings
from orders.payment_processor import process_order_payment

from orders.payment_service import (
    validate_payment_number,
    process_payment,
)


class OrderAPITests(TestCase):
    """Тестирование создания заказов из корзины."""

    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            title="Электроника",
        )

        self.product = Product.objects.create(
            category=self.category,
            title="Ноутбук",
            price=Decimal("1500.00"),
            count=10,
        )



    def test_confirm_order_saves_comment(self):
        """Комментарий сохраняется при подтверждении заказа через API."""

        # Добавляем товар в корзину.
        response = self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Создаём заказ.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        order_id = response.data["orderId"]

        # Подтверждаем заказ с комментарием.
        response = self.client.post(
            f"/api/order/{order_id}",
            {
                "fullName": "Иван Иванов",
                "email": "ivan@example.com",
                "phone": "+37360000000",
                "deliveryType": "ordinary",
                "paymentType": "online",
                "city": "Кишинёв",
                "address": "Улица Тестовая, 10",
                "comment": "Позвоните перед доставкой.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем сохранение в базе данных.
        order = Order.objects.get(pk=order_id)

        self.assertEqual(order.status, "accepted")
        self.assertEqual(
            order.comment,
            "Позвоните перед доставкой.",
        )

        # Проверяем получение комментария через API.
        response = self.client.get(f"/api/order/{order_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["comment"],
            "Позвоните перед доставкой.",
        )



    def test_create_order_from_basket(self):
        """Заказ создаётся с правильной ценой и количеством."""

        response = self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("orderId", response.data)

        order = Order.objects.get(id=response.data["orderId"])
        item = OrderItem.objects.get(order=order)

        self.assertEqual(item.price, Decimal("1500.00"))
        self.assertEqual(item.count, 2)
        self.assertEqual(item.price, Decimal("1500.00"))


    def test_basket_cleared_after_order_creation(self):
        """После создания заказа корзина пуста, а товары сохранены."""

        # Добавляем два ноутбука в корзину.
        response = self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Создаём заказ.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        order_id = response.data["orderId"]

        # Проверяем, что корзина очистилась.
        response = self.client.get("/api/basket")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        # Проверяем, что товары сохранились в заказе.
        order = Order.objects.get(id=order_id)
        item = OrderItem.objects.get(order=order)

        self.assertEqual(item.product_id, self.product.id)
        self.assertEqual(item.count, 2)
        self.assertEqual(item.price, Decimal("1500.00"))
        self.assertEqual(order.total_cost, Decimal("3000.00"))

        # Повторное оформление пустой корзины запрещено.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 1)


    def test_order_reduces_product_stock(self):
        """Создание заказа уменьшает остаток товара."""

        # На складе изначально 10 ноутбуков.
        self.assertEqual(self.product.count, 10)

        # Добавляем два ноутбука в корзину.
        response = self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Создаём заказ.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Проверяем остаток непосредственно в базе данных.
        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 8)

    def test_order_rejects_insufficient_stock(self):
        """Нельзя заказать больше товара, чем есть на складе."""

        # Добавляем два ноутбука в корзину.
        response = self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # После добавления в корзину на складе остался один.
        self.product.count = 1
        self.product.save(update_fields=["count"])

        # Создание заказа должно быть запрещено.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        # Заказ не создан, остаток не изменился.
        self.assertEqual(Order.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 1)

        # При неудачном оформлении корзина сохраняется.
        response = self.client.get("/api/basket")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)



    def test_cancel_order_restores_stock(self):
        """Отмена заказа возвращает товары на склад."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json"
        )
        self.assertEqual(response.status_code, 200)

        order_id = response.data["orderId"]

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 8)

        response = self.client.post(
            f"/api/order/{order_id}/cancel",
            {}, format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 10)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, "cancelled")

    def test_order_cannot_be_cancelled_twice(self):
        """Повторная отмена не увеличивает остатки дважды."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json"
        )
        order_id = response.data["orderId"]

        cancel_url = f"/api/order/{order_id}/cancel"

        response = self.client.post(
            cancel_url, {}, format="json"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            cancel_url, {}, format="json"
        )
        self.assertEqual(response.status_code, 400)

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 10)

    def test_cannot_cancel_paid_order(self):
        """Оплаченный заказ нельзя отменить обычным запросом."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json"
        )
        order_id = response.data["orderId"]

        order = Order.objects.get(pk=order_id)
        order.status = "paid"
        order.save(update_fields=["status"])

        response = self.client.post(
            f"/api/order/{order_id}/cancel",
            {}, format="json",
        )
        self.assertEqual(response.status_code, 400)

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 8)



    def test_empty_basket_cannot_create_order(self):
        """Нельзя оформить заказ с пустой корзиной."""

        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_price_is_saved(self):
        """Изменение цены товара не меняет сохранённый заказ."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.product.price = Decimal("2000.00")
        self.product.save()

        item = OrderItem.objects.get(
            order_id=response.data["orderId"],
        )

        self.assertEqual(item.price, Decimal("1500.00"))


    def test_guest_can_view_own_order(self):
        """Гость может просматривать свой заказ."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json",
        )
        order_id = response.data["orderId"]

        response = self.client.get(f"/api/orders/{order_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], order_id)
        self.assertEqual(len(response.data["products"]), 1)

    def test_guest_cannot_view_another_order(self):
        """Другая сессия не получает доступ к заказу."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json",
        )
        order_id = response.data["orderId"]

        another_client = APIClient()
        response = another_client.get(f"/api/orders/{order_id}")

        self.assertEqual(response.status_code, 403)

    def test_confirm_order(self):
        """Покупатель может подтвердить свой заказ."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json",
        )
        order_id = response.data["orderId"]

        response = self.client.post(
            f"/api/orders/{order_id}",
            {
                "fullName": "Иван Иванов",
                "email": "ivan@example.com",
                "phone": "069123456",
                "deliveryType": "ordinary",
                "paymentType": "online",
                "city": "Кишинёв",
                "address": "Центральная 10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, "accepted")
        self.assertEqual(order.full_name, "Иван Иванов")

    def test_order_delivery_cost(self):
        """Проверяем расчёт доставки при подтверждении заказа."""

        from decimal import Decimal

        from orders.models import DeliverySettings

        # Устанавливаем стоимость товара: 1500 рублей.
        self.product.price = Decimal("1500.00")
        self.product.save(update_fields=["price"])

        # Настройки доставки по техническому заданию.
        DeliverySettings.objects.create(
            free_delivery_threshold=Decimal("2000.00"),
            ordinary_delivery_price=Decimal("200.00"),
            express_delivery_price=Decimal("500.00"),
        )

        # Добавляем один товар в корзину.
        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        # Создаём заказ.
        response = self.client.post(
            "/api/orders",
            [],
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        order_id = response.data["orderId"]

        # Подтверждаем заказ с обычной доставкой.
        response = self.client.post(
            f"/api/orders/{order_id}",
            {
                "fullName": "Иван Иванов",
                "email": "ivan@example.com",
                "phone": "069123456",
                "deliveryType": "ordinary",
                "paymentType": "online",
                "city": "Кишинёв",
                "address": "Центральная 10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем сохранённую стоимость доставки.
        order = Order.objects.get(pk=order_id)

        self.assertEqual(
            order.delivery_cost,
            Decimal("200.00"),
        )

        # 1500 рублей за товар + 200 рублей за доставку.
        self.assertEqual(
            order.total_cost,
            Decimal("1700.00"),
        )

        # Проверяем, что API возвращает правильные суммы.
        response = self.client.get(f"/api/orders/{order_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deliveryCost"], 200.0)
        self.assertEqual(response.data["totalCost"], 1700.0)

    def test_free_delivery(self):
        """Обычная доставка бесплатна при сумме заказа от 2000 рублей."""
        from decimal import Decimal

        self.product.price = Decimal("2000.00")
        self.product.save(update_fields=["price"])

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post("/api/orders", [], format="json")
        order_id = response.data["orderId"]

        response = self.client.post(
            f"/api/orders/{order_id}",
            {
                "fullName": "Иван Иванов",
                "email": "ivan@example.com",
                "phone": "069123456",
                "deliveryType": "ordinary",
                "paymentType": "online",
                "city": "Кишинёв",
                "address": "Центральная 10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.delivery_cost, Decimal("0.00"))
        self.assertEqual(order.total_cost, Decimal("2000.00"))



    def test_express_delivery_cost(self):
        """Экспресс-доставка добавляет 500 рублей к заказу."""
        from decimal import Decimal

        self.product.price = Decimal("1500.00")
        self.product.save(update_fields=["price"])

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post("/api/orders", [], format="json")
        order_id = response.data["orderId"]

        response = self.client.post(
            f"/api/orders/{order_id}",
            {
                "fullName": "Иван Иванов",
                "email": "ivan@example.com",
                "phone": "069123456",
                "deliveryType": "express",
                "paymentType": "online",
                "city": "Кишинёв",
                "address": "Центральная 10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.delivery_cost, Decimal("500.00"))
        self.assertEqual(order.total_cost, Decimal("2000.00"))



    def test_cannot_cancel_pending_order(self):
        """Заказ с ожидающим платежом нельзя отменить."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json"
        )
        self.assertEqual(response.status_code, 200)

        order = Order.objects.get(pk=response.data["orderId"])
        order.status = "pending"
        order.save(update_fields=["status"])

        response = self.client.post(
            f"/api/order/{order.id}/cancel",
            {}, format="json",
        )
        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()
        self.assertEqual(order.status, "pending")

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 8)

    def test_guest_cannot_cancel_another_guests_order(self):
        """Другая гостевая сессия не может отменить заказ."""

        from rest_framework.test import APIClient

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 2},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json"
        )
        self.assertEqual(response.status_code, 200)

        order_id = response.data["orderId"]

        # Новый клиент не имеет доступа к первой сессии.
        another_client = APIClient()

        response = another_client.post(
            f"/api/order/{order_id}/cancel",
            {}, format="json",
        )
        self.assertEqual(response.status_code, 403)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, "created")

        self.product.refresh_from_db()
        self.assertEqual(self.product.count, 8)



    def test_cannot_confirm_order_twice(self):
        """Нельзя повторно подтвердить заказ."""

        self.client.post(
            "/api/basket",
            {"id": self.product.id, "count": 1},
            format="json",
        )

        response = self.client.post(
            "/api/orders", [], format="json",
        )
        order_id = response.data["orderId"]

        data = {
            "fullName": "Иван Иванов",
            "email": "ivan@example.com",
            "phone": "069123456",
            "deliveryType": "ordinary",
            "paymentType": "online",
            "city": "Кишинёв",
            "address": "Центральная 10",
        }

        first = self.client.post(
            f"/api/orders/{order_id}", data, format="json",
        )
        second = self.client.post(
            f"/api/orders/{order_id}", data, format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)



class PaymentAPITests(APITestCase):
    """Проверка учебной оплаты заказов."""

    def setUp(self):
        self.order = Order.objects.create(
            status="accepted",
            payment_type="online",
            total_cost=15000,
        )

        # Гостевой заказ принадлежит текущей сессии.
        session = self.client.session
        session["guest_order_ids"] = [self.order.id]
        session.save()

        self.url = f"/api/payment/{self.order.id}"

        self.payment_data = {
            "number": "12345678",
            "name": "Test User",
            "month": "12",
            "year": "2030",
            "code": "123",
        }

    def test_successful_payment(self):
        """Платёж сначала попадает в очередь, затем обрабатывается."""

        response = self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 202)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

        result = process_order_payment(self.order.id)

        self.assertTrue(result)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")



    def test_retry_payment_after_failure(self):
        """После ошибки покупатель может повторить оплату."""

        from orders.payment_processor import process_order_payment

        # Первая попытка: номер заканчивается на ноль.
        response = self.client.post(
            self.url,
            {"number": "12345670"},
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertFalse(process_order_payment(self.order.id))

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "failed")
        self.assertTrue(self.order.payment_error)

        # Вторая попытка: используем правильный номер.
        response = self.client.post(
            self.url,
            {"number": "12345678"},
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(process_order_payment(self.order.id))

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.order.payment_error, "")



    def test_repeated_payment(self):
        """Повторная оплата запрещена."""

        self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        response = self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_card_number(self):
        """Некорректный номер карты отклоняется."""

        data = self.payment_data.copy()
        data["number"] = "123"

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "accepted")

    def test_unconfirmed_order(self):
        """Нельзя оплатить неподтверждённый заказ."""

        self.order.status = "created"
        self.order.save()

        response = self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_other_guest_cannot_pay(self):
        """Гость не может оплатить чужой заказ."""

        session = self.client.session
        session["guest_order_ids"] = []
        session.save()

        response = self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_order(self):
        """Несуществующий заказ возвращает 404."""

        response = self.client.post(
            "/api/payment/999999",
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_card_data_not_saved(self):
        """Настоящие банковские реквизиты не сохраняются."""

        response = self.client.post(
            self.url,
            self.payment_data,
            format="json",
        )

        self.assertEqual(response.status_code, 202)

        self.order.refresh_from_db()

        # Сохраняется только фиктивный учебный номер.
        self.assertEqual(self.order.payment_number, "12345678")

        # Банковские реквизиты не сохраняются.
        self.assertFalse(hasattr(self.order, "code"))
        self.assertFalse(hasattr(self.order, "month"))
        self.assertFalse(hasattr(self.order, "year"))



class DeliverySettingsTests(TestCase):
    """Проверка стоимости доставки по ТЗ Skillbox."""

    def setUp(self):
        self.settings = DeliverySettings.objects.create(
            free_delivery_threshold=Decimal("2000.00"),
            ordinary_delivery_price=Decimal("200.00"),
            express_delivery_price=Decimal("500.00"),
        )

    def test_ordinary_delivery_below_threshold(self):
        """При заказе дешевле 2000 рублей доставка стоит 200."""
        cost = self.settings.calculate_delivery(
            Decimal("1999.00"), "ordinary"
        )
        self.assertEqual(cost, Decimal("200.00"))

    def test_ordinary_delivery_at_threshold(self):
        """При заказе от 2000 рублей доставка бесплатная."""
        cost = self.settings.calculate_delivery(
            Decimal("2000.00"), "ordinary"
        )
        self.assertEqual(cost, Decimal("0.00"))

    def test_express_delivery(self):
        """Экспресс-доставка стоит 500 рублей."""
        cost = self.settings.calculate_delivery(
            Decimal("15000.00"), "express"
        )
        self.assertEqual(cost, Decimal("500.00"))

    def test_invalid_delivery_type(self):
        """Неизвестный способ доставки запрещён."""
        with self.assertRaises(ValueError):
            self.settings.calculate_delivery(
                Decimal("1000.00"), "unknown"
            )



class PaymentServiceTests(TestCase):
    """Тесты фиктивной платёжной системы."""

    def test_successful_payment(self):
        """Чётный номер без нуля в конце проходит оплату."""
        success, error = process_payment("12345678")

        self.assertTrue(success)
        self.assertEqual(error, "")

    def test_payment_rejected(self):
        """Номер с нулём в конце отклоняется."""
        success, error = process_payment("12345670")

        self.assertFalse(success)
        self.assertTrue(error)

    def test_odd_number(self):
        """Нечётный номер не проходит проверку."""
        with self.assertRaises(ValueError):
            validate_payment_number("12345677")

    def test_number_too_long(self):
        """Номер длиннее восьми цифр запрещён."""
        with self.assertRaises(ValueError):
            validate_payment_number("1234567890")

    def test_letters_not_allowed(self):
        """Буквы в номере запрещены."""
        with self.assertRaises(ValueError):
            validate_payment_number("1234abcd")



class PaymentProcessorTests(TestCase):
    """Тесты обработки учебных платежей."""

    def test_successful_payment(self):
        """Успешная оплата."""
        order = Order.objects.create(
            status="pending",
            payment_number="12345678",
        )

        result = process_order_payment(order.id)
        order.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(order.status, "paid")
        self.assertEqual(order.payment_error, "")

    def test_failed_payment(self):
        """Отклонённая оплата."""
        order = Order.objects.create(
            status="pending",
            payment_number="12345670",
        )

        result = process_order_payment(order.id)
        order.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(order.status, "failed")
        self.assertTrue(order.payment_error)

    def test_order_not_pending(self):
        """Нельзя обрабатывать неподтверждённый платёж."""
        order = Order.objects.create(
            status="accepted",
            payment_number="12345678",
        )

        result = process_order_payment(order.id)
        order.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(order.status, "accepted")

    def test_missing_order(self):
        """Несуществующий заказ."""
        result = process_order_payment(999999)

        self.assertFalse(result)



class OrderCommentTests(TestCase):
    """Проверка комментариев к заказам."""

    def setUp(self):
        self.order = Order.objects.create(
            status="created",
        )

    def test_order_comment_default_empty(self):
        """У нового заказа комментарий по умолчанию пустой."""
        self.assertEqual(self.order.comment, "")

    def test_order_comment_saved_in_database(self):
        """Комментарий сохраняется в базе данных."""
        self.order.comment = "Позвоните перед доставкой."
        self.order.save()

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.comment,
            "Позвоните перед доставкой.",
        )

    def test_order_comment_in_api_serializer(self):
        """Комментарий присутствует в ответе API."""
        from .serializers import OrderSerializer

        self.order.comment = "Доставить после 18:00."
        self.order.save()

        data = OrderSerializer(self.order).data

        self.assertEqual(
            data["comment"],
            "Доставить после 18:00.",
        )



class OrderSoftDeleteTests(TestCase):
    """Проверка мягкого удаления заказов."""

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            username="soft_delete_test",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=self.user)

        self.order = Order.objects.create(
            user=self.user,
            status="accepted",
        )

    def test_soft_deleted_order_stays_in_database(self):
        """Удалённый заказ физически остаётся в базе."""
        self.order.is_deleted = True
        self.order.save(update_fields=["is_deleted"])

        self.assertTrue(
            Order.objects.filter(
                pk=self.order.pk,
                is_deleted=True,
            ).exists()
        )

    def test_soft_deleted_order_hidden_from_history(self):
        """Удалённый заказ не отображается в истории."""
        self.order.is_deleted = True
        self.order.save(update_fields=["is_deleted"])

        response = self.client.get("/api/orders")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_soft_deleted_order_detail_returns_404(self):
        """Удалённый заказ нельзя просмотреть через API."""
        self.order.is_deleted = True
        self.order.save(update_fields=["is_deleted"])

        response = self.client.get(
            f"/api/order/{self.order.pk}"
        )

        self.assertEqual(response.status_code, 404)

    def test_soft_deleted_order_cannot_be_cancelled(self):
        """Удалённый заказ нельзя отменить через API."""
        self.order.is_deleted = True
        self.order.save(update_fields=["is_deleted"])

        response = self.client.post(
            f"/api/order/{self.order.pk}/cancel",
            format="json",
        )

        self.assertEqual(response.status_code, 404)



class OrderAdminSoftDeleteTests(TestCase):
    """Проверка мягкого удаления через Django Admin."""

    def setUp(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from .admin import OrderAdmin

        self.admin = OrderAdmin(Order, admin.site)
        self.request = RequestFactory().post("/admin/orders/order/")

        self.order = Order.objects.create(
            status="accepted",
        )

    def test_admin_delete_one_order(self):
        """Удаление одного заказа не удаляет запись из базы."""
        self.admin.delete_model(self.request, self.order)

        self.order.refresh_from_db()

        self.assertTrue(self.order.is_deleted)
        self.assertTrue(
            Order.objects.filter(pk=self.order.pk).exists()
        )

    def test_admin_delete_multiple_orders(self):
        """Массовое удаление сохраняет записи в базе."""
        second_order = Order.objects.create(status="created")

        queryset = Order.objects.filter(
            pk__in=[self.order.pk, second_order.pk]
        )

        self.admin.delete_queryset(self.request, queryset)

        self.assertEqual(
            Order.objects.filter(
                pk__in=[self.order.pk, second_order.pk],
                is_deleted=True,
            ).count(),
            2,
        )
