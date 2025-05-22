from django_filters.rest_framework import FilterSet, DateFilter, ModelChoiceFilter

from warehouse_app.models import Order, Product, Warehouse, Employee

from easyaudit.models import CRUDEvent

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from datetime import datetime

User = get_user_model()


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            "category_id": ["exact"],
            "warehouse_id": ["exact"],
            "unit_price": ["gt", "lt"],
            "quantity": ["gt", "lt"],
        }
                
class EmployeeFilter(FilterSet):
    class Meta:
        model = Employee
        fields = {
            "warehouse_id": ["exact"],
        }
                

class OrderFilter(FilterSet):
    min_created_at = DateFilter(field_name='created_at', lookup_expr='gte', label='Created After')
    max_created_at = DateFilter(field_name='created_at', lookup_expr='lte', label='Created Before')

    class Meta:
        model = Order
        fields = ['min_created_at', 'max_created_at', 'order_status', 'warehouse', 'initiator', 'tracking_id']
        



class CRUDEventFilter(FilterSet):
    min_datetime = DateFilter(field_name='datetime', lookup_expr='gte', label='Performed After')
    max_datetime = DateFilter(field_name='datetime', lookup_expr='lte', label='Performed Before')

    class Meta:
        model = CRUDEvent
        fields = ['min_datetime', 'max_datetime', 'user', 'user__warehouse_id', 'event_type']
        
    