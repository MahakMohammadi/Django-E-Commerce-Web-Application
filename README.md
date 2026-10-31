# 🛍️ Django E-Commerce Web Application

A full-featured online shopping web application built with **Django** and **MySQL**. The project provides a complete storefront experience, including product browsing, customer authentication, shopping cart management, checkout, and order tracking.

The application features a customized Django administration panel for managing products, collections, customers, inventory, and orders.

## ✨ Features

### 🛒 Storefront
- Homepage featuring featured products, new arrivals, best sellers, and promotions.
- Product browsing with pagination.
- Product search by title and description.
- Product filtering by collection.
- Detailed product pages with images and related products.
- Collection-based product browsing.

### 👤 User Authentication & Profiles
- Customer registration with input validation.
- Login and logout functionality.
- Customer profile pages.
- Automatic customer profile creation upon user registration.
- Persistent authentication using Django sessions.

### 🛍️ Shopping Cart
- Add products to the shopping cart.
- Update product quantities and remove items.
- Session-based cart management for both authenticated and anonymous visitors.
- Automatic inventory validation to prevent adding unavailable quantities.
- Dynamic cart item count and total price calculation.

### 📦 Checkout & Order Management
- Authentication-protected checkout.
- Customer address management.
- Order creation with individual order items.
- Automatic inventory updates after successful checkout.
- Order confirmation page.
- Customer order history.

### ⚙️ Customized Admin Panel
- Product and collection management.
- Customer and membership management.
- Order and payment-status management.
- Inventory monitoring and low-stock filtering.
- Bulk admin actions for updating product inventory and featured status.
- Product image management through inline administration.
- Search, filtering, and optimized database queries.

---

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, Bootstrap 5 |
| Database | MySQL |
| ORM | Django ORM |
| Authentication | Django Authentication System |
| Image Processing | Pillow |
| Testing | Django Test Framework |
| Development Tools | VS Code, MySQL Workbench, Git |

---

## 🏗️ Project Structure

```text
finalproject/
│
├── accounts/
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│
├── store/
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py
│   ├── migrations/
│   ├── templates/
│   │   └── store/
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── signals.py
│
├── tags/
│
├── playground/
│
├── finalproject/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── media/
├── manage.py
├── Pipfile
├── Pipfile.lock
└── .env.example
```

---

## 🗄️ Database Models

The application uses Django ORM to manage a relational MySQL database.

Main models include:

- **Product:** Product information, pricing, inventory, and collection relationships.
- **Collection:** Groups products into different categories.
- **ProductImage:** Stores multiple images for products.
- **Customer:** Customer information and membership levels.
- **Cart & CartItem:** Shopping cart and its associated products.
- **Order & OrderItem:** Customer orders and their individual items.
- **Address:** Customer shipping address information.
- **Promotion:** Product discount and promotional information.
- **Tag & TaggedItem:** Tagging functionality using Django Generic Relations.

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.13
- MySQL Server
- Pipenv
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Install dependencies

```bash
pip install pipenv
pipenv install --ignore-pipfile
pipenv shell
```

### 3. Create the MySQL database

Open MySQL Workbench or your MySQL client and execute:

```sql
CREATE DATABASE storefront;
```

### 4. Configure environment variables

Create a `.env` file in the same directory as `manage.py`, using `.env.example` as a template.

Configure your database credentials and Django settings:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=

DB_NAME=storefront
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-mysql-password
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

Access the administration panel:

```text
http://127.0.0.1:8000/admin/
```

---

## 🧪 Running Tests

The project includes tests for authentication, customer registration, product browsing, shopping cart operations, and checkout functionality.

Run the test suite with:

```bash
python manage.py test
```

---

## 📚 Key Concepts Demonstrated

- Django Model-View-Template (MVT) architecture.
- Object-Relational Mapping (ORM).
- Relational database design and relationships.
- User authentication and session management.
- CRUD operations.
- Django Forms and ModelForms.
- Class-Based Views and Function-Based Views.
- Django signals.
- Database query optimization using `select_related()` and `prefetch_related()`.
- Database transactions and atomic operations.
- Custom Django Admin functionality.
- Automated testing.

---

## 🎯 Project Goal

This project was developed as a practical exercise in Django web development, focusing on building a functional e-commerce application and applying backend development concepts, database management, authentication, and business logic in a real-world application structure.

---

## 📌 Project Status

Developed as a locally running web application for learning and demonstrating Django backend development.

**Note:** This project currently does not include an integrated online payment gateway or production deployment configuration.
