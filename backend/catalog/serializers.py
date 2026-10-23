
from django.db.models import Avg
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import (
    Category,
    Product,
    ProductImage,
    Tag,
    Review,
    Specification,
)

from .translations import get_translated_value


class CategoryImageSerializer(serializers.Serializer):
    """Изображение категории."""

    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, obj) -> str:
        if not obj.icon:
            return ""

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.icon.url)

        return obj.icon.url

    def get_alt(self, obj):
        return get_translated_value(obj, "title")


class SubcategorySerializer(serializers.ModelSerializer):
    """Подкатегория с переводом названия."""

    title = serializers.SerializerMethodField()
    image = CategoryImageSerializer(source="*", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "image")

    def get_title(self, obj):
        return get_translated_value(obj, "title")


class CategorySerializer(serializers.ModelSerializer):
    """Категория с переводом и подкатегориями."""

    title = serializers.SerializerMethodField()
    image = CategoryImageSerializer(source="*", read_only=True)
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")

    def get_title(self, obj):
        return get_translated_value(obj, "title")

    @extend_schema_field(SubcategorySerializer(many=True))
    def get_subcategories(self, obj):
        subcategories = [
            child
            for child in obj.children.all()
            if child.is_active and not child.is_deleted
        ]

        return SubcategorySerializer(
            subcategories,
            many=True,
            context=self.context,
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Тег с переводом названия."""

    name = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ("id", "name")

    def get_name(self, obj):
        return get_translated_value(obj, "name")


class ProductImageSerializer(serializers.ModelSerializer):
    """Изображение товара."""

    src = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("src", "alt")

    def get_src(self, obj) -> str:
        if not obj.image:
            return ""

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class ProductShortSerializer(serializers.ModelSerializer):
    """Краткая информация о товаре для каталога."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    price = serializers.FloatField(read_only=True)

    date = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    freeDelivery = serializers.BooleanField(
        source="free_delivery",
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    tags = TagSerializer(
        many=True,
        read_only=True,
    )

    reviews = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        )

    def get_title(self, obj):
        return get_translated_value(obj, "title")

    def get_description(self, obj):
        return get_translated_value(obj, "description")

    @extend_schema_field(serializers.IntegerField())
    def get_reviews(self, obj):
        """Количество отзывов о товаре."""
        if hasattr(obj, "reviews_count"):
            return obj.reviews_count

        return obj.reviews.count()

    @extend_schema_field(serializers.FloatField())
    def get_rating(self, obj) -> float:
        """Средняя оценка товара."""
        average = getattr(obj, "average_rating", None)

        if average is None:
            average = obj.reviews.aggregate(
                average_rating=Avg("rate")
            )["average_rating"]

        if average is None:
            return 0.0

        return round(average, 1)


class ReviewSerializer(serializers.ModelSerializer):
    """Отзыв покупателя."""

    date = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "author",
            "email",
            "text",
            "rate",
            "date",
        )


class SpecificationSerializer(serializers.ModelSerializer):
    """Характеристика товара с переводом."""

    name = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = Specification
        fields = ("name", "value")

    def get_name(self, obj):
        return get_translated_value(obj, "name")

    def get_value(self, obj):
        return get_translated_value(obj, "value")


class ProductFullSerializer(serializers.ModelSerializer):
    """Полная информация о товаре."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    fullDescription = serializers.SerializerMethodField()

    price = serializers.FloatField(read_only=True)

    date = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    freeDelivery = serializers.BooleanField(
        source="free_delivery",
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    tags = serializers.SerializerMethodField()

    reviews = ReviewSerializer(
        many=True,
        read_only=True,
    )

    specifications = SpecificationSerializer(
        many=True,
        read_only=True,
    )

    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "fullDescription",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "specifications",
            "rating",
        )

    def get_title(self, obj):
        return get_translated_value(obj, "title")

    def get_description(self, obj):
        return get_translated_value(obj, "description")

    def get_fullDescription(self, obj):
        return get_translated_value(
            obj,
            "full_description",
        )

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_tags(self, obj):
        """Сохраняем формат списка строк для страницы товара."""
        return [
            get_translated_value(tag, "name")
            for tag in obj.tags.all()
        ]

    @extend_schema_field(serializers.FloatField())
    def get_rating(self, obj) -> float:
        """Средняя оценка товара."""
        average = getattr(obj, "average_rating", None)

        if average is None:
            average = obj.reviews.aggregate(
                average_rating=Avg("rate")
            )["average_rating"]

        if average is None:
            return 0.0

        return round(average, 1)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Проверка данных при создании отзыва."""

    class Meta:
        model = Review
        fields = (
            "author",
            "email",
            "text",
            "rate",
        )

    def validate_author(self, value):
        """Имя автора не должно состоять из пробелов."""
        if not value.strip():
            raise serializers.ValidationError(
                "Укажите имя автора."
            )

        return value.strip()

    def validate_text(self, value):
        """Отзыв не должен быть пустым."""
        if not value.strip():
            raise serializers.ValidationError(
                "Напишите текст отзыва."
            )

        return value.strip()

    def validate_rate(self, value):
        """Оценка должна быть от 1 до 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Оценка должна быть от 1 до 5."
            )

        return value
