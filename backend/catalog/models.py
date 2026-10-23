
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """Категория товаров с поддержкой одного уровня подкатегорий."""

    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    icon = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
        verbose_name="Изображение категории",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родительская категория",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Показывать на главной странице",
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Удалена",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title

    def clean(self):
        """Запрещает циклы и вложенность более одного уровня."""
        super().clean()

        if self.parent_id is None:
            return

        if self.pk is not None and self.parent_id == self.pk:
            raise ValidationError({
                "parent": "Категория не может быть родителем самой себе."
            })

        visited = set()
        current = self.parent

        while current is not None:
            if current.pk in visited:
                raise ValidationError({
                    "parent": "Обнаружена циклическая связь категорий."
                })

            visited.add(current.pk)

            if self.pk is not None and current.pk == self.pk:
                raise ValidationError({
                    "parent": "Обнаружена циклическая связь категорий."
                })

            current = current.parent

        if self.parent.parent_id is not None:
            raise ValidationError({
                "parent": "Допускается только один уровень подкатегорий."
            })

        if self.pk is not None and self.children.exists():
            raise ValidationError({
                "parent": "Категорию с дочерними категориями нельзя сделать подкатегорией."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Мягкое удаление категории."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])


class Tag(models.Model):
    """Тег для фильтрации товаров."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар интернет-магазина."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Категория",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Краткое описание",
    )
    full_description = models.TextField(
        blank=True,
        verbose_name="Полное описание",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество на складе",
    )
    free_delivery = models.BooleanField(
        default=False,
        verbose_name="Бесплатная доставка",
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="products",
        verbose_name="Теги",
    )

    sort_index = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
    )
    is_limited = models.BooleanField(
        default=False,
        verbose_name="Ограниченная серия",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Удалён",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.title

    def delete(self, using=None, keep_parents=False):
        """Мягкое удаление товара."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])


class ProductImage(models.Model):
    """Изображение товара. Один товар может иметь несколько изображений."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
    )
    image = models.ImageField(
        upload_to="products/",
        verbose_name="Изображение",
    )
    alt = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Описание изображения",
    )
    sort_index = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения",
    )

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ["sort_index", "id"]

    def __str__(self):
        return f"Изображение товара: {self.product.title}"


class Review(models.Model):
    """Отзыв покупателя о товаре."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Товар",
    )

    author = models.CharField(
        max_length=150,
        verbose_name="Имя автора",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Электронная почта",
    )

    text = models.TextField(
        verbose_name="Текст отзыва",
    )

    rate = models.PositiveSmallIntegerField(
        verbose_name="Оценка товара",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

        # Оценка должна находиться в диапазоне от 1 до 5.
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rate__gte=1, rate__lte=5),
                name="review_rate_between_1_and_5",
            ),
        ]

    def __str__(self):
        return f"Отзыв {self.author} о товаре {self.product.title}"

    def clean(self):
        """Проверяем корректность оценки перед сохранением."""
        super().clean()

        if self.rate is not None and not 1 <= self.rate <= 5:
            raise ValidationError({
                "rate": "Оценка должна быть от 1 до 5."
            })

    def save(self, *args, **kwargs):
        # Проверяем данные перед сохранением отзыва.
        self.full_clean()
        return super().save(*args, **kwargs)


class Specification(models.Model):
    """Характеристика товара: название и значение."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specifications",
        verbose_name="Товар",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="Название характеристики",
    )

    value = models.CharField(
        max_length=255,
        verbose_name="Значение характеристики",
    )

    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товаров"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name}: {self.value}"




class CategoryTranslation(models.Model):
    """Переводы названий и описаний категорий."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(
        max_length=2,
        choices=[
            ("ru", "Русский"),
            ("ro", "Română"),
            ("en", "English"),
        ],
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "language"],
                name="unique_category_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.category_id} — {self.language}: {self.title}"


class ProductTranslation(models.Model):
    """Переводы названий и описаний товаров."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(
        max_length=2,
        choices=[
            ("ru", "Русский"),
            ("ro", "Română"),
            ("en", "English"),
        ],
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    full_description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "language"],
                name="unique_product_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.product_id} — {self.language}: {self.title}"


class TagTranslation(models.Model):
    """Переводы названий тегов."""

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(
        max_length=2,
        choices=[
            ("ru", "Русский"),
            ("ro", "Română"),
            ("en", "English"),
        ],
    )
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tag", "language"],
                name="unique_tag_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.tag_id} — {self.language}: {self.name}"


class SpecificationTranslation(models.Model):
    """Переводы характеристик товаров."""

    specification = models.ForeignKey(
        Specification,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(
        max_length=2,
        choices=[
            ("ru", "Русский"),
            ("ro", "Română"),
            ("en", "English"),
        ],
    )
    name = models.CharField(max_length=150)
    value = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["specification", "language"],
                name="unique_specification_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.specification_id} — {self.language}: {self.name}"


