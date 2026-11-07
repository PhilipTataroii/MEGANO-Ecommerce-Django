# MEGANO — Платформа электронной коммерции

🌐 **Языки документации**

🇬🇧 [English](README.md) | 🇷🇺 **Русский** | 🇷🇴 [Română](README.ro.md)

## О проекте

MEGANO — полнофункциональное веб-приложение электронной коммерции, разработанное с использованием Python, Django и Django REST Framework.

Проект создан в качестве итоговой дипломной работы программы профессионального обучения Python Developer от Skillbox в партнёрстве с GeekBrains.

Приложение демонстрирует практические навыки backend-разработки, проектирования REST API, управления базами данных, аутентификации пользователей, обработки заказов и автоматизированного тестирования.

## Возможности проекта

- Каталог товаров с категориями и подробными страницами товаров
- Поиск, фильтрация и сортировка товаров
- Регистрация, авторизация и управление профилями пользователей
- Корзина покупок для гостей и авторизованных пользователей
- Создание заказов и просмотр истории заказов
- Отмена заказов
- Обработка платежей
- Отзывы о товарах
- Панель администрирования Django
- REST API с документацией Swagger/OpenAPI
- Автоматизированное тестирование

## Используемые технологии

### Backend

- Python
- Django 5.2
- Django REST Framework
- SQLite
- drf-spectacular

### Frontend

- HTML
- CSS
- JavaScript
- Django Templates

### Инструменты разработки

- Git
- GitLab
- PyCharm

## Структура проекта

```text
django_diploma/
├── backend/
│   ├── accounts/
│   │   └── fixtures/
│   │       └── users.json
│   ├── basket/
│   ├── catalog/
│   ├── orders/
│   ├── config/
│   └── manage.py
├── diploma-frontend/
├── requirements.txt
├── README.md
├── README.ru.md
└── README.ro.md
```

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://gitlab.skillbox.ru/filip_tataroi/python_django_diploma.git
cd python_django_diploma
```

### 2. Создание виртуального окружения

```bash
python -m venv .venv
```

Активация в Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

В Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Установка локального frontend-пакета

```bash
pip install -e ./diploma-frontend
```

### 5. Переход в директорию backend

```bash
cd backend
```

### 6. Применение миграций базы данных

```bash
python manage.py migrate
```

### 7. Загрузка демонстрационных данных

```bash
python manage.py loaddata users
python manage.py loaddata catalog
```

Демонстрационные данные содержат две учётные записи:

| Имя пользователя | Роль |
|---|---|
| `demo_admin` | Администратор |
| `demo_customer` | Покупатель |

В целях безопасности пароли по умолчанию отключены.

Чтобы установить пароли локально:

```bash
python manage.py changepassword demo_admin
python manage.py changepassword demo_customer
```

### 8. Запуск сервера разработки

```bash
python manage.py runserver
```

После запуска приложение доступно по адресу:

http://127.0.0.1:8000/

## Документация API

**Интерактивная документация Swagger**

http://127.0.0.1:8000/api/docs/

**Схема OpenAPI**

http://127.0.0.1:8000/api/schema/

### Основные API-маршруты

| Маршрут | Описание |
|---|---|
| `/api/catalog` | Каталог товаров |
| `/api/categories` | Категории товаров |
| `/api/product/<id>` | Информация о товаре |
| `/api/basket` | Корзина покупок |
| `/api/orders` | Управление заказами |
| `/api/payment/<order_id>` | Обработка платежей |
| `/api/products/popular` | Популярные товары |
| `/api/products/limited` | Товары с ограниченным предложением |
| `/api/banners` | Рекламные баннеры |

## Тестирование

Для запуска автоматизированных тестов из директории backend:

```bash
python manage.py test
```

## Примечания по разработке

Данное приложение является учебным проектом, предназначенным для демонстрации навыков разработки в профессиональном портфолио.

Конфигурация по умолчанию предназначена для локальной разработки.

Для развёртывания в производственной среде необходимо настроить защищённые переменные окружения, разрешённые хосты, обработку статических файлов и параметры безопасности Django.

## Автор

**Filip Tataroi**

Python / Django Developer

**Тип проекта:** Итоговый дипломный проект — программа Python Developer от Skillbox

GitHub: https://github.com/PhilipTataroii

LinkedIn: https://www.linkedin.com/in/filip-tataroi/

## Лицензия

Проект разработан в образовательных целях и для демонстрации в портфолио. Лицензия на свободное использование исходного кода не предоставляется, если она не добавлена отдельно.
