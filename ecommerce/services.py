"""
services.py - Business logic layer, separated from views.
All core order operations live here to keep views thin and clean.
"""

from django.db import transaction
from .models import Product, Order, OrderItem


class InsufficientStockError(Exception):
    pass


class InvalidQuantityError(Exception):
    pass


class OrderAlreadyCancelledError(Exception):
    pass


def create_order(user, items_data):
    """
    Creates an order transactionally.
    - Validates quantity for each item.
    - Checks stock availability.
    - Deducts stock atomically.
    - Returns the created Order instance.

    Raises:
        InvalidQuantityError: If any item has quantity <= 0.
        InsufficientStockError: If any product doesn't have enough stock.
        Product.DoesNotExist: If a product ID doesn't exist.
    """
    with transaction.atomic():
        order = Order.objects.create(user=user, total_amount=0)
        total_amount = 0

        for item_data in items_data:
            product = Product.objects.select_for_update().get(id=item_data['product_id'])
            quantity = int(item_data['quantity'])

            if quantity <= 0:
                raise InvalidQuantityError(f"Quantity must be greater than zero for product '{product.name}'.")

            if product.stock < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for product '{product.name}'. "
                    f"Available: {product.stock}, Requested: {quantity}."
                )

            product.stock -= quantity
            product.save()

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
            )
            total_amount += product.price * quantity

        order.total_amount = total_amount
        order.save()

    return order


def cancel_order(order):
    """
    Cancels an existing order and restores product stock atomically.

    Raises:
        OrderAlreadyCancelledError: If the order is already cancelled.
    """
    if order.status == 'cancelled':
        raise OrderAlreadyCancelledError("This order has already been cancelled.")

    with transaction.atomic():
        order.status = 'cancelled'
        order.save()

        for item in order.items.select_related('product').all():
            product = Product.objects.select_for_update().get(id=item.product_id)
            product.stock += item.quantity
            product.save()
