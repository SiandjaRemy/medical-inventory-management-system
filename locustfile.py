from locust import HttpUser, TaskSet, task, between
import random
import json

# Sample user credentials for authentication
users = {
    "admin": {"email": "admin@gmail.com", "password": "1111"},
    "manager": {"email": "remysiandja@gmail.com", "password": "987654321@"},
    "employee": {"email": "remy@gmail.com", "password": "987654321@"},
}

warehouses = [
    "6d0783c8-79c8-48e0-a602-ebc93f3bee3f",
    "6d0783c8-79c8-48e0-a602-ebc93f3bee3f",
    "90fb1b63-e452-47bf-9829-d819dab20c1a",
    "c61316d3-97fa-4676-83a7-becdc54a3305",
    "6c8e40ea-c195-415d-8ca5-cf200eeaa47a",
]

MEASUREMENTS = [
    "Millimeter",
    "Centimeter",
    "Meter",
    "Inch",
    "Foot",
    "Kilogram",
    "Milligram",
    "Gram",
    "Pound",
    "Ounce",
    "Liter",
    "Milliliter",
    "Cubic Meter",
    "Cubic Centimeter",
    "Cubic Inch",
    "Cubic Foot",
    "Square Meter",
    "Square Centimeter",
    "Square Inch",
    "Square Foot",
    "Hectare",
    "Acre",
    "Temperature in Celsius",
    "Temperature in Fahrenheit",
    "Volume in Gallons",
    "Volume in Quarts",
    "Volume in Pints",
    "Count",
    "Set",
    "Box",
]


def get_random_measurement_unit():
    return random.choice(MEASUREMENTS).lower()


class AdminBehavior(TaskSet):
    def on_start(self):
        self.token = self.authenticate("admin")

    def authenticate(self, user_type):
        """Authenticate user and return JWT token."""
        user = users[user_type]
        response = self.client.post("/auth/jwt/create/", json=user)
        if response.status_code == 201:
            return response.json().get("access")
        else:
            print(f"Authentication failed for {user_type}: {response.text}")
            return None

    @task(3)
    def create_warehouse(self):
        """Admin creates a warehouse."""
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}

            random_value = random.randint(1, 100)
            data = {"name": f"Site {random_value}", "location": f"Town {random_value}"}
            self.client.post("/warehouses/", headers=headers, json=data)

    @task(2)
    def list_warehouses(self):
        """Admin lists all warehouses."""
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}
            self.client.get("/warehouses/", headers=headers)



class ManagerBehavior(TaskSet):
    def on_start(self):
        self.token = self.authenticate("manager")
        self.user_data = self.my_data(self.token)

    def authenticate(self, user_type):
        """Authenticate user and return JWT token."""
        user = users[user_type]
        response = self.client.post("/auth/jwt/create/", json=user)
        if response.status_code == 201:
            token = response.json().get("access")
            print(f"Token is: {token}")
            return response.json().get("access")
        else:
            # print(f"Authentication failed for {user_type}: {response.text}")
            print(f"Authentication failed for {user_type}")
            print(f"Response: {response}")
            print(f"Response 2: {response.json()}")
            return None
        
    def my_data(self, token):
        """Get authenticated user data."""
        my_token = f"Token {token}"
        headers = {"Authorization": my_token}
        response = self.client.get("/auth/users/me/", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            # print(f"Fetching user data failed for user: {response.text}")
            print(f"Fetching user data failed for user")
            return None

    @task(3)
    def create_employee(self):
        """Manager creates an employee."""
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}
            
            data = {
                "email": f"user-{random.randint(1, 100)}@example.com",
                "first_name": "Test",
                "last_name": "User",
                "phone_number": "+1234567890",
                "image": "",
                "id_number": f"ID{random.randint(1000000, 9999999)}",
                "is_manager": random.choice([True, False]),
                "warehouse_id": self.user_data.get("warehouse_id"),
            }

            self.client.post("/employees/", headers=headers, json=data)

    @task(2)
    def list_employees(self):
        """Manager lists all employees."""
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}
            self.client.get("/employees/", headers=headers)

    @task(2)
    def create_product(self):
        """Manager creates a product."""
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}
            
            payload = {
                "name": "Product A",
                "category": None,
                "description": "A simple product",
                "image": "",
                "measurement_unit": get_random_measurement_unit(),
                "quantity": random.randint(100, 2000),
                "unit_price": random.randint(1000, 50000),
                "warehouse_id": self.user_data.get("warehouse_id"),
            }
            self.client.post("/products/", json=payload)

            data = {
                "name": f"Product {random.randint(1, 100)}",
                "warehouse_id": random.choice(warehouses),
            }
            self.client.post("/products/", headers=headers, json=data)


# class EmployeeBehavior(TaskSet):
#     def on_start(self):
#         self.token = self.authenticate("employee")
#         self.user_data = self.my_data()

#     def authenticate(self, user_type):
#         """Authenticate user and return JWT token."""
#         user = users[user_type]
#         response = self.client.post("/auth/jwt/create/", json=user)
#         if response.status_code == 201:
#             return response.json().get("access")
#         else:
#             print(f"Authentication failed for {user_type}: {response.text}")
#             return None
        
#     def my_data(self):
#         """Get authenticated user data."""
#         headers = {"Authorization": f"Token {self.token}"}
#         response = self.client.get("/auth/users/me/", headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             print(f"Fetching user data failed for user: {response.text}")
#             return None
        

#     # @task(3)
#     # def create_order(self):
#     #     """Employee creates an order."""
#     #     if self.token:
#     #         headers = {"Authorization": f"Token {self.token}"}
#     #         data = {
#     #             "product_id": random.choice(
#     #                 warehouses
#     #             ),  # Assuming product IDs are same as warehouse IDs
#     #             "quantity": random.randint(1, 10),
#     #         }
#     #         self.client.post("/orders/", headers=headers, json=data)

#     # @task(2)
#     # def list_orders(self):
#     #     """Employee lists all orders."""
#     #     if self.token:
#     #         headers = {"Authorization": f"Token {self.token}"}
#     #         self.client.get("/orders/", headers=headers)

#     # @task(1)
#     # def update_order(self):
#     #     """Employee updates an order."""
#     #     if self.token:
#     #         headers = {"Authorization": f"Token {self.token}"}
#     #         order_id = random.randint(
#     #             1, 100
#     #         )  # Assuming order IDs are between 1 and 100
#     #         data = {
#     #             "quantity": random.randint(1, 10),
#     #         }
#     #         self.client.put(f"/orders/{order_id}/", headers=headers, json=data)


class AdminUser(HttpUser):
    tasks = [AdminBehavior]
    wait_time = between(1, 5)
    weight = 1  # 10% of users


class ManagerUser(HttpUser):
    tasks = [ManagerBehavior]
    wait_time = between(1, 5)
    weight = 2  # 20% of users


# class EmployeeUser(HttpUser):
#     tasks = [EmployeeBehavior]
#     wait_time = between(1, 5)
#     weight = 7  # 70% of users
