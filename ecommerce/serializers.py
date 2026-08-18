from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Product, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')
        
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'customer')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_id', 'product', 'quantity', 'price')
        read_only_fields = ('price',)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'status', 'total_amount', 'created_at', 'updated_at', 'items')
        read_only_fields = ('user', 'status', 'total_amount')
