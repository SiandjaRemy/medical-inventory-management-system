from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Count, Q, Sum
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.core import serializers
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from rest_framework import serializers

from warehouse_app.models import (
    OrderPartialPayment,
    Warehouse,
    Employee,
    Product,
    Order,
    OrderItem,
    Category,
)

from phonenumber_field.serializerfields import PhoneNumberField
from easyaudit.models import CRUDEvent


from InventoryManagement.utils.crudevents import (
    bulk_create_crudevents,
    bulk_update_crudevents,
    create_crudevent,
    update_crudevent,
)
from InventoryManagement.utils.context_manager import set_current_context

User = get_user_model()


# All simplified serializers
# Will be referenced in other serializers to have more details about the related objects
class SimpleUserModelSerializer(serializers.ModelSerializer):
    is_manager = serializers.SerializerMethodField()
    is_superuser = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_superuser",
            "is_active",
            "is_manager",
        ]

    def get_is_manager(self, user):
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            return True
        return False


class ActivateOrDeactivateUserSerializer(serializers.Serializer):
    pass


class SimpleWarehouseModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "created_at", "modified_at"]

    # def create(self, validated_data):
    #     user = self.context.get("user")
    #     new_warehouse = Warehouse.objects.create(**validated_data)
    #     create_crudevent(user, new_warehouse)
    #     return new_warehouse

    def create(self, validated_data):
        user = self.context["user"]
        try:
            with set_current_context(user):
                with transaction.atomic():
                    new_warehouse = Warehouse.objects.create(**self.validated_data)

                    return new_warehouse

        except Exception as e:
            raise serializers.ValidationError(str(e))


class SimpleEmployeeModelSerializer(serializers.ModelSerializer):
    user = SimpleUserModelSerializer(many=False, read_only=True)
    is_manager = serializers.BooleanField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "phone_number",
            "image",
            "is_manager",
            "created_at",
            "modified_at",
        ]


class SimpleCategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class CategoryModelSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        # fields = ["id", "name", "slug", "parent_category", "subcategories"]

    def create(self, validated_data):
        user = self.context.get("user")
        name = self.validated_data["name"]
        slug = slugify(name)

        self.validated_data["slug"] = slug

        try:
            with set_current_context(user):
                with transaction.atomic():
                    category = Category.objects.create(**self.validated_data)

                    return category

        except Exception as e:
            raise serializers.ValidationError(str(e))

    # def get_fields(self):
    #     fields = super().get_fields()
    #     method = self.context["method"]
    #     if method == "GET":
    #         fields["parent_category"] = SimpleCategoryModelSerializer(read_only=True)
    #     else:
    #         fields["parent_category"] = serializers.PrimaryKeyRelatedField(
    #             queryset=Category.objects.all(), required=False, allow_null=True
    #         )
    #     return fields


class SimpleProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "image",
            "measurement_unit",
            "quantity",
            "unit_price",
            "created_at",
            "is_available",
            "modified_at",
        ]


class SimpleOrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductModelSerializer(many=False)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "buying_price", "quantity", "created_at"]


class SimpleOrderModelSerializer(serializers.ModelSerializer):
    warehouse = serializers.StringRelatedField()
    initiator = SimpleUserModelSerializer(many=False)

    class Meta:
        model = Order
        fields = [
            "id",
            "warehouse",
            "initiator",
            "tracking_id",
            "created_at",
            "modified_at",
        ]


class SimpleOrderModelSerializer2(serializers.ModelSerializer):
    initiator = SimpleUserModelSerializer(many=False)

    class Meta:
        model = Order
        fields = ["id", "initiator", "tracking_id", "created_at", "modified_at"]


class SimpleOrderPartialPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPartialPayment
        fields = ["id", "amount", "created_at"]


class CreateOrderPartialPaymentSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(required=True, decimal_places=2, max_digits=15)

    # Maybe add the tracking id when filtering
    class Meta:
        model = OrderPartialPayment
        fields = ["id", "amount", "created_at"]

    def create(self, validated_data):
        amount = validated_data["amount"]
        user = self.context["user"]
        order_id = self.context["order_id"]
        # print(f"Context: {self.context}")

        order = (
            Order.objects.only("total_price", "order_status", "partial_payments")
            .prefetch_related("partial_payments")
            .filter(id=order_id, order_status=Order.Status.PENDING)
            .first()
        )
        if order is not None:

            all_partial_payments = order.partial_payments.all()
            total_amount_paid = sum(payment.amount for payment in all_partial_payments)
            remainder = order.total_price - total_amount_paid

            additional_context = {
                "skip_signal": False,
            }
            if amount <= remainder:
                with set_current_context(user, **additional_context):
                    with transaction.atomic():
                        payment_instance = OrderPartialPayment.objects.create(
                            order=order, amount=amount
                        )
                        remainder -= amount
                        if remainder == 0:
                            order.order_status = Order.Status.COMPLETED
                            order.save()
                        return payment_instance
            else:
                raise serializers.ValidationError(
                    {
                        "error": "The amount entered is more than the amount left to pay for this order"
                    }
                )
        else:
            raise serializers.ValidationError({"not_found": f"Order with id '{order_id}' was not found"})



