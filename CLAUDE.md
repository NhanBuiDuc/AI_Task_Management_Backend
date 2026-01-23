# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Database Management
- **Fresh database setup**: `setup_db.bat` - Removes old database, creates migrations, applies them
- **Database teardown**: `teardown_db.bat` - Clean removal of database and migration files
- **Run migrations**: `python manage.py migrate`
- **Create migrations**: `python manage.py makemigrations`
- **Create superuser**: `python manage.py createsuperuser`

### Development Server
- **Start server**: `python manage.py runserver 0.0.0.0:8000` - Runs on port 8000, accessible from network
- **Full environment**: `run.bat` - Orchestrates database setup, server start, and API testing
  - Options: `--no-tests`, `--auto-teardown`, `--keep-server`, `--help`
- **Django admin**: http://localhost:8000/admin/
- **API base**: http://localhost:8000/

### Celery Background Tasks
- **Start Celery worker**: `celery -A jarvis_backend worker --loglevel=info`
- **Start Celery beat scheduler**: `celery -A jarvis_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Test categorization**: `python manage.py test_categorize_tasks` - Manual test of task categorization
- **Setup periodic tasks**: `python manage.py setup_periodic_tasks`

### Testing
- **Run API tests**: `python test_apis.py` - Tests all API endpoints
- **Run Django tests**: `python manage.py test`
- **Test agent integration**: `python test_agent_integration.py`

## Tech Stack & Architecture

**Framework**: Django 5.2.6 with Django REST Framework 3.15.2
**Database**: SQLite (development), ready for PostgreSQL (production)
**Task Queue**: Celery 5.4.0 with Redis broker (or DB for testing)
**WebSockets**: Django Channels 4.2.0 with channels-redis
**AI Integration**: LangChain with local Ollama (llama3.2 model) for task processing
**Scheduled Tasks**: Celery Beat with django-celery-beat for periodic task categorization

## Core Architecture

### Data Models (tasks_api/models.py)

The application uses a hierarchical task management system with automatic view categorization:

**BaseModel** - Abstract base with UUID primary keys and timestamps
- All models inherit from this for consistent ID and timestamp handling

**Project** - Hierarchical project organization
- Self-referential parent/child relationships for nested projects
- Tracks icon, color, task counts, and children status
- Properties: `parent_id`, `task_count`, `has_children`, `is_independent()`

**Section** - Task grouping within projects or global views
- Can belong to a project or be global (Inbox sections)
- Unique constraint on (project, name) combinations
- Many-to-many relationship with views via `SectionView`

**Task** - Core task entity with smart view management
- Priority: low, medium, high, urgent, emergency
- Views: calendar, inbox, today, upcoming, overdue, project
- Repeat patterns: every day, every week, every month, every year
- **CRITICAL**: Tasks have both `completed` (checkable) and `totally_completed` (archived)
- Many-to-many relationship with views via `TaskView`

**Auto-Categorization Logic** (Task.calculate_views_from_due_date):
- Tasks automatically calculate their views based on `due_date` and `project_id`
- Inbox tasks (no project): Include `inbox` view
- Project tasks: Include `project` view
- Due today: Add `today` view
- Due within 14 days: Add `upcoming` view
- Past due: Add `overdue` view
- Views update automatically on save via `update_task_views()`

### URL Structure (tasks_api/urls.py)

The API uses nested routers for hierarchical resources:

**Main Resources**:
- `/tasks/` - Task CRUD with extensive custom actions
- `/projects/` - Project management with hierarchy support
- `/sections/` - Section management with view filtering
- `/labels/` - Task labeling system
- `/task-views/` - Custom view management

**Nested Resources**:
- `/projects/{id}/sections/` - Sections within a project
- `/tasks/{id}/comments/` - Task comments
- `/tasks/{id}/attachments/` - File attachments
- `/tasks/{id}/activities/` - Activity logs

**Feature Endpoints**:
- `/ai/` - AI agent processing, insights, patterns, suggestions, batch operations, streaming
- `/analytics/` - User analytics, productivity reports, task patterns, system metrics, exports, dashboard
- `/collaboration/` - Sessions, shared projects, workspaces, collaborators
- `/notifications/` - Preferences, history, mark-read
- `/search/` - Task, project, and global search
- `/bulk/` - Bulk update, delete, move operations
- `/time/` - Time tracking with start/stop/log/report

**WebSocket Endpoints**:
- `ws/tasks/` - Real-time task updates (TaskManagementConsumer)
- `ws/collaboration/` - Collaborative planning (CollaborativePlanningConsumer)
- `ws/dashboard/` - Live dashboard updates (DashboardConsumer)

### ViewSet Actions (tasks_api/views.py)

**TaskViewSet** - Extensive custom actions:
- `overdue()` - GET tasks with due_date < now
- `due_in_days(days)` - GET tasks due in 3/7/14 days
- `by_view(view)` - GET tasks by view (inbox, today, upcoming, project, overdue)
- `by_priority(priority)` - GET tasks by priority level
- `by_due_date(due_date)` - GET tasks for specific date (Today view)
- `by_date_range(start_date, end_date)` - GET tasks in range (Upcoming view)
- `completed()` - GET all totally_completed tasks
- `counts(today_date)` - GET task counts for all navigation views
- `move_to_project(project_id)` - PATCH move task to project
- `move_to_section(section_id)` - PATCH move task to section
- `make_unsectioned()` - PATCH remove section assignment
- `completion(completed)` - PATCH update completed status
- `total_completion(totally_completed)` - PATCH archive task
- `views(current_view)` - PATCH update task views manually

**ProjectViewSet** - Project hierarchy management:
- `check_name(name, parent_id)` - GET check if name exists
- `independent()` - GET check if project is independent
- `task_count()` - GET count of tasks in project
- `children()` - GET sub-projects
- `move(parent_id)` - PATCH move project to parent
- `make_independent()` - PATCH remove parent relationship

**SectionViewSet** - Section management:
- Query params: `project_id` (filter by project, use 'null' for global), `current_view` (filter by view)
- `check_name(project_id, name)` - GET check if name exists within scope
- `get_or_create_completed(project_id)` - POST get/create Completed section

### Serializers (tasks_api/serializers.py)

**Key Patterns**:
- All IDs converted to strings (UUID → string) in `to_representation()`
- Separate serializers for read (full) vs write (validation) operations
- `TaskSerializer` uses `piority` field (intentional typo matching frontend)
- `current_view` computed from many-to-many `TaskView` relationships
- `CreateTaskSerializer` and `CreateSectionSerializer` handle foreign keys as UUIDs

### AI Agent System (tasks_api/agents/task_agent.py)

**TaskAgent** - LangChain-based natural language task processor:
- Uses local Ollama (llama3.2 model) running on http://localhost:11434
- Processes user intentions: "learn Chinese daily, work on thesis, go to gym"
- Extracts structured tasks with:
  - Category: work, education, health, personal, social, finance
  - Priority: 1-5 scale
  - Frequency: daily, weekly, monthly, once
  - Duration: estimated minutes
  - Time preference: morning, afternoon, evening, anytime
  - Energy level: high, medium, low
  - Deadline urgency: urgent, normal, flexible

**Key Methods**:
- `process_intentions(user_input, context)` - Main processing pipeline
- `validate_ollama_connection()` - Check if Ollama is running
- `_fallback_processing(user_input)` - Rule-based fallback when AI unavailable
- Returns: `TaskExtractionOutput` with tasks, insights, total_estimated_time, feasibility_score

**AI Endpoints** (tasks_api/views_agent.py):
- `/ai/process/` - Process natural language intentions
- `/ai/insights/` - Get AI-generated insights
- `/ai/patterns/` - Analyze task patterns
- `/ai/suggestions/` - Get smart suggestions
- `/ai/batch/` - Batch process multiple tasks
- `/ai/stream/` - Streaming AI responses

### Celery Periodic Tasks (jarvis_backend/celery.py)

**Automatic Task Categorization** - Server-side background processing:

**Scheduled Tasks**:
1. `check-and-update-overdue-tasks` - Every 5 minutes
   - Updates overdue task views
   - Adds `overdue` view to past-due tasks

2. `categorize-tasks-by-due-date` - Every 10 minutes
   - Full recategorization of all tasks
   - Updates `today`, `upcoming`, `inbox`, `project` views based on due dates
   - Critical for automatic view management

3. `daily-section-maintenance` - Daily at midnight (00:00 UTC)
   - Creates/maintains Today sections
   - Cleans up stale view assignments

**Task Categorization Rules** (see CELERY_SETUP.md):
- Inbox tasks: `project_id = null` → `["inbox"]` view
- Project tasks: `project_id != null` → `["project"]` view
- Due today: Add `["today"]` view
- Due within 14 days (this week + next week): Add `["upcoming"]` view
- Past due: Add `["overdue"]` view

### WebSocket Consumers (tasks_api/consumers.py)

**Real-time Communication**:
- `TaskManagementConsumer` - Live task updates, notifications
- `CollaborativePlanningConsumer` - Multi-user collaboration features
- `DashboardConsumer` - Real-time dashboard metrics

### Analytics System (tasks_api/views_analytics.py)

**Endpoints**:
- `/analytics/user/` - User-specific metrics and insights
- `/analytics/productivity/` - Productivity reports and trends
- `/analytics/patterns/` - Task completion patterns analysis
- `/analytics/system/` - System-wide metrics
- `/analytics/export/` - Export analytics data
- `/analytics/dashboard/` - Consolidated dashboard data

Backed by MongoDB (`tasks_api/utils/mongodb.py`) for flexible analytics storage.

## Critical Implementation Notes

### View Management System
- **NEVER manually set views** - Tasks auto-calculate views on save
- **Two completion states**:
  - `completed = True` - Task checked off, stays in view, moves to Completed section
  - `totally_completed = True` - Task archived, removed from all views, section detached
- **View filtering**: Use `TaskView.objects.filter(view='inbox')` to get task IDs, then query tasks
- **Inbox special case**: Inbox = tasks with 'inbox' view BUT NOT 'project' view

### Task Form Dropdown Structure
**2-Level Tree** for project/section selection:
- **Level 1**: 📥 Inbox (root), 📁 Project Name (root)
- **Level 2**: Section Name (indented, `pl-6`, gray text)

**Selection Behavior**:
- Root Inbox → `project_id=null, section_id=null`
- Root Project → `project_id=<id>, section_id=null`
- Inbox Section → `project_id=null, section_id=<id>`
- Project Section → `project_id=<parent_id>, section_id=<id>`

### Date-Based View Boundaries
**Today View**: Single day section (refreshes daily)
- Shows tasks where `due_date = today_date`

**Upcoming View**: 14-day rolling window (2 weekly sections)
- "This Week": `today_date` to `today_date + 7 days`
- "Next Week": `today_date + 8 days` to `today_date + 14 days`

**Counts API** (`/tasks/counts/`):
- Accepts optional `today_date` parameter to match frontend logic
- Returns counts for: inbox, today, upcoming, overdue, completed, projects

### CORS Configuration
- Allowed origins: localhost:3000-3006 (frontend dev servers)
- Allowed hosts: localhost, 127.0.0.1, 172.22.64.61
- Credentials enabled for session handling

### Database Configuration
- **Development**: SQLite (db.sqlite3)
- **Production**: PostgreSQL (psycopg2-binary in requirements, commented)
- **Celery**: Can use SQLite broker for testing or Redis for production

## Common Development Tasks

### Adding a New Task Endpoint
1. Add method to `TaskViewSet` in `tasks_api/views.py`
2. Use `@action(detail=False/True, methods=['get/post/patch'])` decorator
3. Update `tasks_api/urls.py` if needed (nested routers handle most cases)
4. Test with `test_apis.py`

### Creating Custom Management Commands
1. Create file in `tasks_api/management/commands/`
2. Inherit from `BaseCommand`
3. Implement `handle()` method
4. Run with `python manage.py <command_name>`

### Adding Periodic Celery Tasks
1. Define task in `tasks_api/tasks.py` with `@shared_task` decorator
2. Add schedule to `jarvis_backend/celery.py` beat_schedule
3. Register in Django admin or run `python manage.py setup_periodic_tasks`

### Modifying Models
1. Update model in `tasks_api/models.py`
2. Run `python manage.py makemigrations`
3. Review migration file
4. Run `python manage.py migrate`
5. Update corresponding serializer in `tasks_api/serializers.py`

### Testing AI Agent
1. Ensure Ollama is running: Check http://localhost:11434/api/tags
2. Verify llama3.2 model is installed: `ollama list`
3. Test with `python test_agent_integration.py`
4. Monitor logs in `agent.log`

### WebSocket Development
1. Consumers defined in `tasks_api/consumers.py`
2. Routing in `websocket_urlpatterns` (tasks_api/urls.py)
3. Connect to `ws://localhost:8000/ws/<endpoint>/`
4. Test with WebSocket client or browser console

