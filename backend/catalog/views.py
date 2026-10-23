
import unicodedata

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    inline_serializer,
)

from .models import Category, Product, Tag
from .translations import get_translated_value, get_current_language

from .serializers import (
    CategorySerializer,
    ProductShortSerializer,
    ProductFullSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    TagSerializer,
)

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404


@extend_schema(
    summary="Получить список категорий",
    responses=CategorySerializer(many=True),
)
@api_view(["GET"])
def categories_list(request):
    """
    Возвращает каталог категорий в формате Swagger.

    Родительские категории содержат вложенный
    список активных подкатегорий.
    """

    categories = (
        Category.objects.filter(
            parent__isnull=True,
            is_active=True,
            is_deleted=False,
        )
        .prefetch_related("children")
        .order_by("title")
    )

    serializer = CategorySerializer(
        categories,
        many=True,
        context={"request": request},
    )

    return Response(serializer.data)



def normalize_search(text):
    text = unicodedata.normalize("NFD", text.casefold())
    return "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )



@extend_schema_view(
    get=extend_schema(
        summary="Получить каталог товаров",
        responses=inline_serializer(
            name="CatalogListResponse",
            fields={
                "items": ProductShortSerializer(many=True),
                "currentPage": serializers.IntegerField(),
                "lastPage": serializers.IntegerField(),
            },
        ),
        parameters=[
        OpenApiParameter("filter[name]", str, description="Поиск по названию товара"),
        OpenApiParameter("filter[minPrice]", float, description="Минимальная цена"),
        OpenApiParameter("filter[maxPrice]", float, description="Максимальная цена"),
        OpenApiParameter("filter[freeDelivery]", bool, description="Бесплатная доставка"),
        OpenApiParameter("filter[available]", bool, description="Только товары в наличии"),
        OpenApiParameter("category", int, description="ID категории"),
        OpenApiParameter("sort", str, description="Поле сортировки: price, date и другие"),
        OpenApiParameter("sortType", str, enum=["inc", "dec"], description="Направление сортировки"),
        OpenApiParameter("currentPage", int, description="Номер страницы"),
        OpenApiParameter("limit", int, description="Количество товаров на странице (максимум 100)"),
    ],
    ),
)

