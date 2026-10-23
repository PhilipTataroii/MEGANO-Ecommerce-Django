
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Tag, Review, Specification

class CategoryModelTests(TestCase):
    """Автоматические тесты модели категорий."""

    def setUp(self):
        """Создаём основную категорию перед каждым тестом."""
        self.category = Category.objects.create(
            title="Electronics",
            description="Electronic devices",
        )

    def test_category_creation(self):
        """Проверяем создание категории."""
        self.assertEqual(self.category.title, "Electronics")
        self.assertTrue(self.category.is_active)
        self.assertFalse(self.category.is_deleted)

    def test_subcategory_creation(self):
        """Проверяем создание подкатегории."""
        subcategory = Category.objects.create(
            title="Laptops",
            parent=self.category,
        )

        self.assertEqual(subcategory.parent, self.category)

    def test_third_level_is_not_allowed(self):
        """Запрещаем создание третьего уровня категорий."""
        subcategory = Category.objects.create(
            title="Laptops",
            parent=self.category,
        )

        with self.assertRaises(ValidationError):
            Category.objects.create(
                title="Gaming Laptops",
                parent=subcategory,
            )

    def test_category_cannot_be_its_own_parent(self):
        """Категория не может быть родителем самой себя."""
        self.category.parent = self.category

        with self.assertRaises(ValidationError):
            self.category.save()

    def test_circular_relationship_is_not_allowed(self):
        """Проверяем защиту от циклических связей."""
        subcategory = Category.objects.create(
            title="Laptops",
            parent=self.category,
        )

        self.category.parent = subcategory

        with self.assertRaises(ValidationError):
            self.category.save()

    def test_category_soft_delete(self):
        """Проверяем мягкое удаление категории."""
        category_id = self.category.pk

        self.category.delete()
        self.category.refresh_from_db()

        self.assertEqual(self.category.pk, category_id)
        self.assertTrue(self.category.is_deleted)
        self.assertFalse(self.category.is_active)


class ProductModelTests(TestCase):
    """Автоматические тесты модели товаров."""

    def setUp(self):
        """Создаём категорию и тестовый товар."""
        self.category = Category.objects.create(
            title="Electronics",
        )

        self.product = Product.objects.create(
            title="Test Laptop",
            category=self.category,
            description="Laptop for testing",
            price=Decimal("1500.00"),
        )

    def test_product_creation(self):
        """Проверяем создание товара и его стоимость."""
        self.assertEqual(self.product.title, "Test Laptop")
        self.assertEqual(
            self.product.price,
            Decimal("1500.00"),
        )
        self.assertEqual(self.product.category, self.category)

    def test_product_is_active_by_default(self):
        """Новый товар должен быть активным."""
        self.assertTrue(self.product.is_active)
        self.assertFalse(self.product.is_deleted)

    def test_product_soft_delete(self):
        """Проверяем мягкое удаление товара."""
        product_id = self.product.pk

        self.product.delete()
        self.product.refresh_from_db()

        self.assertEqual(self.product.pk, product_id)
        self.assertTrue(self.product.is_deleted)
        self.assertFalse(self.product.is_active)


