import csv
import pandas as pd
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Product, Order, OrderItem
from .serializers import UserSerializer, ProductSerializer, OrderSerializer
from .permissions import IsAdminUserOrReadOnly, IsAdmin, IsOwnerOrAdmin
from .tasks import send_order_confirmation

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminUserOrReadOnly)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)

    def get_queryset(self):
        if self.action == 'list':
            if self.request.user.role == 'admin':
                return Order.objects.all()
            return Order.objects.filter(user=self.request.user)
        return Order.objects.all()

    def create(self, request, *args, **kwargs):
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"detail": "No items provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                order = Order.objects.create(user=request.user, total_amount=0)
                total_amount = 0
                
                for item_data in items_data:
                    product = Product.objects.select_for_update().get(id=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    
                    if quantity <= 0:
                        raise ValueError("Invalid quantity")
                        
                    if product.stock < quantity:
                        raise ValueError(f"Insufficient stock for product {product.name}")
                        
                    product.stock -= quantity
                    product.save()
                    
                    price = product.price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price
                    )
                    total_amount += price * quantity
                
                order.total_amount = total_amount
                order.save()
                
                # Trigger Celery Task
                send_order_confirmation.delay(order.id, request.user.email)

        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        # Admin shouldn't randomly cancel others' orders from this endpoint unless specified, but let's allow users to cancel their own.
        if request.user.role != 'admin' and order.user != request.user:
            return Response({"detail": "Cannot cancel another customer's order."}, status=status.HTTP_403_FORBIDDEN)
            
        if order.status == 'cancelled':
            return Response({"detail": "Order is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            order.status = 'cancelled'
            order.save()
            
            # Restore stock
            for item in order.items.all():
                product = Product.objects.select_for_update().get(id=item.product_id)
                product.stock += item.quantity
                product.save()
                
        return Response({"detail": "Order cancelled successfully."}, status=status.HTTP_200_OK)

class ExportOrdersView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsAdmin)

    def get(self, request):
        export_type = request.query_params.get('type', 'csv')
        orders = Order.objects.all().values('id', 'user__username', 'status', 'total_amount', 'created_at')
        df = pd.DataFrame.from_records(orders)
        
        if df.empty:
            return Response({"detail": "No orders to export"}, status=status.HTTP_404_NOT_FOUND)
            
        if export_type == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
            df.to_excel(response, index=False)
            return response
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="orders.csv"'
            df.to_csv(response, index=False)
            return response
