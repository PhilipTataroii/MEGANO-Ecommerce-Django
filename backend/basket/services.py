
from django.db import transaction

from catalog.models import Product

from .cart import Cart
from .models import BasketItem


@transaction.atomic
def merge_guest_basket(request, user):
    """Переносит товары из гостевой корзины в корзину пользователя."""

    guest_items = request.session.get(Cart.SESSION_KEY, {})

    if not isinstance(guest_items, dict) or not guest_items:
        return

    for product_id, quantity in guest_items.items():
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            continue

        if type(quantity) is not int or quantity <= 0:
            continue

        product = Product.objects.filter(
            id=product_id,
            is_active=True,
            is_deleted=False,
            category__is_active=True,
            category__is_deleted=False,
        ).first()

        if product is None:
            continue

        basket_item, _ = BasketItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={"count": 0},
        )

        basket_item.count = min(
            basket_item.count + quantity,
            product.count,
        )

        if basket_item.count > 0:
            basket_item.save(update_fields=["count"])
        else:
            basket_item.delete()

    request.session.pop(Cart.SESSION_KEY, None)
    request.session.modified = True
