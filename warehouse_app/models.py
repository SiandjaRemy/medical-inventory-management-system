from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

from phonenumber_field.modelfields import PhoneNumberField

from cloudinary_storage.storage import MediaCloudinaryStorage
import uuid
import random
import string
from decimal import Decimal


# Create your models here.

User = get_user_model()


class Warehouse(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        warehouse = f"{self.name} - {self.location}"
        return warehouse


class Employee(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    warehouse = models.ForeignKey(
        Warehouse, related_name="employees", on_delete=models.CASCADE
    )
    user = models.OneToOneField(User, related_name="employee", on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = PhoneNumberField()
    id_number = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(null=True, blank=True, upload_to="employee_images/", storage=MediaCloudinaryStorage)
    is_manager = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.role}"
    
    def block_user(self):
        if self.user.is_active:
            self.user.is_active = False
            self.user.save()
            return True
        return False
        
    def unblock_user(self):
        if not self.user.is_active:
            self.user.is_active = True
            self.user.save()
            return True
        return False

    def set_manager(self):
        if self.user.role != User.ROLES.EMPLOYEE_MANAGER or not self.is_manager: #check both at the same time
            self.user.role = User.ROLES.EMPLOYEE_MANAGER
            self.is_manager = True
            self.user.save()
            self.save()
            return True
        return False

    def set_employee(self):
        if self.user.role != User.ROLES.EMPLOYEE or self.is_manager: #check both at the same time
            self.user.role = User.ROLES.EMPLOYEE
            self.is_manager = False
            self.user.save()
            self.save()
            return True
        return False


    class Meta:
        ordering = ["-created_at"]



class Category(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    name = models.CharField(max_length=30)
    slug = models.CharField(max_length=30, unique=True, blank=True)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="subcategories",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Categories"
    
    


class Product(models.Model):
    class MeasurementUnit(models.TextChoices):
        MILLIMETER = "mm", "Millimeter"
        CENTIMETER = "cm", "Centimeter"
        METER = "m", "Meter"
        INCH = "in", "Inch"
        FOOT = "ft", "Foot"
        KILOGRAM = "kg", "Kilogram"
        MILLIGRAM = "mg", "Milligram"
        GRAM = "g", "Gram"
        POUND = "lb", "Pound"
        OUNCE = "oz", "Ounce"
        LITER = "l", "Liter"
        MILLILITER = "ml", "Milliliter"
        CUBIC_METER = "m³", "Cubic Meter"
        CUBIC_CENTIMETER = "cm³", "Cubic Centimeter"
        CUBIC_INCH = "in³", "Cubic Inch"
        CUBIC_FOOT = "ft³", "Cubic Foot"
        SQUARE_METER = "m²", "Square Meter"
        SQUARE_CENTIMETER = "cm²", "Square Centimeter"
        SQUARE_INCH = "in²", "Square Inch"
        SQUARE_FOOT = "ft²", "Square Foot"
        HECTARE = "ha", "Hectare"
        ACRE = "acre", "Acre"
        TEMPERATURE_CELSIUS = "°C", "Temperature in Celsius"
        TEMPERATURE_FAHRENHEIT = "°F", "Temperature in Fahrenheit"
        VOLUME_GALLONS = "gal", "Volume in Gallons"
        VOLUME_QUARTS = "qt", "Volume in Quarts"
        VOLUME_PINTS = "pt", "Volume in Pints"
        COUNT = "count", "Count"
        SET = "set", "Set"
        BOX = "box", "Box"

    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    warehouse = models.ForeignKey(
        Warehouse, related_name="products", on_delete=models.CASCADE
    )
    # Category should not be null nor blank so remove later
    category = models.ForeignKey(
        Category,
        related_name="products",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="product_images/", storage=MediaCloudinaryStorage)
    measurement_unit = models.CharField(max_length=50, choices=MeasurementUnit.choices)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(0),
        ],
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    expiratory_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} - {self.name} - (measured in {self.get_measurement_unit_display()}) for {self.warehouse}"

    class Meta:
        ordering = ["-created_at"]


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REFUNDED = "refunded", "Refunded"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    warehouse = models.ForeignKey(
        Warehouse, related_name="orders", on_delete=models.CASCADE
    )
    # Customer should not be null nor blank so remove later
    customer = models.CharField(max_length=255)
    customer_phone_number = PhoneNumberField(null=True)
    initiator = models.ForeignKey(
        User, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True
    )  # The employee who created the order
    order_status = models.CharField(
        max_length=50, choices=Status.choices, default=Status.PENDING
    )
    tracking_id = models.CharField(default="", max_length=50, unique=True)
    total_price = models.DecimalField(
        max_digits=15,
        default=0,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ["-created_at"]
        
    def generate_tracking_id(self):
        while True:
            # Generate a random number in the range 100000 to 999999
            random_number = random.randint(100000, 999999)
            # Get the first letter of the customer's name (if available)
            first_letter = self.customer[0].upper() if self.customer else 'X'
            # Generate two random uppercase letters
            random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            # Construct the tracking ID
            tracking_id = f"TM-{random_number}{first_letter}{random_letters}"
            # Check if the generated tracking ID is unique
            if not Order.objects.filter(tracking_id=tracking_id).exists():
                return tracking_id

    def save(self, *args, **kwargs):
        # Generate tracking_id only if it is not set
        if not self.tracking_id:
            self.tracking_id = self.generate_tracking_id()
        # Round the total_price to 2 decimal places before saving
        self.total_price = Decimal(self.total_price).quantize(Decimal('0.00'))        
        super().save(*args, **kwargs)
        


class OrderPartialPayment(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="partial_payments"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    buying_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.quantity}"

    class Meta:
        ordering = ["-created_at"]
