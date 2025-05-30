﻿# 🏥 PharmaWarehouse API - Modern Inventory Management for Medical Supply Chains  

*A robust Django REST API powering multi-warehouse pharmaceutical inventory systems with granular access control and audit compliance*  

[![Django](https://img.shields.io/badge/Django-4.2-brightgreen)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-blue)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-purple)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

---
![2](https://github.com/user-attachments/assets/843b152d-6149-4fa0-8335-b939c2b2b762)

---

## 🌟 Key Features

### 🔐 Role-Based Access Control
- **Admin Overlord**: Full system control - create warehouses, manage users, audit trails
- **Warehouse Managers**: Complete oversight of assigned location (inventory, orders, staff)
- **Operational Staff**: Secure order processing with partial payment tracking

### 📦 Core Inventory Capabilities
- Multi-warehouse pharmaceutical stock management
- Batch tracking with expiry date monitoring
- Installment payment system with validation
- Cloudinary-integrated product imaging (GMP-compliant storage)

### 📊 **Real-Time Business Intelligence**
- **Executive Dashboard**: Single-endpoint delivery of critical KPIs including:
  - Warehouse performance metrics
  - Employee productivity analytics
  - Product stock levels (with low/out-of-stock alerts)
  - Annual sales trends by month
- **Role-Adaptive Data**: Automatically filters data based on user permissions
- **Optimized Queries**: Aggregates multiple datasets in efficient database calls

### 🕵️ Enterprise-Grade Security
- Custom permission architecture tailored for medical logistics
- JWT authentication with Djoser integration
- Full audit trails via django-easyaudit
- Action whitelisting per user role

### ⚡ Operational Tools
- Paginated API endpoints with search/filter
- Comprehensive activity logs
- Performance-optimized queries (Django Debug Toolbar validated)

---


## 🛠️ **Getting Started: Your API Adventure Awaits!** 🚀

Ready to dive in? Setting up this API is a breeze! Just follow these simple steps, and you'll be up and running in no time.

### **The Quick Start Guide** 🏁

1.  **Clone it Down!** 🌳
    Grab the code from this repository to kick things off.
    ```bash
    git clone https://github.com/SiandjaRemy/medical-inventory-management-system.git
    cd medical-inventory-management-system
    ```

2.  **Virtual Environment Magic!** ✨
    Create a dedicated virtual environment. It's like giving your project its own clean, organized workspace.
    ```bash
    python -m venv venv
    ```
    or 
    ```bash
    virtualenv venv
    ```

3.  **Activate the Virtual Environment:**
    * **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install the Essentials!** 📦
    Run `pip install -r requirements.txt` to get all the necessary ingredients for your API.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Secret .env File!** 🤫
    Create a super-secret `.env` file in the root directory of your project. This is where your sensitive keys and configurations will live, safe from prying eyes (and Git). Don't worry, there's a `.env.local` to guide you!

6.  **Database Delight!** 💾
    Set up your local **PostgreSQL** database (my favorite!), or opt for **SQLite** if you prefer. Just make sure to configure those environment variables in your `.env` file **before** you migrate!

7.  **Migration Mania!** ➡️
    Run these commands to get your database schema all set up:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

8.  **Key to the Kingdom!** 🔑
    Generate a strong Django secret key and set it as the `SECRET_KEY` environment variable in your `.env` file. This keeps your project secure!

9.  **Debug On (for now!)** 🐞
    Set `DEBUG=True` in your `.env` for happy development. Remember to turn this off in production!

10. **Server's Up!** 💻
    Finally, fire up the server:
    ```bash
    python manage.py runserver
    ```

    * **Explore Endpoints!** 🗺️ Head to `http://localhost:8000/swagger` for an interactive API experience.
    * **Read the Docs!** 📚 Get the full lowdown on the API at `http://localhost:8000/redoc`.

---

## 🏗️ **System Architecture**
```mermaid
graph TD
  A[Admin] -->|Manages| B[Warehouses]
  A -->|Assigns| C[Managers]
  C -->|Oversees| D[Employees]
  D -->|Processes| E[Orders]
  E -->|Tracks| F[Partial Payments]
  G[Audit System] -->|Logs| H[All Actions]
  I[Dashboard] -->|Aggregates| J[Warehouse Data]
  I -->|Visualizes| K[Business Metrics]
```

---

## 🌟 **Under the Hood: What Makes This API Tick?** 💖

This isn't just a collection of endpoints; it's a meticulously crafted system designed for efficiency and control!

### **A Tale of Two Apps** ✌️

I've smartly divided this project into two core applications:

* **`accounts`**: Your go-to for all things user-related – authentication, permissions, and profiles.
* **`warehouse_app`**: The powerhouse handling all the logistics, from product inventory to order fulfillment.

### 📈 **Decision-Ready Dashboards**
The API includes a powerful dashboard endpoint that delivers comprehensive operational insights at a glance:

* **Smart Data Filtering**: Automatically adjusts displayed metrics based on user role and warehouse assignment

* **Inventory Health Monitoring**: Tracks stock levels with low-stock and out-of-stock indicators

* **Sales Performance**: Monthly breakdowns of completed vs pending orders with revenue tracking

* **Team Analytics**: Employee headcounts with active/inactive status tracking

* **Admin-Only Insights**: Additional warehouse comparison metrics for system administrators

All data is delivered through a single optimized endpoint that minimizes database queries while maximizing information value.


### **Hierarchies & Superpowers!** 🦸‍♀️🦸‍♂️

Our API features a robust **role-based access control** system, ensuring everyone has just the right amount of power!

* 👑 **Admin Users:** These are the supreme commanders! They can create warehouses, onboard employees (managers or simple staff), manage all products (even delete them from their dashboard!), process orders, and handle partial payments. Plus, they see *all* user actions logged by `django-easy-audit` – total transparency!
* 💼 **Manager Users:** They're the regional chiefs! Managers wield significant power, but only within their **assigned warehouse**. They can do almost everything an Admin can, except create other managers. They also get to keep an eye on their team's activities.
* 🤝 **Simple Employees:** The boots-on-the-ground heroes! Employees focus on core tasks: creating orders and processing those flexible partial payments.

### **Money Talks: Partial Payments!** 💰

Since not every payment is a one-shot deal, this system gracefully handles **partial payments**, making installments a breeze. Intelligent validations ensure customers never overpay, and order statuses update automatically once the full amount is settled. How cool is that?

### **Always Watching: Auditing & Logging!** 🕵️‍♀️

Transparency and traceability are key!

* **`django-easy-audit`**: This awesome library keeps a watchful eye on every action users perform, providing an invaluable audit trail.
* **High-Level Logging**: I've implemented detailed logging to ensure every significant event is recorded. From minor info to critical errors, they're all captured, making debugging and monitoring a dream!

### **Find Anything, Anytime!** 🔎

No more needle-in-a-haystack searches! Most of the endpoints come equipped with **pagination, powerful search capabilities, flexible filtering, and intelligent ordering**, so you can pinpoint exactly what you need, exactly when you need it.

---

## 🔒 **Authentication: Your Digital Fortress!** 🛡️

I've customized **`djoser`** to create a secure and user-friendly authentication system, featuring:

* **Your Profile, Your Control:** Easily view and update your user profile.
* **Password Power-Ups:** Change your password securely whenever you need a refresh.
* **Forgot Your Password? No Problem!** The smooth password reset flow ensures you're never locked out.
* **Secure Logout:** A robust logout mechanism ensures your session ends securely, every single time.

---

## 📸 **Media & Storage: Cloud-Powered!** ☁️

Say goodbye to local storage woes! **Cloudinary** handles all your media needs. Employee profile pictures, product images – everything's stored securely and efficiently in the cloud.

---

## 🧪 **Testing & Deployment: Built for Reliability!** ✅

This API isn't just functional; it's rock-solid!

* **Rigorous Testing:** I've written extensive tests for the endpoints, models, and views. This means less bugs, more features, and peace of mind!
* **Deployment Ready!** 🚀
    Getting this API into production is easy-peasy! I've included handy `build.sh` and `run_gunicorn.py` files to streamline deployment on platforms like Render.

---

## 📈 **Looking Ahead: The Road to Even More!** 🛣️

**Planned Features**:

* Complete load testing suite

* Regulatory compliance module

* Real-time stock alerts

**Contribution Guide:**
Got any questions or ideas? I'd love to hear them!

1. Fork the repository

2. Create your feature branch

3. Submit a PR with tests
