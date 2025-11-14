# CloudStorm

A modern, Django-based file management system with AI-powered data extraction, group-based organization, and secure cloud storage integration.

## Features

- **File Management**: Upload, organize, and manage files (images, videos, documents, audio)
- **Group-Based Organization**: Organize files into public or private groups with role-based access control
- **AI-Powered Data Extraction**: Extract data from images, documents, audio, and video files using OpenAI
- **Secure Storage**: Azure Blob Storage integration for scalable file storage
- **User Authentication**: JWT-based authentication with encrypted user data
- **Tagging System**: Tag files and groups for easy organization and search
- **Async Processing**: Celery-based background tasks for file processing
- **API Documentation**: Interactive API documentation with Swagger UI and ReDoc
- **Virus Scanning**: Built-in virus scanning middleware for uploaded files
- **RESTful API**: Comprehensive REST API with filtering, pagination, and search

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL 12
- **Task Queue**: Celery 5.2 with Redis
- **Storage**: Azure Blob Storage
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: drf-spectacular
- **Testing**: pytest
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized setup)
- PostgreSQL 12+ (if running locally)
- Redis (if running locally)
- Azure Storage Account (for cloud storage)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd CloudStorm
```

2. Create a `.env` file in the root directory with the following variables:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
DEBUG=True
DJANGO_ENV=development

# Database
POSTGRES_DB=cloudstorm
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
PG_HOST=db
PG_PORT=5432

# Azure Storage
AZURE_CONTAINER=your-container-name
AZURE_ACCOUNT_NAME=your-account-name
AZURE_ACCOUNT_KEY=your-account-key
AZURE_CONNECTION_STRING=your-connection-string

# OpenAI
OPEN_API_KEY=your-openai-api-key

# Field Encryption
FIELD_ENCRYPTION_KEY=your-field-encryption-key
```

3. Build and start the services:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd CloudStorm
```

2. Create a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a `.env` file as shown above)

5. Run database migrations:
```bash
python manage.py migrate
```

6. Load fixtures (optional):
```bash
python manage.py loaddata fixtures/fixtures.json
```

7. Start the development server:
```bash
python manage.py runserver
```

8. In a separate terminal, start Celery worker:
```bash
celery -A CloudStorm worker -l INFO --pool=solo
```

## Project Structure

```
CloudStorm/
├── apps/
│   ├── files/          # File management app
│   ├── groups/         # Group management app
│   └── users/          # User authentication app
├── CloudStorm/        # Main project settings
│   ├── settings/      # Environment-specific settings
│   └── urls.py        # URL configuration
├── tests/             # Test suite
├── fixtures/          # Database fixtures
├── scripts/           # Startup scripts
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── manage.py
```

## API Documentation

Once the server is running, access the API documentation at:

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## Authentication

The API uses JWT (JSON Web Token) authentication. To authenticate:

1. Register a new user or login:
```bash
POST /api/users/register/
POST /api/users/login/
```

2. Use the returned access token in subsequent requests:
```bash
Authorization: Bearer <access_token>
```

## Key Endpoints

### Users
- `POST /api/users/register/` - Register a new user
- `POST /api/users/login/` - Login and get JWT tokens
- `POST /api/users/logout/` - Logout (blacklist token)

### Groups
- `GET /api/groups/` - List groups
- `POST /api/groups/` - Create a group
- `GET /api/groups/{id}/` - Retrieve a group
- `PATCH /api/groups/{id}/` - Update a group
- `DELETE /api/groups/{id}/` - Delete a group

### Files
- `GET /api/files/` - List files (with filtering and pagination)
- `POST /api/files/` - Upload file(s)
- `GET /api/files/{id}/` - Retrieve file details
- `PATCH /api/files/{id}/` - Update file metadata
- `DELETE /api/files/{id}/` - Delete a file

## Testing

Run tests using pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=apps
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `ENCRYPTION_KEY` | Encryption key for sensitive data | Yes |
| `DEBUG` | Debug mode (True/False) | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `POSTGRES_USER` | Database user | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `AZURE_CONTAINER` | Azure Blob Storage container name | Yes |
| `AZURE_ACCOUNT_NAME` | Azure Storage account name | Yes |
| `AZURE_ACCOUNT_KEY` | Azure Storage account key | Yes |
| `OPEN_API_KEY` | OpenAI API key for data extraction | Yes |
| `FIELD_ENCRYPTION_KEY` | Key for encrypting model fields | Yes |

## Development

### Running Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating a Superuser

```bash
python manage.py createsuperuser
```

### Accessing Django Admin

Navigate to `http://localhost:8000/admin/` and login with your superuser credentials.

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment variables
2. Set `DJANGO_ENV=production` in your environment variables
3. Ensure all required environment variables are set
4. Use a production-ready WSGI server (Gunicorn is included)
5. Configure proper CORS settings
6. Set up SSL/TLS certificates
7. Configure proper database backups

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Author

**Konstantinos Damianos**
- Email: kostas2372@gmail.com

## Support

For support, email kostas2372@gmail.com or open an issue in the repository.

