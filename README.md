# FastAPI Template Project

Welcome to the **FastAPI Template Project**! This repository provides a powerful and flexible template to kickstart your FastAPI projects with a robust backend setup, including authentication, administration, task management, and more. The template leverages a modern Python stack to ensure scalability and maintainability.

## Features

- **Authentication**: Integration with `fastapi-users` for managing user authentication and registration with support for SQLAlchemy.
- **Admin Interface**: A fully featured admin interface using `sqladmin` for managing your database entities.
- **CRUD Operations**: Pre-built CRUD endpoints for managing your database models, allowing you to focus on building your application logic.
- **Database Migrations**: Database migration support using `alembic` with an asynchronous database setup.
- **S3 File Handling**: Integrated support for handling files with S3, including CRUD operations and generating signed URLs.
- **Task Management**: Two task managers are included:
  - **Taskiq**: Lightweight and async-friendly task manager with support for Redis and RabbitMQ.
  - **Celery**: A powerful task manager with support for periodic tasks using SQLAlchemy-based scheduling.
- **Two CLI Modes**: The project can be run in two different modes, making it versatile for development and production environments.

## Tech Stack

The following are the key technologies used in this project:

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- **SQLAlchemy (asyncio)**: Database toolkit and ORM with asynchronous support.
- **Alembic**: Lightweight database migration tool for use with SQLAlchemy.
- **PostgreSQL**: Advanced open-source relational database.
- **Redis**: In-memory data structure store used as a database, cache, and message broker.
- **Gunicorn**: Python WSGI HTTP server for UNIX.
- **aioboto3**: Asynchronous version of boto3, the AWS SDK for Python, used for S3 integration.
- **Pillow**: Python Imaging Library for image processing.
- **Taskiq**: Lightweight task manager with support for FastAPI, Redis, and RabbitMQ.
- **Celery**: Distributed task queue with scheduling capabilities.
- **sqladmin**: Simple yet powerful admin interface for SQLAlchemy.

## Project Structure

### app

```
├── src
│ ├── admin # Admin-related modules, including authentication
│ ├── auth # Authentication logic
│ ├── conf # Configuration files and settings
│ ├── crud # CRUD operations
│ ├── db # Database models and session management
│ ├── media # Media handling
│ ├── models # Database models
│ ├── schemas # Pydantic models
│ ├── static # Static files (CSS, JS, etc.)
│ ├── tasks # Task definitions for Taskiq and Celery
│ ├── templates # HTML templates for rendering
│ ├── users # User-related logic and models
│ ├── cli.py # CLI utilities for managing the application
│ └── main.py # Main entry point of the application
│ └── routers.py # Application route definitions
├── alembic # Alembic migrations
├── alembic.ini # Alembic configuration file
├── .dockerignore # Dockerignore configurations
├── Dockerfile # Dockerfile for building the application image
└──  requirements.txt # Project dependencies
```

### launching infrastructure

```
infra
├── debug # Configuration for debug
├── nginx # Nginx configurations
├── stage # Configuration for staging
└── scripts # Additional scripts for deployment and management
```

### The launch control is in the root

```
app.py # Application management script
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/fastapi_template.git
cd fastapi_template
```

2. **Install dependencies:**

```bash
python3.11 -m venv venv && source venv/bin/activate && python -m pip install --upgrade pip setuptools wheel

pip install -r backend/requirements.txt
```

3. **Create local domains to work with s3:**

```bash
sudo ./infra/add_hosts.sh
```

4. **Run the project:**

```bash
./app.py debug

# or

./app.py stage
```

5. **Project shutdown:**

```bash
./app.py stop

# or

./app.py stop --clean #  if the system needs to be cleared of dangling
```

### Usage

- **Admin Interface**: Accessible at /admin once the server is running.
- **API Documentation**: Automatically generated documentation available at /docs or /redoc.
- **Saving images from the frontend**: An interface for saving pictures is available on the home page. VUE.JS scripts can be found in the /static folder.
- **Task Management**: Tasks can be triggered using Taskiq or Celery, with configurations available in the tasks directory.

### Contributing

Contributions are welcome! Please open an issue or submit a pull request with your enhancements or bug fixes.

### License

This project is licensed under the MIT License.
