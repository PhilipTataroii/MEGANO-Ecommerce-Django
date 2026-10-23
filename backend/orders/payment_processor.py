
"""Обработка платежей учебного интернет-магазина."""

from django.db import transaction

from .models import Order
from .payment_service import process_payment


def process_order_payment(order_id):
    """Обрабатывает ожидающий платёж и сохраняет результат."""

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(
            pk=order_id,
        ).first()

        if order is None:
            return False

        # Обрабатываем только платежи в очереди.
        if order.status != "pending":
            return False

        try:
            success, error = process_payment(order.payment_number)
        except ValueError as exc:
            success = False
            error = str(exc)

        if success:
            order.status = "paid"
            order.payment_error = ""
        else:
            order.status = "failed"
            order.payment_error = error

        order.save(update_fields=["status", "payment_error"])

        return success
