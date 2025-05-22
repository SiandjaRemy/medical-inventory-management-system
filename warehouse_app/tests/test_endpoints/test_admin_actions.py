from os import name
from django.contrib.auth import get_user_model

from warehouse_app.models import Category, Employee, Product, Warehouse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

import logging
import json
import random

from InventoryManagement.utils.context_manager import set_current_context

logger = logging.getLogger(__name__)
User = get_user_model()

warehouse_endpoint = "http://localhost:8000/warehouses/"
employee_endpoint = "http://localhost:8000/employees/"
userlogs_endpoint = "http://localhost:8000/userlogs/"
products_endpoint = "http://localhost:8000/products/"
category_endpoint = "http://localhost:8000/categories/"
orders_endpoint = "http://localhost:8000/orders/"


# ----------------------------------------------------------------------------------
#           Testing actions that can be performed on warehouse as admin
# ----------------------------------------------------------------------------------


class AdminActionsOnWarehouseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email="myadmin@gmail.com", username="myadmin", password="987654321@"
        )
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")

        data = {"name": "Site 3", "location": "London"}
        data_2 = {"name": "Site 5", "location": "London"}

        with set_current_context(self.admin_user):
            self.new_warehouse = Warehouse.objects.create(**data)
            self.new_warehouse_2 = Warehouse.objects.create(**data_2)

    def test_create_warehouse(self):
        data = {"name": "Site 4", "location": "Paris"}

        response = self.client.post(warehouse_endpoint, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        warehouse = Warehouse.objects.get(name=data["name"])
        self.assertEqual(warehouse.name, data["name"])

    def test_list_warehouses(self):
        response = self.client.get(warehouse_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # with open('response1.txt', 'w') as f:
        #     f.write(f"Results: {response.data}\n")  # Write the response data as JSON
        # The 2 existing warehouses can be ssen in the setup
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_warehouse(self):
        response = self.client.get(f"{warehouse_endpoint}{self.new_warehouse.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Write response data to a file
        # with open('response.txt', 'w') as f:
        #     f.write(f"Results: {response.data}\n")  # Write the response data as JSON

        self.assertEqual(response.data["name"], "Site 3")

    def test_update_warehouse(self):
        data = {"name": "Site 5 updated", "location": "Paris"}
        response = self.client.put(
            f"{warehouse_endpoint}{self.new_warehouse_2.id}/", data=data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Site 5 updated")


# ----------------------------------------------------------------------------------
#           Testing actions that can be performed on Employees as admin
# ----------------------------------------------------------------------------------


class AdminActionsOnEmployeesTestCase(APITestCase):
    def setUp(self):
        """
        The setup for this test will require the creation of a warehouse

        """
        self.client = APIClient()

        # Set admin
        self.admin_user = User.objects.create_superuser(
            email="myadmin@gmail.com", username="myadmin", password="987654321@"
        )
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")

        # Create data for warehouses
        data = {"name": "Site 1", "location": "London"}
        data_2 = {"name": "Site 2", "location": "London"}

        with set_current_context(self.admin_user):
            self.new_warehouse = Warehouse.objects.create(**data)
            self.new_warehouse_2 = Warehouse.objects.create(**data_2)

        # Create a manager linked to a warehouse
        employee_manager_data = {
            "email": "mymanager@gmail.com",
            "first_name": "my",
            "last_name": "manager",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "5877956612",
            "is_manager": True,
            "warehouse_id": self.new_warehouse.id,
        }
        employee_data = {
            "email": "myemployee@gmail.com",
            "first_name": "my",
            "last_name": "employee",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "5877956612",
            "is_manager": False,
            "warehouse_id": self.new_warehouse.id,
        }
        self.client.post(employee_endpoint, data=employee_manager_data)
        self.client.post(employee_endpoint, data=employee_data)

    def test_list_employees(self):
        response = self.client.get(employee_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_and_list_employees(self):
        employee_data = {
            "email": "mymanager2@gmail.com",
            "first_name": "my",
            "last_name": "manager2",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "58779566177",
            "is_manager": True,
            "warehouse_id": self.new_warehouse_2.id,
        }
        post_response = self.client.post(employee_endpoint, data=employee_data)
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        get_response = self.client.get(employee_endpoint)

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["count"], 3)

    def test_create_and_list_filtered_employees(self):
        employee_data = {
            "email": "mymanager2@gmail.com",
            "first_name": "my",
            "last_name": "manager2",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "58779566177",
            "is_manager": True,
            "warehouse_id": self.new_warehouse_2.id,
        }
        post_response = self.client.post(employee_endpoint, data=employee_data)
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        get_response_1 = self.client.get(
            f"{employee_endpoint}?warehouse_id={self.new_warehouse_2.id}"
        )
        get_response_2 = self.client.get(
            f"{employee_endpoint}?warehouse_id={self.new_warehouse.id}"
        )

        # Check nummber of uses in warehouse 2
        self.assertEqual(get_response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response_1.data["count"], 1)

        # Check nummber of uses in warehouse 1
        self.assertEqual(get_response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response_2.data["count"], 2)

    # Modify employee and user relation and add signals suct that a change on user will be reflected of employee
    # When done, create employee manualy in setup and update in in a test


# ----------------------------------------------------------------------------------
#           Testing actions that can be performed on products as admin
# ----------------------------------------------------------------------------------


def get_random_measurement_unit():
    return random.choice([unit[0] for unit in Product.MeasurementUnit.choices])


class AdminActionsOnProductsTestCase(APITestCase):
    def setUp(self):
        """
        The setup for this test will require the creation of warehouses

        """
        self.client = APIClient()

        # Set admin
        self.admin_user = User.objects.create_superuser(
            email="myadmin@gmail.com", username="myadmin", password="987654321@"
        )
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")

        # Create data for warehouses
        warehouse_data = {"name": "Site 1", "location": "London"}
        warehouse_data_2 = {"name": "Site 2", "location": "London"}

        # Create data for category
        category_data = {
            "name": "Category 1",
        }

        with set_current_context(self.admin_user):
            self.new_warehouse = Warehouse.objects.create(**warehouse_data)
            self.new_warehouse_2 = Warehouse.objects.create(**warehouse_data_2)

            self.new_category = Category.objects.create(**category_data)

            # Create products linked to a warehouses
            product_1 = {
                "name": "Product A",
                "category": self.new_category,
                "description": "A simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.new_warehouse.id,
            }
            product_2 = {
                "name": "Product B",
                "category": self.new_category,
                "description": "Another simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.new_warehouse_2.id,
            }

            self.product_1 = Product.objects.create(**product_1)
            self.product_2 = Product.objects.create(**product_2)

    def test_list_products(self):
        response = self.client.get(products_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_and_list_products(self):
        product = {
            "name": "Product C",
            "category": self.new_category.id,
            "description": "Another simple product",
            "image": "",
            "measurement_unit": get_random_measurement_unit(),
            "quantity": random.randint(100, 2000),
            "unit_price": random.randint(1000, 50000),
            "warehouse_id": self.new_warehouse_2.id,
        }
        post_response = self.client.post(products_endpoint, data=product)
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        get_response = self.client.get(products_endpoint)

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["count"], 3)

    def test_list_filtered_products(self):
        get_response_1 = self.client.get(
            f"{products_endpoint}?warehouse_id={self.new_warehouse_2.id}"
        )
        get_response_2 = self.client.get(
            f"{products_endpoint}?warehouse_id={self.new_warehouse.id}"
        )

        # Check nummber of uses in products 2
        self.assertEqual(get_response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response_1.data["count"], 1)

        # Check nummber of uses in products 1
        self.assertEqual(get_response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response_2.data["count"], 1)

    def test_update_products(self):
        product = {
            "name": "Product A+",
            "category": self.new_category.id,
            "description": "Another simple product",
            "image": "",
            "measurement_unit": get_random_measurement_unit(),
            "quantity": random.randint(100, 2000),
            "unit_price": random.randint(1000, 50000),
            "warehouse_id": self.new_warehouse.id,
        }

        response = self.client.patch(
            f"{products_endpoint}{self.product_1.id}/", data=product
        )
        with open("response1.txt", "w") as f:
            f.write(f"Results 1: {response.data}\n")  # Write the response data as JSON

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], product["name"])


# ----------------------------------------------------------------------------------
#           Testing actions that can be performed on logs as admin
# ----------------------------------------------------------------------------------


# Update the creation of crud event and send them to signals to test them in a better way
class AdminActionsOnUserLogsTestCase(APITestCase):
    def setUp(self):
        """
        The setup for this test will require the creation of some instances via their endpoints

        """
        self.client = APIClient()

        # Set admin
        self.admin_user = User.objects.create_superuser(
            email="myadmin@gmail.com", username="myadmin", password="987654321@"
        )
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")

        # Create data for warehouses
        warehouse_data = {"name": "Site 1", "location": "London"}
        warehouse_data_2 = {"name": "Site 2", "location": "London"}

        self.client.post(warehouse_endpoint, data=warehouse_data)
        self.client.post(warehouse_endpoint, data=warehouse_data_2)

        # Create data for category
        category_data = {
            "name": "Category 1",
        }
        self.client.post(category_endpoint, data=category_data)
        # Create products linked to a warehouses

    def test_list_userlogs(self):
        response = self.client.get(userlogs_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)


# ----------------------------------------------------------------------------------
#           Testing actions that can be performed orders as admin
# ----------------------------------------------------------------------------------


class AdminActionsOnOrdersTestCase(APITestCase):
    def setUp(self):
        """
        The setup for this test will require the creation of warehouses and products

        """
        self.client = APIClient()

        # Set admin
        self.admin_user = User.objects.create_superuser(
            email="myadmin@gmail.com", username="myadmin", password="987654321@"
        )
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")

        # Create data for warehouses
        warehouse_data = {"name": "Site 1", "location": "London"}
        warehouse_data_2 = {"name": "Site 2", "location": "London"}

        # Create data for category
        category_data = {
            "name": "Category 1",
        }

        with set_current_context(self.admin_user):
            self.new_warehouse = Warehouse.objects.create(**warehouse_data)
            self.new_warehouse_2 = Warehouse.objects.create(**warehouse_data_2)

            self.new_category = Category.objects.create(**category_data)

            # Create products linked to a warehouses
            product_1 = {
                "name": "Product A",
                "category": self.new_category,
                "description": "A simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.new_warehouse.id,
            }
            product_2 = {
                "name": "Product B",
                "category": self.new_category,
                "description": "Another simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.new_warehouse_2.id,
            }
            product_3 = {
                "name": "Product C",
                "category": self.new_category,
                "description": "Another simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.new_warehouse_2.id,
            }

            # This is done because signals rent trigered during bulk create and so the crudevent wont be created
            self.product_1 = Product.objects.create(**product_1)
            self.product_2 = Product.objects.create(**product_2)
            self.product_3 = Product.objects.create(**product_3)

    def test_list_orders(self):
        response = self.client.get(orders_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    # Try creating order with products from different warehouses
    def test_create_orders_with_unexpected_product(self):
        order = {
            "customer": "John Doe",
            "customer_phone_number": "+237658884014",
            "order_items": [
                {"product": self.product_1.id, "quantity": 10},
                {"product": self.product_2.id, "quantity": 4},
                {"product": self.product_3.id, "quantity": 3},
            ],
            "initial_deposit": 5500.0,
            "warehouse_id": self.new_warehouse.id,
        }

        # Precise the format dus to the presence of an array in the data
        post_response = self.client.post(orders_endpoint, data=order, format="json")
        self.assertEqual(post_response.status_code, status.HTTP_400_BAD_REQUEST)

        # with open('response.txt', 'w') as f:
        #     f.write(f"Order data being sent: {order}\n")  # Write the response data as JSON
        #     f.write(f"Results post: {post_response}\n")  # Write the response data as JSON
        #     f.write(f"Results post 2: {post_response.data}\n")  # Write the response data as JSON

    # Try creating order with products from the same warehouses
    def test_create_and_list_orders(self):
        order = {
            "customer": "John Doe",
            "customer_phone_number": "+237658884014",
            "order_items": [
                {"product": self.product_2.id, "quantity": 10},
                {"product": self.product_3.id, "quantity": 10},
            ],
            "initial_deposit": 2500.0,
            "warehouse_id": self.new_warehouse_2.id,
        }

        post_response = self.client.post(orders_endpoint, data=order, format="json")
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        get_response = self.client.get(orders_endpoint)

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["count"], 1)

        # with open('response0.txt', 'w') as f:
        #     f.write(f"Order data being sent: {order}\n")  # Write the response data as JSON
        #     f.write(f"Results get: {get_response.data}\n")  # Write the response data as JSON
        #     f.write(f"Results post: {post_response}\n")  # Write the response data as JSON
        #     f.write(f"Results post 2: {post_response.data}\n")  # Write the response data as JSON
