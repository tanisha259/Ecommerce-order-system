import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ecommerce.models import User, Product, Order, OrderItem

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    user = User.objects.create_user(username='admin', password='password', role='admin')
    return user

@pytest.fixture
def customer_user():
    user = User.objects.create_user(username='customer', password='password', role='customer')
    return user

@pytest.fixture
def customer_user2():
    user = User.objects.create_user(username='customer2', password='password', role='customer')
    return user

@pytest.fixture
def product1():
    return Product.objects.create(name='Product 1', price=10.00, stock=5)

@pytest.fixture
def product2():
    return Product.objects.create(name='Product 2', price=20.00, stock=10)

@pytest.mark.django_db
class TestOrders:
    
    @patch('ecommerce.views.send_order_confirmation.delay')
    def test_customer_creates_order_multiple_products(self, mock_celery, api_client, customer_user, product1, product2):
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-list')
        data = {
            'items': [
                {'product_id': product1.id, 'quantity': 2},
                {'product_id': product2.id, 'quantity': 1}
            ]
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        mock_celery.assert_called_once()
        
        # Check stock update
        product1.refresh_from_db()
        product2.refresh_from_db()
        assert product1.stock == 3
        assert product2.stock == 9
        
        # Check total amount
        assert Order.objects.count() == 1
        order = Order.objects.first()
        assert order.total_amount == 40.00 # 2*10 + 1*20

    def test_insufficient_stock(self, api_client, customer_user, product1):
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-list')
        data = {
            'items': [{'product_id': product1.id, 'quantity': 10}]
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient stock" in response.data['detail']
        
        # Stock shouldn't change
        product1.refresh_from_db()
        assert product1.stock == 5

    def test_invalid_quantity(self, api_client, customer_user, product1):
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-list')
        data = {
            'items': [{'product_id': product1.id, 'quantity': 0}]
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid quantity" in response.data['detail']

    def test_customer_sees_own_orders(self, api_client, customer_user, customer_user2, product1):
        Order.objects.create(user=customer_user, total_amount=10)
        Order.objects.create(user=customer_user2, total_amount=20)
        
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['user'] == customer_user.id

    def test_admin_sees_all_orders(self, api_client, admin_user, customer_user, customer_user2):
        Order.objects.create(user=customer_user, total_amount=10)
        Order.objects.create(user=customer_user2, total_amount=20)
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('order-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_customer_can_cancel_own_order(self, api_client, customer_user, product1):
        order = Order.objects.create(user=customer_user, total_amount=10, status='pending')
        OrderItem.objects.create(order=order, product=product1, quantity=2, price=10)
        
        # Manually reduce stock like it was done during order creation
        product1.stock -= 2
        product1.save()
        
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-cancel', kwargs={'pk': order.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        order.refresh_from_db()
        assert order.status == 'cancelled'
        
        # Stock restored
        product1.refresh_from_db()
        assert product1.stock == 5

    def test_customer_cannot_cancel_another_customer_order(self, api_client, customer_user, customer_user2):
        order = Order.objects.create(user=customer_user2, total_amount=10, status='pending')
        
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-cancel', kwargs={'pk': order.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_cannot_cancel_already_cancelled_order(self, api_client, customer_user):
        order = Order.objects.create(user=customer_user, total_amount=10, status='cancelled')
        
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-cancel', kwargs={'pk': order.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transaction_rollback_works_correctly(self, api_client, customer_user, product1, product2):
        api_client.force_authenticate(user=customer_user)
        url = reverse('order-list')
        
        # product1 has 5 stock, product2 has 10.
        # This will fail on product2 due to insufficient stock, so product1 stock should rollback.
        data = {
            'items': [
                {'product_id': product1.id, 'quantity': 2},
                {'product_id': product2.id, 'quantity': 15}
            ]
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verify rollback
        product1.refresh_from_db()
        product2.refresh_from_db()
        assert product1.stock == 5
        assert product2.stock == 10
        assert Order.objects.count() == 0
