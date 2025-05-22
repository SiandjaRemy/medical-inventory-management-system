from django.contrib.auth import get_user_model

from warehouse_app.models import Employee, Warehouse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

import logging
import json

from InventoryManagement.utils.context_manager import set_current_context

logger = logging.getLogger(__name__)
User = get_user_model()

warehouse_endpoint = "http://localhost:8000/warehouses/"
employee_endpoint = "http://localhost:8000/employees/"
userlogs_endpoint = "http://localhost:8000/userlogs/"
products_endpoint = "http://localhost:8000/products/"
orders_endpoint = "http://localhost:8000/orders/"



# ----------------------------------------------------------------------------------
#          Testing actions a warehouse manager can perform on an warehouses
# ----------------------------------------------------------------------------------

class ManagerActionsOnWarehouseTestCase(APITestCase):
    
    def setUp(self):
        # Create clients
        self.client = APIClient()
        self.client_2 = APIClient()
        
        # Set admin
        self.admin_user = User.objects.create_superuser(email="myadmin@gmail.com", username="myadmin", password="987654321@")
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_tokens = str(admin_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_tokens}")
        
        # Create data for warehouses
        data = {
            "name": "Site 1",
            "location": "London"
        }
        data_2 = {
            "name": "Site 2",
            "location": "London"
        }
        
        with set_current_context(self.admin_user):
            self.new_warehouse = Warehouse.objects.create(**data)
            self.new_warehouse_2 = Warehouse.objects.create(**data_2)
        
        # Create a manager linked to a warehouse
        employee_manager_date = {
            "email": "mymanager@gmail.com",
            "first_name": "my",
            "last_name": "manager",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "5877956612",
            "is_manager": True,
            "warehouse_id": self.new_warehouse.id,
        }
        self.client.post(employee_endpoint, data=employee_manager_date)
        manager = Employee.objects.filter(user__email=employee_manager_date["email"]).first()
        manager_refresh = RefreshToken.for_user(manager.user)
        self.manager_tokens = str(manager_refresh.access_token)

        self.client_2.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_tokens}")

        employee_data = {
            "email": "myemployee@gmail.com",
            "first_name": "my",
            "last_name": "employee",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "5877956612",
        }
        # Manager creates an employee
        self.client_2.post(employee_endpoint, data=employee_data)
        
    def test_list_warehouses(self):
        response = self.client_2.post(warehouse_endpoint)                
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                        

    def test_retrieve_manager_warehouses(self):
        response = self.client_2.get(f"{warehouse_endpoint}{self.new_warehouse.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['name'], 'Site 1')
        
        
    def test_retrieve_another_warehouses(self):
        response = self.client_2.get(f"{warehouse_endpoint}{self.new_warehouse_2.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                        
        
    def test_update_employee_in_warehouse(self):
        data = {
            "first_name": "my",
            "last_name": "employee updated",
            "phone_number": "+237659789941",
            "image": "",
            "id_number": "000000000000",
        }
        employee = Employee.objects.filter(user__email="myemployee@gmail.com").first()
        response = self.client_2.patch(f"{employee_endpoint}{employee.id}/", data=data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_number'], data["id_number"])
        
    
    
# ----------------------------------------------------------------------------------
#          Testing actions a warehouse manager can perform on an Employees
# ----------------------------------------------------------------------------------


