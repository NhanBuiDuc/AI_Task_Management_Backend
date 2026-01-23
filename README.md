# JARVIS Backend - Django REST API

A Django-based REST API for the JARVIS task management system with AI-powered features.

## Quick Start (Windows)

### 1. Setup Database

```bash
cd back-end
setup_db.bat
```

This will:
- Remove old database files
- Clean migrations
- Create fresh migrations
- Apply migrations
- Optionally create a superuser

### 2. Run Quick Test

```bash
python quick_test.py
```

This verifies that the database and models are working correctly.

### 3. Start Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

The API will be available at: http://localhost:8000

### 4. Run API Tests

In a new terminal (while server is running):

```bash
python test_apis.py
```

This will test all API endpoints and create sample data.

## Complete Development Environment

The `run.bat` script orchestrates the entire setup:

```bash
# Basic usage
run.bat

# Skip API tests
run.bat --no-tests

# Keep server running after tests
run.bat --keep-server

# Automatically teardown database on exit
run.bat --auto-teardown

# Show help
run.bat --help
```

## API Endpoints

### Core Resources

- **Projects**: `/projects/`
  - GET - List all projects
  - POST - Create project
  - GET `/projects/{id}/` - Get project details
  - PATCH `/projects/{id}/` - Update project
  - DELETE `/projects/{id}/` - Delete project
  - GET `/projects/{id}/children/` - Get sub-projects
  - PATCH `/projects/{id}/move/` - Move project to parent
  - PATCH `/projects/{id}/make_independent/` - Remove parent

- **Sections**: `/sections/`
  - GET - List all sections (filter by `?project_id=...`)
  - POST - Create section
  - GET `/sections/{id}/` - Get section details
  - PATCH `/sections/{id}/` - Update section
  - DELETE `/sections/{id}/` - Delete section
  - POST `/sections/get_or_create_completed/` - Get/create Completed section

- **Tasks**: `/tasks/`
  - GET - List all tasks (filter by `?project_id=...`)
  - POST - Create task
  - GET `/tasks/{id}/` - Get task details
  - PATCH `/tasks/{id}/` - Update task
  - DELETE `/tasks/{id}/` - Delete task

### Task Actions

- PATCH `/tasks/{id}/completion/` - Mark task as completed
- PATCH `/tasks/{id}/total_completion/` - Archive task (totally completed)
- PATCH `/tasks/{id}/move_to_project/` - Move task to different project
- PATCH `/tasks/{id}/move_to_section/` - Move task to section
- PATCH `/tasks/{id}/make_unsectioned/` - Remove section assignment

### View Filters

- GET `/tasks/by_view/?view=inbox` - Get tasks by view (inbox, today, upcoming, project, overdue)
- GET `/tasks/by_due_date/?due_date=YYYY-MM-DD` - Get tasks due on specific date
- GET `/tasks/by_date_range/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get tasks in range
- GET `/tasks/overdue/` - Get overdue tasks
- GET `/tasks/completed/` - Get totally completed tasks
- GET `/tasks/counts/?today_date=YYYY-MM-DD` - Get task counts for all views

## Data Models

### Project
```json
{
  "id": "uuid",
  "name": "Project Name",
  "parent_id": "uuid or null",
  "icon": "📁",
  "color": "#FF6B6B",
  "taskCount": 5,
  "hasChildren": false
}
```

### Section
```json
{
  "id": "uuid",
  "name": "Section Name",
  "project_id": "uuid or null",
  "current_view": ["inbox", "today"]
}
```

### Task
```json
{
  "id": "uuid",
  "name": "Task Name",
  "description": "Task description",
  "project_id": "uuid or null",
  "section_id": "uuid or null",
  "due_date": "2025-01-20",
  "completed": false,
  "totally_completed": false,
  "current_view": ["inbox", "today"],
  "piority": "medium",
  "reminder_date": "2025-01-20T09:00:00Z",
  "completed_date": "",
  "duration_in_minutes": 30,
  "repeat": "every week"
}
```

## Key Features

### Automatic View Calculation

Tasks automatically calculate their views based on `due_date` and `project_id`:

- **Inbox tasks** (no project): `["inbox"]` view
- **Project tasks**: `["project"]` view
- **Due today**: Add `["today"]` view
- **Due within 14 days**: Add `["upcoming"]` view
- **Past due**: Add `["overdue"]` view

Views update automatically when you save a task.

### Two Completion States

- **completed**: Task is checked off, moves to Completed section, stays in view
- **totally_completed**: Task is archived, removed from all views, section detached

### Hierarchical Projects

Projects can have parent/child relationships for nested organization.

### Section Organization

Sections can belong to:
- A specific project (scoped sections)
- No project (global sections like Inbox sections)

## Celery Background Tasks (Optional)

For automatic task categorization, you need Redis and Celery:

### Start Redis
```bash
redis-server
```

### Start Celery Worker
```bash
celery -A jarvis_backend worker --loglevel=info
```

### Start Celery Beat
```bash
celery -A jarvis_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Periodic Tasks

