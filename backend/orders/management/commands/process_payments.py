
"""Команда обработки очереди учебных платежей."""

import time

from django.core.management.base import BaseCommand

from orders.models import Order
from orders.payment_processor import process_order_payment


class Command(BaseCommand):
    help = "Обрабатывает ожидающие учебные платежи."

    def add_arguments(self, parser):
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Постоянно проверять очередь платежей.",
        )

        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Интервал проверки в секундах.",
        )

    def process_queue(self):
        """Обрабатывает все ожидающие платежи."""

        order_ids = list(
            Order.objects.filter(
                status="pending",
            ).values_list("id", flat=True)
        )

        for order_id in order_ids:
            success = process_order_payment(order_id)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Заказ №{order_id}: оплата успешна."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Заказ №{order_id}: оплата не выполнена."
                    )
                )

        return len(order_ids)

    def handle(self, *args, **options):
        """Запускает обработку один раз или постоянно."""

        if not options["watch"]:
            count = self.process_queue()
            self.stdout.write(
                f"Обработано платежей: {count}"
            )
            return

        interval = options["interval"]

        if interval < 1:
            self.stderr.write(
                "Интервал должен быть не меньше 1 секунды."
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Обработчик платежей запущен. "
                "Для остановки нажмите Ctrl+C."
            )
        )

        try:
            while True:
                self.process_queue()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(
                "\nОбработчик платежей остановлен."
            )
