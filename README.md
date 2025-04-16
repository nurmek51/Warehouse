# Warehouse & Store Management Project

Welcome to your supercharged Warehouse & Store Management Django application! This repository houses the code for handling warehouse imports, managing store inventory, and performing all sorts of item wizardry. For full API documentation, visit [**warehouse.nurmek.site/docs**](https://warehouse.nurmek.site/docs).

> **Hint of humor:** A wise person once said, *“Never underestimate the power of neat organization… or well-placed barcodes.”* Now, you can do both with style.

## Table of Contents
1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Requirements](#requirements)
4. [Setup & Installation](#setup--installation)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [Key Endpoints](#key-endpoints)
8. [Contributing](#contributing)

---

## Features

- **Warehouse Upload**: Import items via CSV/XLSX into the warehouse, track them with a special `Upload` record.
- **Store Operations**: Move items from warehouse to store, apply discounts, sell them, and remove expired goods.
- **Inventory Tracking**: Manage item status (`warehouse`, `showcase`, `sold`, `deleted`), while automatically marking products as expired if needed.
- **Barcode Scanning**: Quickly identify items on the store by scanning barcodes to check stock availability or sell them on the spot.
- **Swagger Documentation**: Explore all available endpoints in a fancy interface at [warehouse.nurmek.site/docs](https://warehouse.nurmek.site/docs).

---

## Tech Stack

- **Django** (with Django REST Framework) – for the web application and RESTful API
- **PostgreSQL** – database
- **Celery & RabbitMQ** – background tasks (like automatic notifications and forecast tasks)
- **Swagger / drf-yasg** – interactive documentation
- **Docker (optional)** – containerize your entire environment

---

## Requirements

1. **Python 3.10+**
2. **PostgreSQL** (with correct credentials in the environment)
3. **RabbitMQ** (for Celery tasks, or tweak Celery settings as needed)
4. **Pipenv** or **virtualenv** (recommended for Python environment)

---

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-name/warehouse.git
   cd warehouse
   ```

2. **Create a virtual environment & activate** (example with `virtualenv`):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:  
   Create a `.env` file at the project root (same level as `settings.py`). Typical variables include:
   ```ini
   SECRET_KEY=your-secret-key
   DB_NAME=warehouse_db
   DB_USER=warehouse_user
   DB_PASSWORD=supersecretpassword
   DB_HOST=localhost
   DB_PORT=5432
   EMAIL_HOST_USER=your_email_address
   EMAIL_HOST_PASSWORD=your_email_password
   ```
   Make sure they match your PostgreSQL and email server settings.

5. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (so you can log in to Django admin, if desired):
   ```bash
   python manage.py createsuperuser
   ```

---

## Running the Application

- **Start the Django server**:
  ```bash
  python manage.py runserver
  ```
  By default, this will run on http://127.0.0.1:8000/.

- **Optional: Start Celery** (if you want scheduled tasks or background notifications):
  ```bash
  celery -A warehouse worker -l info
  ```
  
- **Optional: Start Celery Beat** (to schedule tasks like daily expiry notifications):
  ```bash
  celery -A warehouse beat -l info
  ```

---

## Project Structure

A quick peek into key files and directories:

```
warehouse/
├── accounts/         # Authentication & user account logic
├── store/            # Store inventory management app
│   ├── models.py     # `StoreItem` model
│   ├── views.py      # Store item operations (discount, remove, transfer, sell)
│   └── urls.py       # Store API routes
├── warehouse_app/    # Warehouse side of the project
│   ├── models.py     # `Upload` model for importing files
│   ├── views.py      # File upload and warehouse items management
│   └── urls.py       # Warehouse API routes
├── prediction/       # Forecasting module (placeholder)
├── warehouse/        # Primary Django project settings and config
│   ├── settings.py   # Environment, database, installed apps
│   ├── urls.py       # Project-level routes, including swagger
│   ├── celery.py     # Celery configuration
│   └── wsgi.py       # WSGI entry point
└── requirements.txt
```

---

## Key Endpoints

Below is a small selection. For the complete list, refer to the [Swagger UI](https://warehouse.nurmek.site/docs).

### Warehouse
- **POST** `/api/warehouse/upload`  
  Import products to the warehouse via CSV or Excel file.

- **GET** `/api/warehouse/files`  
  List uploaded files.

- **GET** `/api/warehouse/items/{file_id}`  
  Show warehouse items for a specific file upload.

- **POST** `/api/warehouse/to-store`  
  Transfer items from warehouse to the store.

### Store
- **GET** `/api/store/items`  
  List all items currently on the store showcase.

- **POST** `/api/store/discount`  
  Apply a discount to a showcase item.

- **POST** `/api/store/remove`  
  Mark an expired item as deleted.

- **POST** `/api/store/transfer-to-warehouse`  
  Move an item back from the store to the warehouse.

- **POST** `/api/store/sell`  
  Sell an item from the store.

- **GET** `/api/store/scan/{barcode}`  
  Find and retrieve item details by its barcode.

> All endpoints that require authorization expect a JWT token in the `Authorization` header as `Bearer <token>`.

---

## Contributing

If you have ideas to improve this project, feel free to open an issue or submit a pull request. The world can always use more well-managed warehouses and properly labeled items.