- Every 5 minutes: Check and update overdue tasks
- Every 10 minutes: Categorize all tasks by due date
- Daily at midnight: Maintain Today sections

## AI Features (Optional)

The backend includes AI-powered features using local Ollama.

### Setup Ollama

1. Download Ollama from https://ollama.ai
2. Install llama3.2 model: `ollama pull llama3.2`
3. Start Ollama (usually auto-starts)

### AI Endpoints

- POST `/ai/process/` - Process natural language intentions
- POST `/ai/suggestions/` - Generate task suggestions
- GET `/ai/insights/` - Get AI insights
- GET `/ai/patterns/` - Analyze task patterns
- POST `/ai/batch/` - Create multiple tasks from suggestions

Note: AI endpoints require authentication (not included in basic setup).

## Testing

### Manual API Testing

Use the provided `test_apis.py` script:

```bash
python test_apis.py
```

This tests:
- Project CRUD operations
- Section management
- Task creation and updates
- View filters
- Task movement and completion

### Django Unit Tests

```bash
python manage.py test
```

## Database Management

### Reset Database
```bash
setup_db.bat
```

### Create Migrations
```bash
python manage.py makemigrations
```

### Apply Migrations
```bash
python manage.py migrate
```

### Django Admin

Access at: http://localhost:8000/admin/

Create a superuser first:
```bash
python manage.py createsuperuser
```

## Troubleshooting

### Port 8000 Already in Use

Kill the process:
```bash
# Find process ID
netstat -ano | findstr :8000

# Kill process (replace <PID> with actual ID)
taskkill /F /PID <PID>
```

### Migration Errors

Reset database and migrations:
```bash
setup_db.bat
```

### Server Won't Start

Check `django.log` for errors:
```bash
type django.log
```

### Tests Failing

Make sure server is running:
```bash
# Terminal 1
python manage.py runserver 0.0.0.0:8000

# Terminal 2
python test_apis.py
```

## Configuration

### Settings (jarvis_backend/settings.py)

- **DEBUG**: Set to `False` in production
- **SECRET_KEY**: Change in production
- **ALLOWED_HOSTS**: Update for your domain
- **CORS_ALLOWED_ORIGINS**: Configure allowed frontend origins
- **DATABASE**: Currently SQLite, can switch to PostgreSQL

### CORS Configuration

Allowed origins for local development:
- http://localhost:3000 (and other ports)
- http://127.0.0.1:3000 (and other ports)

## Project Structure

```
back-end/
├── jarvis_backend/         # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py             # URL routing
│   ├── celery.py           # Celery configuration
│   └── asgi.py             # ASGI configuration (WebSockets)
├── tasks_api/              # Main application
│   ├── models.py           # Data models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views (core)
│   ├── views_agent.py      # AI-powered views
│   ├── views_analytics.py  # Analytics views
│   ├── urls.py             # API URL routing
│   ├── agents/             # AI agents
│   │   └── task_agent.py   # LangChain task agent
│   ├── utils/              # Utility modules
│   │   ├── analytics.py    # Analytics tracking
│   │   ├── mongodb.py      # MongoDB integration
│   │   └── notifications.py # Notification service
│   └── management/         # Django commands
│       └── commands/
│           ├── setup_periodic_tasks.py
│           └── test_categorize_tasks.py
├── test_apis.py            # API test suite
├── quick_test.py           # Quick database test
├── run.bat                 # Master run script
├── setup_db.bat            # Database setup
├── teardown_db.bat         # Database cleanup
└── requirements.txt        # Python dependencies
```

## Production Deployment

1. Set `DEBUG = False`
2. Change `SECRET_KEY`
3. Update `ALLOWED_HOSTS`
4. Switch to PostgreSQL database
5. Use Redis for Celery broker
6. Set up proper authentication
7. Configure CORS for your frontend domain
8. Use gunicorn or uwsgi for WSGI server
9. Set up nginx as reverse proxy
10. Configure HTTPS/SSL

## Support

For issues or questions:
- Check CLAUDE.md for architecture details
- Review CELERY_SETUP.md for background tasks
- Check django.log for server errors
- Run quick_test.py to verify setup