@api_view(["GET"])
def catalog_list(request):
    """
    Каталог товаров с фильтрацией и пагинацией.
    Параметры соответствуют Swagger.
    """

    # Получаем активные товары и заранее рассчитываем рейтинг.
    products = (
        Product.objects.filter(
            is_active=True,
            is_deleted=False,
        )
        .select_related("category")
        .prefetch_related("images", "tags")
        .annotate(
            reviews_count=Count("reviews", distinct=True),
            average_rating=Avg("reviews__rate"),
        )
    )

    # Получаем параметры фильтрации.
    name = request.query_params.get("filter[name]")
    min_price = request.query_params.get("filter[minPrice]")
    max_price = request.query_params.get("filter[maxPrice]")
    free_delivery = request.query_params.get("filter[freeDelivery]")
    available = request.query_params.get("filter[available]")
    category = request.query_params.get("category")

    # Фильтр по названию товара.
    if name:
        language = get_current_language()
        search_text = normalize_search(name.strip())

        matching_ids = []

        for product in products.prefetch_related("translations"):
            titles = [product.title]

            titles.extend(
                translation.title
                for translation in product.translations.all()
                if translation.language == language
            )

            if any(
                    search_text in normalize_search(title)
                    for title in titles
            ):
                matching_ids.append(product.id)

        products = products.filter(id__in=matching_ids)

    # Фильтры по цене.
    try:
        if min_price not in (None, ""):
            products = products.filter(price__gte=min_price)

        if max_price not in (None, ""):
            products = products.filter(price__lte=max_price)
    except (ValueError, TypeError):
        return Response(
            {"detail": "Некорректное значение цены."},
            status=400,
        )

    # Фильтр по бесплатной доставке.
    # Если галочка выключена, показываем все товары.
    if free_delivery and free_delivery.lower() == "true":
        products = products.filter(free_delivery=True)

    # Фильтр по наличию на складе.
    # Если галочка выключена, не ограничиваем выборку.
    if available and available.lower() == "true":
        products = products.filter(count__gt=0)

    # Фильтр по категории.
    if category:
        try:
            products = products.filter(category_id=int(category))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Некорректный ID категории."},
                status=400,
            )



    # Фильтрация товаров по тегам.
    # Пример: /catalog?tags=1
    # Несколько тегов: /catalog?tags=1,2

    tags_param = request.query_params.get("tags")

    if not tags_param:
        tag_values = request.query_params.getlist("tags[]")
        if tag_values:
            tags_param = ",".join(tag_values)

    if tags_param:
        try:
            tag_ids = [
                int(tag_id.strip())
                for tag_id in tags_param.split(",")
            ]

            # ID тегов должны быть положительными.
            if any(tag_id <= 0 for tag_id in tag_ids):
                raise ValueError

        except ValueError:
            return Response(
                {"detail": "Некорректные ID тегов."},
                status=400,
            )

        # Товар должен содержать хотя бы один указанный тег.
        products = products.filter(
            tags__id__in=tag_ids
        ).distinct()


    # Получаем параметры сортировки из Swagger.
    sort = request.query_params.get("sort")
    sort_type = request.query_params.get("sortType", "inc")

    # Разрешённые направления сортировки.
    if sort_type not in ("inc", "dec"):
        return Response(
            {"detail": "sortType должен быть inc или dec."},
            status=400,
        )

    # Поля сортировки согласно Swagger.
    sort_fields = {
        "price": "price",
        "date": "created_at",
        "rating": "average_rating",
        "reviews": "reviews_count",
    }

    if sort:
        if sort not in sort_fields:
            return Response(
                {"detail": "Указанный тип сортировки пока не поддерживается."},
                status=400,
            )

        sort_field = sort_fields[sort]

        # dec — по убыванию, inc — по возрастанию.
        if sort_type == "dec":
            sort_field = f"-{sort_field}"

        products = products.order_by(sort_field, "id")
    else:
        products = products.order_by("sort_index", "id")

    # Получаем параметры пагинации.
    try:
        current_page = int(request.query_params.get("currentPage", 1))
        limit = int(request.query_params.get("limit", 20))
    except (ValueError, TypeError):
        return Response(
            {"detail": "Неверные параметры пагинации."},
            status=400,
        )

    if current_page < 1 or limit < 1:
        return Response(
            {"detail": "Номер страницы и лимит должны быть больше нуля."},
            status=400,
        )

    limit = min(limit, 100)

    paginator = Paginator(products, limit)

    if current_page > paginator.num_pages:
        items = []
    else:
        items = paginator.page(current_page).object_list

    serializer = ProductShortSerializer(
        items,
        many=True,
        context={"request": request},
    )

    return Response({
        "items": serializer.data,
        "currentPage": current_page,
        "lastPage": paginator.num_pages,
    })


@extend_schema(
    summary="Получить подробную информацию о товаре",
    responses=ProductFullSerializer,
)
@api_view(["GET"])
def product_detail(request, id):
    """Получение полной информации об одном товаре."""

    # Получаем только активный и не удалённый товар.
    # Связанные данные загружаем заранее для оптимизации запросов.
    products = (
        Product.objects.filter(
            is_active=True,
            is_deleted=False,
        )
        .select_related("category")
        .prefetch_related(
            "images",
            "tags",
            "reviews",
            "specifications",
        )
        .annotate(
            average_rating=Avg("reviews__rate"),
        )
    )

    # Если товара нет, возвращаем HTTP 404.
    product = get_object_or_404(products, pk=id)

    # Преобразуем товар в JSON по схеме ProductFull.
    serializer = ProductFullSerializer(
        product,
        context={"request": request},
    )

    return Response(serializer.data)


@extend_schema(
    summary="Добавить отзыв о товаре",
    request=ReviewCreateSerializer,
    responses={200: ReviewSerializer(many=True)},
)
@api_view(["POST"])
def product_review_create(request, id):
    """Добавление отзыва к товару."""

    # Проверяем, существует ли активный товар.
    product = get_object_or_404(
        Product,
        pk=id,
        is_active=True,
        is_deleted=False,
    )

    # Проверяем данные, отправленные покупателем.
    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Сохраняем отзыв и связываем его с товаром.
    serializer.save(product=product)

    # Получаем обновлённый список отзывов.
    reviews = product.reviews.all().order_by("-created_at")

    # Возвращаем отзывы в формате Swagger.
    response_serializer = ReviewSerializer(
        reviews,
        many=True,
        context={"request": request},
    )

    return Response(response_serializer.data)



