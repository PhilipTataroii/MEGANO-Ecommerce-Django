
from django.conf import settings
from django.db import models


class BasketItem(models.Model):
    """Товар в корзине авторизованного пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Пользователь",
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Товар",
    )

    count = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзинах"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_basket_product",
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.product.title} × {self.count}"
