from django.db import transaction
from django.db.models import F
from catalog.models import Product
from decimal import Decimal
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer

from basket.cart import Cart
from .models import Order, OrderItem, DeliverySettings

from .serializers import (
    OrderSerializer,
    OrderConfirmSerializer,
    PaymentSerializer,
)


@extend_schema(
    methods=["GET"],
    summary="Получить список заказов",
    responses=OrderSerializer(many=True),
)
@extend_schema(
    methods=["POST"],
    operation_id="create_order_from_basket",
    summary="Создать заказ из корзины",
    request=None,
    responses={
        200: inline_serializer(
            name="OrderCreatedResponse",
            fields={
                "orderId": serializers.IntegerField(),
            },
        ),
    },
)
@api_view(["GET", "POST"])
def orders_view(request):
    """Получение списка заказов и создание нового заказа."""

    if request.method == "GET":
        if not request.user.is_authenticated:
            return Response([])

        orders = Order.objects.filter(
            user=request.user,
            is_deleted=False,
        ).prefetch_related(
            "items__product__images",
            "items__product__tags",
        )

        serializer = OrderSerializer(
            orders,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    # Получаем товары из серверной корзины.
    cart = Cart(request)
    items = cart.get_items()

    if not items:
        return Response(
            {"detail": "Корзина пуста."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Проверяем остатки товаров.
    for item in items:
        product = item["product"]
        if item["count"] > product.count:
            return Response(
                {"detail": f"Недостаточно товара: {product.title}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    total_cost = sum(
        (item["price"] * item["count"] for item in items),
        start=Decimal("0.00"),
    )

    # Создаём заказ и резервируем товары в одной транзакции.
    with transaction.atomic():
        for item in items:
            product = item["product"]
            quantity = item["count"]

            # Уменьшаем остаток только при достаточном количестве.
            updated = Product.objects.filter(
                pk=product.pk,
                count__gte=quantity,
                is_active=True,
                is_deleted=False,
            ).update(count=F("count") - quantity)

            if updated != 1:
                # Откат всей транзакции при нехватке товара.
                transaction.set_rollback(True)
                return Response(
                    {
                        "detail": (
                            f"Недостаточно товара: {product.title}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_cost=total_cost,
            status="created",
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item["product"],
                count=item["count"],
                price=item["price"],
            )
            for item in items
        ])

        # Очищаем корзину после успешного создания заказа.
        cart.clear()

    # Запоминаем гостевой заказ в сессии покупателя.
    if not request.user.is_authenticated:
        guest_order_ids = request.session.get("guest_order_ids", [])
        guest_order_ids.append(order.id)
        request.session["guest_order_ids"] = guest_order_ids
        request.session.modified = True

    return Response(
        {"orderId": order.id},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    methods=["GET"],
    summary="Получить информацию о заказе",
    responses=OrderSerializer,
)
@extend_schema(
    methods=["POST"],
    summary="Подтвердить заказ",
    request=OrderConfirmSerializer,
    responses={
        200: inline_serializer(
            name="OrderConfirmedResponse",
            fields={
                "orderId": serializers.IntegerField(),
            },
        ),
    },
)
@api_view(["GET", "POST"])
def order_detail_view(request, order_id):
    """Просмотр и подтверждение заказа."""

    order = Order.objects.filter(
        pk=order_id,
        is_deleted=False,
    ).first()

    if order is None:
        return Response(
            {"detail": "Заказ не найден."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Авторизованный пользователь не должен видеть чужие заказы.
    if order.user_id is not None:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.pk
        ):
            return Response(
                {"detail": "Доступ запрещён."},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        # Гостевой заказ доступен только в сессии его создателя.
        if order.id not in request.session.get("guest_order_ids", []):
            return Response(
                {"detail": "Доступ запрещён."},
                status=status.HTTP_403_FORBIDDEN,
            )

    if request.method == "GET":
        serializer = OrderSerializer(
            order,
            context={"request": request},
        )
        return Response(serializer.data)

    if order.status != "created":
        return Response(
            {"detail": "Заказ уже подтверждён."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = OrderConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    order.full_name = data["fullName"]
    order.email = data["email"]
    order.phone = data["phone"]
    order.delivery_type = data["deliveryType"]
    order.payment_type = data["paymentType"]
    order.city = data["city"]
    order.address = data["address"]
    order.comment = data.get("comment", "")

    # Получаем настройки доставки из базы данных.
    delivery_settings = DeliverySettings.objects.order_by("pk").first()

    if delivery_settings is None:
        delivery_settings = DeliverySettings.objects.create()

    # Стоимость товаров без доставки.
    products_total = sum(
        (item.price * item.count for item in order.items.all()),
        start=Decimal("0.00"),
    )

    # Рассчитываем стоимость выбранной доставки.
    order.delivery_cost = delivery_settings.calculate_delivery(
        products_total,
        order.delivery_type,
    )

    # Итоговая стоимость: товары + доставка.
    order.total_cost = products_total + order.delivery_cost

    order.status = "accepted"
    order.save()

    return Response(
        {"orderId": order.id},
        status=status.HTTP_200_OK,
    )



@extend_schema(
    methods=["POST"],
    summary="Оплатить заказ",
    description="Отправляет учебный платёж в очередь обработки.",
    request=PaymentSerializer,
    responses={
        202: inline_serializer(
            name="PaymentAcceptedResponse",
            fields={
                "detail": serializers.CharField(),
                "status": serializers.CharField(),
                "orderId": serializers.IntegerField(),
            },
        ),
    },
)
@api_view(["POST"])
def payment_view(request, order_id):
    """Добавляет учебный платёж в очередь обработки."""

    # Проверяем существование заказа.
    order = Order.objects.filter(
        pk=order_id,
        is_deleted=False,
    ).first()

    if order is None:
        return Response(
            {"detail": "Заказ не найден."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Проверяем доступ к заказу.
    if order.user_id is not None:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.pk
        ):
            return Response(
                {"detail": "Доступ запрещён."},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        if order.id not in request.session.get("guest_order_ids", []):
            return Response(
                {"detail": "Доступ запрещён."},
                status=status.HTTP_403_FORBIDDEN,
            )

    # Повторно оплачивать успешный платёж нельзя.
    if order.status == "paid":
        return Response(
            {"detail": "Заказ уже оплачен."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Не допускаем повторной отправки ожидающего платежа.
    if order.status == "pending":
        return Response(
            {"detail": "Платёж уже ожидает обработки."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Разрешаем новую попытку после ошибки.
    if order.status not in ("accepted", "failed"):
        return Response(
            {"detail": "Сначала подтвердите заказ."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Разрешаем оба учебных способа оплаты.
    if order.payment_type not in ("online", "someone"):
        return Response(
            {"detail": "Неподдерживаемый способ оплаты."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Проверяем учебный номер.
    serializer = PaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Сохраняем только фиктивный номер, без банковских реквизитов.
    order.payment_number = serializer.validated_data["number"]
    order.payment_error = ""
    order.status = "pending"

    order.save(
        update_fields=[
            "payment_number",
            "payment_error",
            "status",
        ]
    )

    return Response(
        {
            "detail": "Платёж добавлен в очередь обработки.",
            "status": "pending",
            "orderId": order.id,
        },
        status=status.HTTP_202_ACCEPTED,
    )



@extend_schema(
    methods=["POST"],
    summary="Отменить заказ",
    description=(
        "Отменяет заказ и возвращает товары на склад. "
        "Отмена доступна только для заказов без активного платежа."
    ),
    request=None,
    responses={
        200: inline_serializer(
            name="OrderCancelledResponse",
            fields={
                "detail": serializers.CharField(),
                "status": serializers.CharField(),
                "orderId": serializers.IntegerField(),
            },
        ),
    },
)
@api_view(["POST"])
def cancel_order_view(request, order_id):
    """Отменяет заказ и возвращает товары на склад."""

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(
            pk=order_id,
            is_deleted=False,
        ).first()

        if order is None:
            return Response(
                {"detail": "Заказ не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем права доступа к заказу.
        if order.user_id is not None:
            if (
                not request.user.is_authenticated
                or order.user_id != request.user.pk
            ):
                return Response(
                    {"detail": "Доступ запрещён."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            guest_order_ids = request.session.get(
                "guest_order_ids", []
            )

            if order.id not in guest_order_ids:
                return Response(
                    {"detail": "Доступ запрещён."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Отменять можно только заказ без активного платежа.
        if order.status not in ("created", "accepted", "failed"):
            return Response(
                {
                    "detail": (
                        "Этот заказ нельзя отменить. "
                        "Возможно, он уже оплачен или ожидает оплаты."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Возвращаем зарезервированные товары на склад.
        for item in order.items.all():
            Product.objects.filter(pk=item.product_id).update(
                count=F("count") + item.count
            )

        # Меняем статус в той же транзакции.
        order.status = "cancelled"
        order.save(update_fields=["status"])

    return Response(
        {
            "detail": "Заказ отменён. Товары возвращены на склад.",
            "status": "cancelled",
            "orderId": order.id,
        },
        status=status.HTTP_200_OK,
    )