@extend_schema(
    summary="Получить список тегов",
    parameters=[
        OpenApiParameter(
            name="category",
            type=int,
            description="ID категории для фильтрации тегов",
            required=False,
        ),
    ],
    responses=TagSerializer(many=True),
)
@api_view(["GET"])
def tags_list(request):
    """Получение списка тегов с фильтрацией по категории."""

    # Получаем все теги в алфавитном порядке.
    tags = Tag.objects.all().order_by("name")

    # Получаем ID категории из параметров запроса.
    category_id = request.query_params.get("category")

    if category_id is not None:
        try:
            category_id = int(category_id)

            if category_id <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return Response(
                {"detail": "Некорректный ID категории."},
                status=400,
            )

        # Фильтруем теги по активным товарам категории.
        # products — обратная связь ManyToMany модели Tag.
        tags = tags.filter(
            products__category_id=category_id,
            products__is_active=True,
            products__is_deleted=False,
        ).distinct()

    # Возвращаем результат в формате Swagger.
    serializer = TagSerializer(tags, many=True)

    return Response(serializer.data)



@extend_schema(
    summary="Получить популярные товары",
    responses=ProductShortSerializer(many=True),
)
@api_view(["GET"])
def popular_products(request):
    """Возвращает до 8 популярных товаров для главной страницы."""

    # Выбираем только активные и неудалённые товары.
    products = (
        Product.objects.filter(
            is_active=True,
            is_deleted=False,
            category__is_active=True,
            category__is_deleted=False,
        )
        .select_related("category")
        .prefetch_related("images", "tags", "reviews")
        .order_by("sort_index", "id")[:8]
    )

    # Используем готовый сериализатор каталога.
    serializer = ProductShortSerializer(
        products,
        many=True,
        context={"request": request},
    )

    return Response(serializer.data)


@extend_schema(
    summary="Получить товары ограниченного тиража",
    responses=ProductShortSerializer(many=True),
)
@api_view(["GET"])
def limited_products(request):
    """Возвращает до 16 товаров ограниченного тиража."""

    products = (
        Product.objects.filter(
            is_active=True,
            is_deleted=False,
            is_limited=True,
            category__is_active=True,
            category__is_deleted=False,
        )
        .select_related("category")
        .prefetch_related("images", "tags", "reviews")
        .order_by("sort_index", "id")[:16]
    )

    serializer = ProductShortSerializer(
        products,
        many=True,
        context={"request": request},
    )

    return Response(serializer.data)



@extend_schema(
    summary="Получить баннеры главной страницы",
    responses=inline_serializer(
        name="BannerResponse",
        fields={
            "category": serializers.IntegerField(),
            "title": serializers.CharField(),
            "price": serializers.FloatField(),
            "images": inline_serializer(
                name="BannerImage",
                fields={
                    "src": serializers.CharField(),
                    "alt": serializers.CharField(),
                },
                many=True,
            ),
        },
        many=True,
    ),
)
@api_view(["GET"])
def banners_list(request):
    """Возвращает до трёх баннеров главной страницы MEGANO."""

    # Получаем три избранные активные категории.
    categories = (
        Category.objects.filter(
            is_featured=True,
            is_active=True,
            is_deleted=False,
            parent__isnull=True,
        )
        .order_by("id")[:3]
    )

    banners = []

    for category in categories:
        # Формируем список изображений в формате фронтенда.
        images = []

        if category.icon:
            images.append({
                "src": request.build_absolute_uri(category.icon.url),
                "alt": get_translated_value(category, "title"),
            })

        # Получаем минимальную цену активного товара категории.
        from django.db.models import Min

        min_price = (
            Product.objects.filter(
                category=category,
                is_active=True,
                is_deleted=False,
            )
            .aggregate(price=Min("price"))["price"]
        )

        banners.append({
            "category": category.id,
            "title": get_translated_value(category, "title"),
            "price": float(min_price) if min_price is not None else 0,
            "images": images,
        })

    return Response(banners)