class AdminSoftDeleteTests(TestCase):
    """
    Тесты мягкого удаления через Django Admin.

    Проверяем удаление отдельных объектов
    и массовое удаление товаров и категорий.
    """

    def setUp(self):
        """Создаём администратора и тестовые объекты."""
        User = get_user_model()

        self.admin_user = User.objects.create_superuser(
            username="test_admin",
            email="admin@example.com",
            password="TestPassword123!",
        )

        # Авторизуем администратора
        self.client.force_login(self.admin_user)

        # Создаём категорию и два товара
        self.category = Category.objects.create(
            title="Electronics",
        )

        self.product1 = Product.objects.create(
            title="Laptop",
            category=self.category,
            price=Decimal("1000.00"),
        )

        self.product2 = Product.objects.create(
            title="Smartphone",
            category=self.category,
            price=Decimal("500.00"),
        )

    def test_admin_single_product_soft_delete(self):
        """Проверяем удаление одного товара через админку."""
        url = reverse(
            "admin:catalog_product_delete",
            args=[self.product1.pk],
        )

        response = self.client.post(
            url,
            {"post": "yes"},
        )

        self.assertEqual(response.status_code, 302)

        # Товар должен остаться в базе данных
        self.product1.refresh_from_db()

        self.assertTrue(self.product1.is_deleted)
        self.assertFalse(self.product1.is_active)

    def test_admin_bulk_product_soft_delete(self):
        """Проверяем массовое удаление товаров."""
        url = reverse("admin:catalog_product_changelist")

        response = self.client.post(
            url,
            {
                "action": "delete_selected",
                "_selected_action": [
                    str(self.product1.pk),
                    str(self.product2.pk),
                ],
                "post": "yes",
            },
        )

        self.assertEqual(response.status_code, 302)

        # Проверяем сохранение обоих товаров
        for product in (self.product1, self.product2):
            product.refresh_from_db()

            self.assertTrue(product.is_deleted)
            self.assertFalse(product.is_active)

    def test_admin_single_category_soft_delete(self):
        """Проверяем удаление одной категории без товаров."""
        category = Category.objects.create(
            title="Test Category",
        )

        url = reverse(
            "admin:catalog_category_delete",
            args=[category.pk],
        )

        response = self.client.post(
            url,
            {"post": "yes"},
        )

        self.assertEqual(response.status_code, 302)

        category.refresh_from_db()

        self.assertTrue(category.is_deleted)
        self.assertFalse(category.is_active)

    def test_admin_bulk_category_soft_delete(self):
        """
        Проверяем массовое удаление категорий.

        Используем категории без связанных товаров,
        чтобы проверить механизм Soft Delete отдельно.
        """
        first_category = Category.objects.create(
            title="Test Category One",
        )

        second_category = Category.objects.create(
            title="Test Category Two",
        )

        url = reverse("admin:catalog_category_changelist")

        response = self.client.post(
            url,
            {
                "action": "delete_selected",
                "_selected_action": [
                    str(first_category.pk),
                    str(second_category.pk),
                ],
                "post": "yes",
            },
        )

        # Проверяем код ответа и состояние записей
        self.assertEqual(response.status_code, 302)

        for category in (first_category, second_category):
            category.refresh_from_db()

            self.assertTrue(category.is_deleted)
            self.assertFalse(category.is_active)