class CrudEventModelSerializer(serializers.ModelSerializer):
    user = SimpleUserModelSerializer(many=False)
    event_type = serializers.SerializerMethodField()
    datetime = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = CRUDEvent
        fields = "__all__"

    def get_event_type(self, obj):
        return obj.get_event_type_display()  # Get human-readable name

    def get_datetime(self, obj):
        datetime = obj.datetime.strftime("%B %d, %Y - %H:%M:%S")
        return datetime

    def get_content_type(self, obj):
        return str(
            obj.content_type
        )  # Get the string representation of the ContentType object


class CrudEventModelSerializer2(serializers.ModelSerializer):
    event_type = serializers.SerializerMethodField()
    datetime = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = CRUDEvent
        fields = "__all__"

    def get_event_type(self, obj):
        return obj.get_event_type_display()  # Get human-readable name

    def get_datetime(self, obj):
        datetime = obj.datetime.strftime("%B %d, %Y - %H:%M:%S")
        return datetime

    def get_content_type(self, obj):
        return str(
            obj.content_type
        )  # Get the string representation of the ContentType object


class UserWithLogsSerializer(serializers.ModelSerializer):
    crudevent_set = CrudEventModelSerializer2(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "crudevent_set"]


# Main serializers
# Most will be used during to display data for get requests


# Employee related serializers
class EmployeeModelSerializer(serializers.ModelSerializer):
    warehouse = SimpleWarehouseModelSerializer(many=False, read_only=True)
    user = SimpleUserModelSerializer(many=False, read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "warehouse",
            "phone_number",
            "id_number",
            "image",
            "is_manager",
            "created_at",
        ]


class CreateEmployeeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    phone_number = PhoneNumberField()
    image = serializers.ImageField(required=False)
    is_manager = serializers.BooleanField()
    id_number = serializers.CharField()

    def get_fields(self):
        fields = super().get_fields()
        user = self.context.get("user")  # Use .get() to avoid KeyError
        if user and user.is_superuser:  # Check if user exists and is a superuser
            fields["warehouse_id"] = serializers.UUIDField(required=True)
            fields["is_manager"] = serializers.BooleanField()
        else:
            if "warehouse_id" in fields:  # remove the field if it exists
                del fields["warehouse_id"]
            if "is_manager" in fields:
                del fields["is_manager"]
        return fields

    def save(self, **kwargs):
        email = self.validated_data.get("email")
        first_name = self.validated_data.get("first_name")
        last_name = self.validated_data.get("last_name")
        phone_number = self.validated_data.get("phone_number")
        image = self.validated_data.get("image")
        id_number = self.validated_data.get("id_number")

        full_name = f"{first_name} {last_name}"
        lower_email = email.lower()

        # Check if user is admin and get the warehouse id accordingly
        # Also get is_manager value and overwrite the current one
        user = self.context["user"]
        if user.is_superuser:
            warehouse_id = self.validated_data.get("warehouse_id")
            is_manager = self.validated_data.get("is_manager")
            if not warehouse_id:
                raise serializers.ValidationError(
                    {"message": "Admin must pass warehouse id to create orders"}
                )
        else:
            warehouse_id = self.context["warehouse_id"]
            is_manager = False

        # Set user role based on
        if is_manager:
            role = User.ROLES.EMPLOYEE_MANAGER
        else:
            role = User.ROLES.EMPLOYEE

        additional_context = {
            "skip_signal": False,
            "email": lower_email,
            "username": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
        }

        try:
            with set_current_context(user, **additional_context):
                with transaction.atomic():
                    new_employee = Employee.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number,
                        image=image,
                        is_manager=is_manager,
                        id_number=id_number,
                        warehouse_id=warehouse_id,
                    )

                    return new_employee

        except Exception as e:
            print(f"Employee error: {e}")
            raise serializers.ValidationError(str(e))


class UpdateEmployeeSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    phone_number = PhoneNumberField(required=False)
    image = serializers.ImageField(required=False)
    id_number = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        user = self.context["user"]
        sender = Employee.objects.select_related("user").filter(id=instance.id).first()
        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        new_instance = instance
        with set_current_context(user):
            with transaction.atomic():
                update_crudevent(old_obj=sender, obj=new_instance)

        return instance


