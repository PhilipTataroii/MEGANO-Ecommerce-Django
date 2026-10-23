from django.conf import settings
from django.db import models


class Order(models.Model):
    """Заказ покупателя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Покупатель",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ФИО",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    delivery_type = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Способ доставки",
    )
    payment_type = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Способ оплаты",
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Общая стоимость",
    )

    delivery_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Стоимость доставки",
    )

    status = models.CharField(
        max_length=30,
        default="created",
        verbose_name="Статус заказа",
    )

    payment_error = models.TextField(
        blank=True,
        verbose_name="Ошибка оплаты",
    )

    payment_number = models.CharField(
        max_length=8,
        blank=True,
        verbose_name="Номер учебного платёжного счёта",
    )

    city = models.CharField(max_length=150, blank=True)
    address = models.CharField(max_length=255, blank=True)

    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий к заказу",
    )

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Удалён",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ №{self.pk}"


class OrderItem(models.Model):
    """Товар в заказе с сохранённой ценой на момент покупки."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    count = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Стоимость позиции",
    )

    class Meta:
        verbose_name = "Товар заказа"
        verbose_name_plural = "Товары заказа"

    def __str__(self):
        return f"{self.product.title} — {self.count} шт."


class DeliverySettings(models.Model):
    """Настройки стоимости доставки интернет-магазина."""

    free_delivery_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=2000,
        verbose_name="Порог бесплатной доставки",
    )

    ordinary_delivery_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=200,
        verbose_name="Стоимость обычной доставки",
    )

    express_delivery_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=500,
        verbose_name="Стоимость экспресс-доставки",
    )

    class Meta:
        verbose_name = "Настройки доставки"
        verbose_name_plural = "Настройки доставки"

    def __str__(self):
        return "Настройки доставки"

    def calculate_delivery(self, order_total, delivery_type):
        """Рассчитывает стоимость доставки по требованиям ТЗ."""

        if delivery_type == "express":
            return self.express_delivery_price

        if delivery_type == "ordinary":
            if order_total < self.free_delivery_threshold:
                return self.ordinary_delivery_price
            return 0

        raise ValueError("Неизвестный способ доставки")