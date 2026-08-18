from celery import shared_task
import time

@shared_task
def send_order_confirmation(order_id, user_email):
    # Simulate sending email
    time.sleep(2)
    print(f"Order Confirmation for Order ID: {order_id} sent to {user_email}.")
    return True
