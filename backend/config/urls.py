from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from basket.views import basket_view

from orders.views import (
    orders_view,
    order_detail_view,
    payment_view,
    cancel_order_view,
)

from catalog.views import (
    categories_list,
    catalog_list,
    product_detail,
    product_review_create,
    tags_list,
    popular_products,
    limited_products,
    banners_list,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


# Основные маршруты интернет-магазина.
urlpatterns = [
    # Панель администратора Django.
    path("admin/", admin.site.urls),

    # API каталога товаров.
    path("api/categories", categories_list, name="categories-list"),
    path("api/catalog", catalog_list, name="catalog-list"),
    path("api/product/<int:id>", product_detail, name="product-detail"),
    path(
        "api/product/<int:id>/review",
        product_review_create,
        name="product-review-create",
    ),
    path("api/tags", tags_list, name="tags-list"),

    # API главной страницы.
    path("api/products/popular", popular_products, name="popular-products"),
    path("api/products/limited", limited_products, name="limited-products"),
    path("api/banners", banners_list, name="banners-list"),

    # API корзины.
    path("api/basket", basket_view, name="basket"),

    # API заказов и оплаты.
    path("api/orders", orders_view, name="orders"),
    path("api/order/<int:order_id>", order_detail_view, name="order-detail"),
    path("api/orders/<int:order_id>", order_detail_view, name="order-detail-alias"),
    path("api/payment/<int:order_id>", payment_view, name="payment"),
    path("api/order/<int:order_id>/cancel", cancel_order_view, name="order-cancel"),

    # API авторизации и профиля.
    path("api/", include("accounts.urls")),

    # Страницы фронтенда MEGANO.
    path("", include("frontend.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("i18n/", include("django.conf.urls.i18n")),
]


# Отображение загруженных изображений при разработке.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )