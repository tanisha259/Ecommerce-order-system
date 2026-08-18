import pandas as pd
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Product, Order
from .serializers import UserSerializer, ProductSerializer, OrderSerializer
from .permissions import IsAdminUserOrReadOnly, IsAdmin, IsOwnerOrAdmin
from .tasks import send_order_confirmation
from .services import (
    create_order,
    cancel_order,
    InsufficientStockError,
    InvalidQuantityError,
    OrderAlreadyCancelledError,
)


class RegisterView(generics.CreateAPIView):
    """Handles new user registration and returns JWT tokens."""
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
    """
    Admin: Full CRUD on products.
    Customer: Read-only. Product listing is cached for 15 minutes.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminUserOrReadOnly)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Admin: Can see all orders.
    Customer: Can only see and manage their own orders.
    """
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)

    def get_queryset(self):
        if self.action == 'list':
            if self.request.user.role == 'admin':
                return Order.objects.all()
            return Order.objects.filter(user=self.request.user)
        return Order.objects.all()

    def create(self, request, *args, **kwargs):
        """Delegates order creation to the service layer."""
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"detail": "No items provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = create_order(user=request.user, items_data=items_data)
            send_order_confirmation.delay(order.id, request.user.email)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except InvalidQuantityError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientStockError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Delegates order cancellation to the service layer."""
        order = self.get_object()

        if request.user.role != 'admin' and order.user != request.user:
            return Response(
                {"detail": "You do not have permission to cancel this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            cancel_order(order)
        except OrderAlreadyCancelledError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Order cancelled successfully."}, status=status.HTTP_200_OK)


class ExportOrdersView(APIView):
    """Admin-only endpoint to export all orders as CSV or Excel."""
    permission_classes = (permissions.IsAuthenticated, IsAdmin)

    def get(self, request):
        export_type = request.query_params.get('type', 'csv')
        orders = Order.objects.all().values('id', 'user__username', 'status', 'total_amount', 'created_at')
        df = pd.DataFrame.from_records(orders)

        if df.empty:
            return Response({"detail": "No orders to export."}, status=status.HTTP_404_NOT_FOUND)

        if export_type == 'excel':
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
            df.to_excel(response, index=False)
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="orders.csv"'
            df.to_csv(response, index=False)

        return response
