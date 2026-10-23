
from catalog.models import Product

from .models import BasketItem


class Cart:
    """Корзина: сессия для гостей, база данных для пользователей."""

    SESSION_KEY = "basket"

    def __init__(self, request):
        self.session = request.session
        self.user = request.user
        self.is_authenticated = self.user.is_authenticated

        if self.is_authenticated:
            self.items = {
                str(item.product_id): item.count
                for item in BasketItem.objects.filter(user=self.user)
            }
        else:
            self.items = self.session.get(self.SESSION_KEY, {}).copy()

    def save(self):
        """Сохраняет корзину в сессию или базу данных."""

        if self.is_authenticated:
            for product_id, count in self.items.items():
                BasketItem.objects.update_or_create(
                    user=self.user,
                    product_id=int(product_id),
                    defaults={"count": count},
                )

            BasketItem.objects.filter(
                user=self.user,
            ).exclude(
                product_id__in=[int(key) for key in self.items],
            ).delete()

        else:
            self.session[self.SESSION_KEY] = self.items
            self.session.modified = True

    def add(self, product_id, count):
        """Добавляет товар или увеличивает количество."""

        key = str(product_id)
        current_count = self.items.get(key, 0)

        self.items[key] = current_count + count
        self.save()

    def remove(self, product_id, count):
        """Уменьшает количество товара или удаляет его."""

        key = str(product_id)

        if key not in self.items:
            return

        remaining = self.items[key] - count

        if remaining > 0:
            self.items[key] = remaining
        else:
            del self.items[key]

        self.save()

    def get_items(self):
        """Возвращает товары и их количество."""

        product_ids = [int(key) for key in self.items]

        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_deleted=False,
            category__is_active=True,
            category__is_deleted=False,
        ).prefetch_related("images", "tags")

        result = []

        for product in products:
            quantity = self.items[str(product.id)]

            result.append({
                "product": product,
                "count": quantity,
                "price": product.price,
            })

        return result


    def clear(self):
        """Полностью очищает корзину пользователя или гостя."""
        self.items.clear()
        self.save()