## Environment Setup

### Required Services
- **Python 3.x** with packages from requirements.txt
- **Redis** (optional, for Celery with production broker)
- **Ollama** (optional, for AI features) - http://localhost:11434

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Fresh database setup
setup_db.bat

# Start development server
python manage.py runserver 0.0.0.0:8000

# (Optional) Start Celery services
redis-server
celery -A jarvis_backend worker --loglevel=info
celery -A jarvis_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# (Optional) Install Ollama and llama3.2
# Download from https://ollama.ai
ollama pull llama3.2
```

## Logging & Debugging

- **Agent logs**: `agent.log` - AI processing and LangChain verbose output
- **Django logs**: Console output from runserver
- **Celery logs**: Worker and beat process outputs
- **Debug mode**: `DEBUG = True` in settings (not for production)
- **Logging config**: Configured in `settings.py` for `tasks_api.agents` logger

## API Design Patterns

### Consistent Response Format
- Success: `{ "id": "...", "name": "...", ... }` or `[ {...}, {...} ]`
- Error: `{ "error": "Error message" }` with appropriate HTTP status
- Counts: `{ "inbox": 5, "today": 3, ... }`

### Query Parameter Conventions
- `project_id` - Filter by project, use 'null' string for null values
- `current_view` - Filter by view name (inbox, today, upcoming, etc.)
- `due_date` - ISO date string (YYYY-MM-DD)
- `start_date`, `end_date` - Date range queries
- `today_date` - Optional override for "today" calculations (testing/timezone)

### HTTP Methods
- **GET** - Read operations, list, retrieve
- **POST** - Create new resources
- **PATCH** - Partial update (preferred over PUT)
- **DELETE** - Remove resources
- Custom actions use appropriate method based on semantics

## Security Notes

- **Development secret key**: Change `SECRET_KEY` in production
- **CORS**: Restricted to specific origins (localhost variants)
- **Authentication**: Currently `AllowAny` - implement auth for production
- **CSRF**: Enabled via middleware
- **OpenAI API key**: Placeholder in settings, replace for production AI features
