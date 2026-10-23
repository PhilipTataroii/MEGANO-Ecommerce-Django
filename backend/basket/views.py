
from django.db.models import Avg, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from catalog.models import Product
from catalog.serializers import ProductShortSerializer

from .cart import Cart


def serialize_basket(request, cart):
    """Возвращает корзину в формате Swagger."""

    items = cart.get_items()
    result = []

    for item in items:
        product = item["product"]

        # Используем готовый сериализатор каталога.
        data = ProductShortSerializer(
            product,
            context={"request": request},
        ).data

        # В корзине count — выбранное количество,
        # price — общая стоимость позиции.
        data["count"] = item["count"]
        data["price"] = float(item["price"])

        result.append(data)

    return result


@extend_schema(
    methods=["GET"],
    summary="Получить корзину",
    responses=ProductShortSerializer(many=True),
)
@extend_schema(
    methods=["POST", "DELETE"],
    summary="Изменить количество товара в корзине",
    request=inline_serializer(
        name="BasketChangeRequest",
        fields={
            "id": serializers.IntegerField(min_value=1),
            "count": serializers.IntegerField(min_value=1),
        },
    ),
    responses=ProductShortSerializer(many=True),
)
@api_view(["GET", "POST", "DELETE"])
def basket_view(request):
    """Просмотр, добавление и удаление товаров из корзины."""

    cart = Cart(request)

    # Получение корзины.
    if request.method == "GET":
        return Response(serialize_basket(request, cart))

    # Проверяем ID товара и количество.
    product_id = request.data.get("id")
    count = request.data.get("count")

    if (
        type(product_id) is not int
        or type(count) is not int
        or product_id <= 0
        or count <= 0
    ):
        return Response(
            {"detail": "ID товара и количество должны быть положительными целыми числами."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Добавление товара.
    if request.method == "POST":
        product = Product.objects.filter(
            id=product_id,
            is_active=True,
            is_deleted=False,
            category__is_active=True,
            category__is_deleted=False,
        ).first()

        if product is None:
            return Response(
                {"detail": "Товар не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_count = cart.items.get(str(product_id), 0)

        if current_count + count > product.count:
            return Response(
                {"detail": "Недостаточно товара на складе."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.add(product_id, count)

        return Response(serialize_basket(request, cart))

    # Уменьшение количества или удаление товара.
    cart.remove(product_id, count)

    return Response(serialize_basket(request, cart))
