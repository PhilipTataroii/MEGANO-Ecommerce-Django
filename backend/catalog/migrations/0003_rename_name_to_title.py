
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_alter_category_options_alter_product_options_and_more"),
    ]

    operations = [
        # Сохраняем существующие названия категорий.
        migrations.RenameField(
            model_name="category",
            old_name="name",
            new_name="title",
        ),

        # Сохраняем существующие названия товаров.
        migrations.RenameField(
            model_name="product",
            old_name="name",
            new_name="title",
        ),
    ]