class CatalogAPITests(TestCase):
    """Автоматические тесты API каталога товаров."""

    def setUp(self):
        # Создаём категорию и два товара с разными ценами.
        self.category = Category.objects.create(
            title="Электроника",
        )

        self.product1 = Product.objects.create(
            title="Видеокарта",
            category=self.category,
            price=Decimal("15000.00"),
            count=10,
            free_delivery=True,
        )

        self.product2 = Product.objects.create(
            title="Клавиатура",
            category=self.category,
            price=Decimal("2000.00"),
            count=0,
            free_delivery=False,
        )

    def test_catalog_returns_products(self):
        """Каталог возвращает оба активных товара."""
        response = self.client.get("/api/catalog")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)

    def test_filter_by_price(self):
        """Фильтр минимальной цены исключает дешёвый товар."""
        response = self.client.get(
            "/api/catalog",
            {"filter[minPrice]": "10000"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(
            response.json()["items"][0]["title"],
            "Видеокарта",
        )

    def test_filter_by_availability(self):
        """Фильтр наличия исключает товар без остатков."""
        response = self.client.get(
            "/api/catalog",
            {"filter[available]": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_sort_by_price(self):
        """Проверяем сортировку товаров по убыванию цены."""
        response = self.client.get(
            "/api/catalog",
            {"sort": "price", "sortType": "dec"},
        )

        self.assertEqual(response.status_code, 200)

        items = response.json()["items"]

        self.assertEqual(items[0]["title"], "Видеокарта")
        self.assertEqual(items[1]["title"], "Клавиатура")

    def test_catalog_pagination(self):
        """Проверяем разделение товаров на страницы."""
        response = self.client.get(
            "/api/catalog",
            {"currentPage": "1", "limit": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["lastPage"], 2)



class CatalogTagAPITests(TestCase):
    """Проверяем фильтрацию товаров по тегам."""

    def setUp(self):
        # Создаём категорию.
        self.category = Category.objects.create(
            title="Электроника",
        )

        # Создаём два тега.
        self.gaming_tag = Tag.objects.create(name="Gaming")
        self.office_tag = Tag.objects.create(name="Office")

        # Создаём товары.
        self.gaming_product = Product.objects.create(
            title="Игровая видеокарта",
            category=self.category,
            price=Decimal("15000.00"),
            count=10,
        )

        self.office_product = Product.objects.create(
            title="Офисная клавиатура",
            category=self.category,
            price=Decimal("2000.00"),
            count=5,
        )

        # Привязываем теги к товарам.
        self.gaming_product.tags.add(self.gaming_tag)
        self.office_product.tags.add(self.office_tag)

    def test_filter_by_gaming_tag(self):
        """По тегу Gaming возвращается только видеокарта."""
        response = self.client.get(
            "/api/catalog",
            {"tags": str(self.gaming_tag.id)},
        )

        self.assertEqual(response.status_code, 200)

        items = response.json()["items"]

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Игровая видеокарта")

    def test_filter_by_multiple_tags(self):
        """По двум тегам возвращаются оба товара."""
        response = self.client.get(
            "/api/catalog",
            {
                "tags": (
                    f"{self.gaming_tag.id},"
                    f"{self.office_tag.id}"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)

    def test_filter_by_nonexistent_tag(self):
        """Несуществующий тег возвращает пустой каталог."""
        response = self.client.get(
            "/api/catalog",
            {"tags": "999999"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])

    def test_invalid_tag_id(self):
        """Некорректный ID тега возвращает ошибку 400."""
        response = self.client.get(
            "/api/catalog",
            {"tags": "abc"},
        )

        self.assertEqual(response.status_code, 400)



class CategoryAPITests(TestCase):
    """Проверяем API категорий интернет-магазина."""

    def setUp(self):
        # Создаём основную категорию.
        self.category = Category.objects.create(
            title="Электроника",
        )

        # Создаём вложенную подкатегорию.
        self.subcategory = Category.objects.create(
            title="Ноутбуки",
            parent=self.category,
        )

    def test_categories_list(self):
        """API возвращает основную категорию."""
        response = self.client.get("/api/categories")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Электроника")

    def test_subcategories(self):
        """Подкатегория находится внутри основной категории."""
        response = self.client.get("/api/categories")

        data = response.json()
        subcategories = data[0]["subcategories"]

        self.assertEqual(len(subcategories), 1)
        self.assertEqual(
            subcategories[0]["title"],
            "Ноутбуки",
        )

    def test_inactive_category_hidden(self):
        """Неактивные категории не отображаются."""
        self.category.is_active = False
        self.category.save()

        response = self.client.get("/api/categories")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_inactive_subcategory_hidden(self):
        """Неактивные подкатегории не отображаются."""
        self.subcategory.is_active = False
        self.subcategory.save()

        response = self.client.get("/api/categories")

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["subcategories"], [])

    def test_category_image_structure(self):
        """Проверяем формат изображения по Swagger."""
        response = self.client.get("/api/categories")

        image = response.json()[0]["image"]

        self.assertIn("src", image)
        self.assertIn("alt", image)
        self.assertEqual(image["alt"], "Электроника")


class ProductDetailAPITests(TestCase):
    """Тесты API полной информации о товаре."""

    @classmethod
    def setUpTestData(cls):
        # Создаём категорию.
        cls.category = Category.objects.create(
            title="Электроника",
        )

        # Создаём товар.
        cls.product = Product.objects.create(
            category=cls.category,
            title="Игровая видеокарта",
            description="Видеокарта для игр",
            full_description="Полное описание видеокарты",
            price=15000,
            count=10,
            free_delivery=True,
        )

        # Добавляем тег.
        cls.tag = Tag.objects.create(name="Gaming")
        cls.product.tags.add(cls.tag)

        # Добавляем отзыв.
        Review.objects.create(
            product=cls.product,
            author="Filip",
            email="",
            text="Отличная видеокарта!",
            rate=5,
        )

        # Добавляем характеристику.
        Specification.objects.create(
            product=cls.product,
            name="Видеопамять",
            value="8 ГБ",
        )

    def test_product_detail_returns_200(self):
        """Существующий товар должен открываться."""

        response = self.client.get(
            reverse("product-detail", args=[self.product.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_product_detail_contains_required_fields(self):
        """Ответ должен содержать поля из Swagger."""

        response = self.client.get(
            reverse("product-detail", args=[self.product.id])
        )

        data = response.json()

        required_fields = (
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

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, data)

        self.assertEqual(data["title"], "Игровая видеокарта")
        self.assertEqual(
            data["fullDescription"],
            "Полное описание видеокарты",
        )

    def test_product_detail_contains_reviews_and_rating(self):
        """API должен возвращать отзывы и средний рейтинг."""

        response = self.client.get(
            reverse("product-detail", args=[self.product.id])
        )

        data = response.json()

        self.assertEqual(len(data["reviews"]), 1)
        self.assertEqual(data["reviews"][0]["author"], "Filip")
        self.assertEqual(data["reviews"][0]["rate"], 5)
        self.assertEqual(data["rating"], 5.0)

    def test_product_detail_contains_tags_and_specifications(self):
        """API должен возвращать теги и характеристики."""

        response = self.client.get(
            reverse("product-detail", args=[self.product.id])
        )

        data = response.json()

        self.assertEqual(data["tags"], ["Gaming"])
        self.assertEqual(
            data["specifications"],
            [{"name": "Видеопамять", "value": "8 ГБ"}],
        )

    def test_nonexistent_product_returns_404(self):
        """Несуществующий товар должен возвращать ошибку 404."""

        response = self.client.get(
            reverse("product-detail", args=[999999])
        )

        self.assertEqual(response.status_code, 404)


class ProductReviewAPITests(TestCase):
    """Тесты добавления отзывов к товарам."""

    @classmethod
    def setUpTestData(cls):
        # Создаём категорию и тестовый товар.
        cls.category = Category.objects.create(
            title="Электроника",
        )

        cls.product = Product.objects.create(
            category=cls.category,
            title="Игровая видеокарта",
            description="Видеокарта для игр",
            price=15000,
            count=10,
        )

    def test_create_review_success(self):
        """Корректный отзыв успешно сохраняется."""

        response = self.client.post(
            reverse("product-review-create", args=[self.product.id]),
            data={
                "author": "Filip",
                "email": "filip@example.com",
                "text": "Отличная видеокарта!",
                "rate": 5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), 1)

        reviews = response.json()
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["author"], "Filip")
        self.assertEqual(reviews[0]["rate"], 5)

    def test_invalid_rating_returns_400(self):
        """Оценка выше пяти должна отклоняться."""

        response = self.client.post(
            reverse("product-review-create", args=[self.product.id]),
            data={
                "author": "Filip",
                "text": "Хороший товар",
                "rate": 8,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    def test_empty_review_text_returns_400(self):
        """Пустой текст отзыва запрещён."""

        response = self.client.post(
            reverse("product-review-create", args=[self.product.id]),
            data={
                "author": "Filip",
                "text": "   ",
                "rate": 5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    def test_nonexistent_product_returns_404(self):
        """Нельзя оставить отзыв несуществующему товару."""

        response = self.client.post(
            reverse("product-review-create", args=[999999]),
            data={
                "author": "Filip",
                "text": "Отличный товар!",
                "rate": 5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Review.objects.count(), 0)


class TagsAPITests(TestCase):
    """Тесты API получения тегов."""

    @classmethod
    def setUpTestData(cls):
        # Создаём две категории.
        cls.category1 = Category.objects.create(
            title="Компьютеры",
        )
        cls.category2 = Category.objects.create(
            title="Телефоны",
        )

        # Создаём два товара.
        cls.product1 = Product.objects.create(
            category=cls.category1,
            title="Видеокарта",
            price=15000,
            count=10,
        )
        cls.product2 = Product.objects.create(
            category=cls.category2,
            title="Смартфон",
            price=8000,
            count=5,
        )

        # Создаём теги.
        cls.tag1 = Tag.objects.create(name="Gaming")
        cls.tag2 = Tag.objects.create(name="Mobile")

        cls.product1.tags.add(cls.tag1)
        cls.product2.tags.add(cls.tag2)

    def test_get_all_tags(self):
        """Без фильтра возвращаются все теги."""

        response = self.client.get("/api/tags")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_filter_tags_by_category(self):
        """Фильтрация возвращает теги нужной категории."""

        response = self.client.get(
            "/api/tags",
            {"category": self.category1.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Gaming")

    def test_invalid_category_returns_400(self):
        """Некорректный ID категории возвращает ошибку 400."""

        response = self.client.get(
            "/api/tags",
            {"category": "abc"},
        )

        self.assertEqual(response.status_code, 400)

    def test_nonexistent_category_returns_empty_list(self):
        """Для несуществующей категории возвращается пустой список."""

        response = self.client.get(
            "/api/tags",
            {"category": 999999},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])



class HomepageAPITests(TestCase):
    """Тесты API главной страницы интернет-магазина MEGANO."""

    @classmethod
    def setUpTestData(cls):
        # Создаём избранную категорию для баннеров.
        cls.category = Category.objects.create(
            title="Электроника",
            is_featured=True,
        )

        # Создаём обычный популярный товар.
        cls.product1 = Product.objects.create(
            category=cls.category,
            title="Игровая видеокарта",
            price=Decimal("15000.00"),
            count=10,
            sort_index=1,
        )

        # Создаём товар ограниченного тиража.
        cls.product2 = Product.objects.create(
            category=cls.category,
            title="Игровая клавиатура",
            price=Decimal("5000.00"),
            count=5,
            sort_index=2,
            is_limited=True,
        )

    def test_banners_returns_featured_category(self):
        """API баннеров возвращает избранную категорию."""
        response = self.client.get("/api/banners")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["category"], self.category.id)
        self.assertEqual(data[0]["title"], "Электроника")
        self.assertEqual(data[0]["price"], 5000.0)
        self.assertIn("images", data[0])

    def test_banners_excludes_non_featured_categories(self):
        """Обычные категории не должны попадать в баннеры."""
        Category.objects.create(
            title="Одежда",
            is_featured=False,
        )

        response = self.client.get("/api/banners")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_banners_limit_three(self):
        """На главной странице должно быть не более трёх баннеров."""
        for index in range(5):
            Category.objects.create(
                title=f"Категория {index}",
                is_featured=True,
            )

        response = self.client.get("/api/banners")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_popular_products_returns_products(self):
        """Популярные товары возвращаются в правильном порядке."""
        response = self.client.get("/api/products/popular")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Игровая видеокарта")
        self.assertEqual(data[1]["title"], "Игровая клавиатура")

    def test_popular_products_limit_eight(self):
        """API возвращает не более восьми популярных товаров."""
        for index in range(10):
            Product.objects.create(
                category=self.category,
                title=f"Товар {index}",
                price=1000,
                sort_index=index + 3,
            )

        response = self.client.get("/api/products/popular")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)

    def test_limited_products_only(self):
        """В Limited Edition попадают только товары ограниченной серии."""
        response = self.client.get("/api/products/limited")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Игровая клавиатура")

    def test_limited_products_limit_sixteen(self):
        """API возвращает не более 16 товаров ограниченного тиража."""
        for index in range(20):
            Product.objects.create(
                category=self.category,
                title=f"Лимитированный товар {index}",
                price=2000,
                is_limited=True,
            )

        response = self.client.get("/api/products/limited")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 16)

    def test_inactive_products_hidden(self):
        """Неактивные товары не отображаются на главной странице."""
        self.product1.is_active = False
        self.product1.save()

        response = self.client.get("/api/products/popular")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["title"],
            "Игровая клавиатура",
        )

    def test_deleted_products_hidden(self):
        """Удалённые товары не отображаются на главной странице."""
        self.product2.delete()

        response = self.client.get("/api/products/limited")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

