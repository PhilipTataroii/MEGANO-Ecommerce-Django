from datetime import date
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from catalog.serializers import ProductShortSerializer
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Информация о заказе в формате Swagger MEGANO."""

    createdAt = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M",
        read_only=True,
    )

    fullName = serializers.CharField(
        source="full_name",
        read_only=True,
    )

    deliveryType = serializers.CharField(
        source="delivery_type",
        read_only=True,
    )

    paymentType = serializers.CharField(
        source="payment_type",
        read_only=True,
    )

    totalCost = serializers.FloatField(
        source="total_cost",
        read_only=True,
    )

    deliveryCost = serializers.FloatField(
        source="delivery_cost",
        read_only=True,
    )

    products = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "createdAt",
            "fullName",
            "email",
            "phone",
            "deliveryType",
            "paymentType",
            "totalCost",
            "deliveryCost",
            "status",
            "payment_error",
            "city",
            "address",
            "comment",
            "products",
        )

    @extend_schema_field(ProductShortSerializer(many=True))
    def get_products(self, obj):
        """Возвращаем товары заказа с сохранёнными ценами."""

        request = self.context.get("request")
        result = []

        for item in obj.items.all():
            product_data = ProductShortSerializer(
                item.product,
                context={"request": request},
            ).data

            product_data["count"] = item.count
            product_data["price"] = float(item.price)

            result.append(product_data)

        return result


class OrderConfirmSerializer(serializers.Serializer):
    """Проверка данных покупателя при подтверждении заказа."""

    fullName = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)

    deliveryType = serializers.ChoiceField(
        choices=["ordinary", "express"],
    )

    paymentType = serializers.ChoiceField(
        choices=["online", "someone"],
    )

    city = serializers.CharField(max_length=150)
    address = serializers.CharField(max_length=255)

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=2000,
    )



class PaymentSerializer(serializers.Serializer):
    """Проверка номера для фиктивной оплаты по ТЗ Skillbox."""

    number = serializers.CharField(
        min_length=1,
        max_length=8,
        trim_whitespace=False,
    )

    def validate_number(self, value):
        """Проверяет формат и чётность учебного номера."""
        from .payment_service import validate_payment_number

        try:
            return validate_payment_number(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error))
