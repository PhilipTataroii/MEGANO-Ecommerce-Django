
from django.contrib import admin

from .models import DeliverySettings, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Товары внутри заказа."""

    model = OrderItem
    extra = 0
    readonly_fields = ("product", "count", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Управление заказами покупателей."""

    list_display = (
        "id",
        "full_name",
        "email",
        "total_cost",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "delivery_type",
        "payment_type",
    )

    search_fields = ("full_name", "email", "phone")

    readonly_fields = ("created_at",)

    inlines = [OrderItemInline]

    def get_queryset(self, request):
        """Не показываем мягко удалённые заказы."""
        queryset = super().get_queryset(request)
        return queryset.filter(is_deleted=False)

    def delete_model(self, request, obj):
        """Удаляем один заказ без удаления из базы."""
        obj.is_deleted = True
        obj.save(update_fields=["is_deleted"])

    def delete_queryset(self, request, queryset):
        """Мягко удаляем несколько выбранных заказов."""
        queryset.update(is_deleted=True)


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    """Настройки стоимости доставки."""

    list_display = (
        "id",
        "free_delivery_threshold",
        "ordinary_delivery_price",
        "express_delivery_price",
    )