# Products related serializers
class CreateProductModelSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.ChoiceField(choices=Product.MeasurementUnit)
    # warehouse_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "description",
            "image",
            "measurement_unit",
            "quantity",
            "unit_price",
            "created_at",
            "modified_at",
            "warehouse_id",
        ]

    # def get_fields(self):
    #     fields = super().get_fields()
    #     user = self.context["user"]
    #     if user.is_superuser:
    #         fields["warehouse_id"] = serializers.UUIDField(required=True)
    #     return fields

    def get_fields(self):
        fields = super().get_fields()
        user = self.context.get("user")  # Use .get() to avoid KeyError
        if user and user.is_superuser:  # Check if user exists and is a superuser
            fields["warehouse_id"] = serializers.UUIDField(required=True)
        elif "warehouse_id" in fields:  # remove the field if it exists
            del fields["warehouse_id"]
        return fields

    def create(self, validated_data):
        user = self.context["user"]
        if user.is_superuser:
            warehouse_id = self.validated_data.pop("warehouse_id")
            if not warehouse_id:
                raise serializers.ValidationError(
                    {"message": "Admin must pass warehouse id to create orders"}
                )
        else:
            warehouse_id = self.context["warehouse_id"]

        self.validated_data["warehouse_id"] = warehouse_id

        try:
            with set_current_context(user):
                with transaction.atomic():
                    new_product = Product.objects.create(**self.validated_data)

                    return new_product
        except Exception as e:
            raise serializers.ValidationError(str(e))


class UpdateProductModelSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.ChoiceField(choices=Product.MeasurementUnit, required=False)
    name = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "description",
            "image",
            "measurement_unit",
            "quantity",
            "unit_price",
            "created_at",
            "modified_at",
        ]

    def update(self, instance, validated_data):
        # Get the user who made the update
        # print(f"validated_data: {validated_data}")
        # print(f"measurement_unit: {validated_data["measurement_unit"]}")
        user = self.context["user"]
        # Store the model instance before it is updated
        sender = (
            Product.objects.select_related("warehouse", "category")
            .filter(id=instance.id)
            .first()
        )

        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        new_instance = instance
        with set_current_context(user):
            with transaction.atomic():
                update_crudevent(old_obj=sender, obj=new_instance)

        return instance


class WarehousesListForDashboardSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    location = serializers.CharField()
    
class EmployeesCountSerializer(serializers.Serializer):
    all_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    inactive_employees = serializers.IntegerField()
    number_of_managers = serializers.IntegerField()
    
class ProductsCountSerializer(serializers.Serializer):
    all_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    expired_products = serializers.IntegerField(required=False)


class MonthlySalesSerializer(serializers.Serializer):
    month = serializers.CharField()
    number_of_completed_orders = serializers.IntegerField()
    number_of_pending_orders = serializers.IntegerField()
    month_total_sales = serializers.IntegerField()


class DashboardDataSerializer(serializers.Serializer):
    warehouses_data = WarehousesListForDashboardSerializer(many=True, required=False)
    employees_data = EmployeesCountSerializer(many=False)
    product_data = ProductsCountSerializer(many=False)
    annual_sales = MonthlySalesSerializer(many=True)
    


class ProductModelSerializer(serializers.ModelSerializer):
    warehouse = SimpleWarehouseModelSerializer(many=False)
    category = SimpleCategoryModelSerializer(many=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "image",
            "category",
            "description",
            "warehouse",
            "measurement_unit",
            "quantity",
            "unit_price",
            "is_available",
            "created_at",
            "modified_at",
        ]


# Order and order items related serializers


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderItemForCreateOrderSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.IntegerField(validators=[MinValueValidator(1)])


class CreateOrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemForCreateOrderSerializer(many=True, write_only=True)
    order_status = serializers.CharField(read_only=True)
    initial_deposit = serializers.DecimalField(default=0.00, write_only=True, decimal_places=2, max_digits=15)
    tracking_id = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_phone_number",
            "tracking_id",
            "order_status",
            "order_items",
            "initial_deposit",
            "warehouse_id",
        ]

    def get_fields(self):
        fields = super().get_fields()
        user = self.context.get("user")  # Use .get() to avoid KeyError
        if user and user.is_superuser:  # Check if user exists and is a superuser
            fields["warehouse_id"] = serializers.UUIDField(required=True)
        elif "warehouse_id" in fields:  # remove the field if it exists
            del fields["warehouse_id"]
        return fields

    def create(self, validated_data):
        customer = self.validated_data.get("customer")
        customer_phone_number = self.validated_data.get("customer_phone_number")
        order_items = self.validated_data.get("order_items")

        initial_deposit = self.validated_data.pop("initial_deposit")

        user = self.context["user"]
        if user.is_superuser:
            warehouse_id = self.validated_data.get("warehouse_id")
            if not warehouse_id:
                raise serializers.ValidationError(
                    {"message": "Admin must pass warehouse id to create orders"}
                )
        else:
            warehouse_id = self.context["warehouse_id"]

        # Fetch products with quantities in one query
        product_query = Product.objects.filter(
            id__in=[item["product"] for item in order_items], warehouse_id=warehouse_id
        )

        if len(product_query) != len(order_items):
            raise serializers.ValidationError(
                {"message": "All selected products must belong to the same warehouse"}
            )

        # Create a dictionary to map product IDs to their prices and quantities
        product_price_map = {
            product.id: (product.unit_price, product.quantity)
            for product in product_query
        }

        # Calculate total price and prepare to update product quantities
        order_total_price = 0
        for item in order_items:
            product_id = item["product"]
            quantity = item["quantity"]

            price, available_quantity = product_price_map[product_id]
            if available_quantity < quantity:
                raise serializers.ValidationError(
                    {
                        "message": f"Insufficient stock for product ID {product_id}. Available: {available_quantity}, Requested: {quantity}"
                    }
                )
            order_total_price += price * quantity

        # # Complexe approach
        # order_total_price = sum(
        #     product_price_map[product_id][0] * quantity
        #     for item in order_items
        #     for product_id, quantity in [(item['product'], item['quantity'])]
        # )

        # Change symbole to prevent order creation when testing
        if initial_deposit > order_total_price:
            # if initial_deposit:
            raise serializers.ValidationError(
                {
                    "message": "The initial deposit cannot be more than the order total cost"
                }
            )

        # Pass this argument to prevent signal from creating other curdevents
        additional_context = {
            "skip_signal": True,
        }

        with set_current_context(user, **additional_context):
            with transaction.atomic():
                events = []
                order_status = (
                    Order.Status.COMPLETED
                    if order_total_price == initial_deposit
                    else Order.Status.PENDING
                )
                print(f"order_status: {order_status}")
                # Create the order
                order = Order.objects.create(
                    warehouse_id=warehouse_id,
                    customer=customer,
                    customer_phone_number=customer_phone_number,
                    initiator=user,
                    total_price=order_total_price,
                    order_status=order_status,
                )
                events.append(order)

                if initial_deposit > 0:
                    initial_partial_payment = OrderPartialPayment.objects.create(
                        order=order, amount=initial_deposit
                    )
                    events.append(initial_partial_payment)

                # Logic to manually create a crud events in bulk
                bulk_create_crudevents(objects=events)

                # Create order items in bulk for all products passed
                OrderItem.objects.bulk_create(
                    [
                        OrderItem(
                            order=order,
                            product_id=item["product"],
                            buying_price=product_price_map[product_id][0],
                            quantity=item["quantity"],
                        )
                        for item in order_items
                        for product_id, _ in [(item["product"], item["quantity"])]
                    ]
                )

                products_to_update = []
                for item in order_items:
                    product_id = item["product"]
                    quantity = item["quantity"]

                    if product_id in product_price_map:
                        # Reduce the quantity of the ordered products
                        new_quantity = F("quantity") - quantity
                        products_to_update.append(
                            Product(id=product_id, quantity=new_quantity)
                        )

                # Bulk update products
                Product.objects.bulk_update(products_to_update, ["quantity"])

        return order


class OrderModelSerializer(serializers.ModelSerializer):
    order_items = SimpleOrderItemSerializer(many=True)
    warehouse = SimpleWarehouseModelSerializer(many=False, read_only=True)
    initiator = SimpleUserModelSerializer(many=False, read_only=True)
    partial_payments = SimpleOrderPartialPaymentSerializer(many=True)
    remainder = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_phone_number",
            "order_status",
            "tracking_id",
            "order_items",
            "warehouse",
            "initiator",
            "partial_payments",
            "total_price",
            "remainder",
            "created_at",
            "modified_at",
        ]

    def get_remainder(self, obj):
        all_partial_payments = obj.partial_payments.all()
        total_amount_paid = sum(payment.amount for payment in all_partial_payments)
        remainder = obj.total_price - total_amount_paid
        return remainder


# Warehouse related serializers
class FullWarehouseModelSerializer(serializers.ModelSerializer):
    employees = SimpleEmployeeModelSerializer(many=True)
    products = SimpleProductModelSerializer(many=True)
    orders = SimpleOrderModelSerializer2(many=True)

    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "employees", "products", "orders"]


class WarehouseCountModelSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            'id',
            'name',
            'location',
            'employee_count',
            'product_count',
            'order_count'
        ]
        
    def get_employee_count(self, obj):
        count = obj.employees_count
        return count
    
    def get_product_count(self, obj):
        count = obj.products_count
        return count
    
    def get_order_count(self, obj):
        count = obj.orders_count
        return count