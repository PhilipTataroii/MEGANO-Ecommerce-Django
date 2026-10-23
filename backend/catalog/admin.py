
from django.contrib import admin

from .models import (
    Category,
    Product,
    ProductImage,
    Tag,
    Review,
    Specification,
)


class ProductImageInline(admin.TabularInline):
    """Добавление изображений на странице товара."""

    model = ProductImage
    extra = 1
    fields = ("image", "alt", "sort_index")
    ordering = ("sort_index",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Управление тегами."""

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Управление категориями интернет-магазина."""

    list_display = (
        "id",
        "title",
        "parent",
        "is_active",
        "is_featured",
        "is_deleted",
    )

    list_filter = (
        "is_active",
        "is_featured",
        "is_deleted",
    )

    search_fields = ("title",)
    list_editable = ("is_active", "is_featured")
    ordering = ("title",)

    def delete_model(self, request, obj):
        """Мягкое удаление одной категории."""
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Мягкое удаление нескольких категорий."""
        queryset.update(
            is_deleted=True,
            is_active=False,
        )


class SpecificationInline(admin.TabularInline):
    """Редактирование характеристик прямо в карточке товара."""

    model = Specification
    extra = 1
    fields = ("name", "value")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Управление товарами, изображениями и тегами."""

    list_display = (
        "id",
        "title",
        "category",
        "price",
        "count",
        "free_delivery",
        "sort_index",
        "is_limited",
        "is_active",
        "is_deleted",
    )

    list_filter = (
        "category",
        "tags",
        "free_delivery",
        "is_limited",
        "is_active",
        "is_deleted",
    )

    search_fields = (
        "title",
        "description",
        "full_description",
    )

    list_editable = (
        "price",
        "count",
        "is_active",
        "is_limited",
    )

    ordering = ("sort_index", "title")

    filter_horizontal = ("tags",)

    inlines = [ProductImageInline, SpecificationInline]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "category",
                    "title",
                    "description",
                    "full_description",
                    "tags",
                )
            },
        ),
        (
            "Цена и наличие",
            {
                "fields": (
                    "price",
                    "count",
                    "free_delivery",
                )
            },
        ),
        (
            "Отображение",
            {
                "fields": (
                    "sort_index",
                    "is_limited",
                    "is_active",
                    "is_deleted",
                )
            },
        ),
    )

    def delete_model(self, request, obj):
        """Мягкое удаление одного товара."""
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Мягкое удаление нескольких товаров."""
        queryset.update(
            is_deleted=True,
            is_active=False,
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Управление отзывами покупателей."""

    list_display = (
        "id",
        "product",
        "author",
        "rate",
        "created_at",
    )

    list_filter = (
        "rate",
        "created_at",
    )

    search_fields = (
        "author",
        "product__title",
        "text",
    )

    readonly_fields = ("created_at",)

    # Сначала показываем новые отзывы.
    ordering = ("-created_at",)

