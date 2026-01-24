# JARVIS Task Management API Blueprint

**Generated:** 2026-01-24 01:19:25

This document provides a comprehensive overview of all API endpoints, their inputs, and outputs.

## Table of Contents

- [AI & Chat](#ai-and-chat) (15 endpoints)
- [Account](#account) (8 endpoints)
- [Analytics](#analytics) (7 endpoints)
- [Collaboration](#collaboration) (8 endpoints)
- [General](#general) (4 endpoints)
- [Import/Export](#import/export) (6 endpoints)
- [Notifications](#notifications) (3 endpoints)
- [Projects](#projects) (32 endpoints)
- [Recurring](#recurring) (1 endpoints)
- [Scheduler](#scheduler) (4 endpoints)
- [Search](#search) (1 endpoints)
- [Sections](#sections) (8 endpoints)
- [Tasks](#tasks) (48 endpoints)
- [Templates](#templates) (1 endpoints)
- [Time Tracking](#time-tracking) (2 endpoints)
- [Webhooks](#webhooks) (2 endpoints)

---

## AI & Chat

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/process/` | Process natural language intentions into structure |
| `GET` | `/ai/insights/` | Get AI-generated insights and recommendations. |
| `POST` | `/ai/insights/` | Get AI-generated insights and recommendations. |
| `GET` | `/ai/patterns/` | Analyze user patterns and provide insights. |
| `POST` | `/ai/patterns/` | Analyze user patterns and provide insights. |
| `POST` | `/ai/suggestions/` | Generate AI-powered task suggestions for drag & dr |
| `PUT` | `/ai/suggestions/` | Generate AI-powered task suggestions for drag & dr |
| `POST` | `/ai/batch/` | Create multiple tasks from selected AI suggestions |
| `POST` | `/ai/stream/` | Handle streaming AI responses for real-time intera |
| `POST` | `/ai/chat/` | Conversation-based AI chat for task management. |
| `GET` | `/ai/chat/<str:session_id>/history/` | Get conversation history for a session. |
| `DELETE` | `/ai/chat/<str:session_id>/history/` | Get conversation history for a session. |
| `GET` | `/ai/suggestions/<str:session_id>/` | Manage pending task suggestions from AI conversati |
| `POST` | `/ai/suggestions/<str:session_id>/` | Manage pending task suggestions from AI conversati |
| `POST` | `/ai/intent/` | Intent-based AI chat for task management. |
| `POST` | `/ai/intent/execute/` | Execute a specific intent with given params. |
| `GET` | `/ai/intent/list/` | List all available intents. |
| `GET` | `/ai/intent/session/<str:session_id>/` | Manage intent chat sessions. |
| `DELETE` | `/ai/intent/session/<str:session_id>/` | Manage intent chat sessions. |
| `POST` | `/ai/extract/` | Extract tasks from natural language WITHOUT auto-e |
| `POST` | `/ai/batch-create/` | Create multiple tasks from a pre-extracted list. |

### Detailed Documentation

#### `POST` /ai/process/

> Process natural language intentions into structured tasks.

---

#### `GET` /ai/insights/

> Get AI-generated insights and recommendations.

---

#### `POST` /ai/insights/

> Get AI-generated insights and recommendations.

---

#### `GET` /ai/patterns/

> Analyze user patterns and provide insights.

---

#### `POST` /ai/patterns/

> Analyze user patterns and provide insights.

---

#### `POST` /ai/suggestions/

> Generate AI-powered task suggestions for drag & drop interface.

---

#### `PUT` /ai/suggestions/

> Generate AI-powered task suggestions for drag & drop interface.

---

#### `POST` /ai/batch/

> Create multiple tasks from selected AI suggestions.

---

#### `POST` /ai/stream/

> Handle streaming AI responses for real-time interaction.

---

#### `POST` /ai/chat/

> Conversation-based AI chat for task management.

---

#### `GET` /ai/chat/<str:session_id>/history/

> Get conversation history for a session.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `DELETE` /ai/chat/<str:session_id>/history/

> Get conversation history for a session.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `GET` /ai/suggestions/<str:session_id>/

> Manage pending task suggestions from AI conversations.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `POST` /ai/suggestions/<str:session_id>/

> Manage pending task suggestions from AI conversations.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `POST` /ai/intent/

> Intent-based AI chat for task management.

---

#### `POST` /ai/intent/execute/

> Execute a specific intent with given params.

---

#### `GET` /ai/intent/list/

> List all available intents.

---

#### `GET` /ai/intent/session/<str:session_id>/

> Manage intent chat sessions.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `DELETE` /ai/intent/session/<str:session_id>/

> Manage intent chat sessions.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Required path parameter |

---

#### `POST` /ai/extract/

> Extract tasks from natural language WITHOUT auto-executing.

---

#### `POST` /ai/batch-create/

> Create multiple tasks from a pre-extracted list.

---

## Account

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/account/register/` | Register a new account. |
| `POST` | `/account/login/` | Authenticate an account and return account details |
| `GET` | `/account/profile/` | Get account profile by user_id. |
| `PATCH` | `/account/update/` | Update account profile. |
| `POST` | `/account/change-password/` | Change account password. |
| `GET` | `/account/list/` | List all accounts (for admin/development purposes) |
| `DELETE` | `/account/delete/` | Delete an account (soft delete by setting is_activ |
| `POST` | `/webhooks/register/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `POST` /account/register/

> Register a new account.

---

#### `POST` /account/login/

> Authenticate an account and return account details.

---

#### `GET` /account/profile/

> Get account profile by user_id.

---

#### `PATCH` /account/update/

> Update account profile.

---

#### `POST` /account/change-password/

> Change account password.

---

#### `GET` /account/list/

> List all accounts (for admin/development purposes).

---

#### `DELETE` /account/delete/

> Delete an account (soft delete by setting is_active=False).

---

#### `POST` /webhooks/register/

> ViewSet for Task model with all required endpoints.

**Action:** `register_webhook`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

## Analytics

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/user/` | Get comprehensive analytics for the authenticated  |
| `GET` | `/analytics/productivity/` | Generate detailed productivity reports with recomm |
| `POST` | `/analytics/productivity/` | Generate detailed productivity reports with recomm |
| `GET` | `/analytics/patterns/` | Analyze and retrieve task patterns using AI. |
| `POST` | `/analytics/patterns/` | Analyze and retrieve task patterns using AI. |
| `GET` | `/analytics/system/` | System-wide metrics for monitoring and admin dashb |
| `GET` | `/analytics/export/` | Export analytics data in various formats. |
| `GET` | `/analytics/dashboard/` | Aggregate dashboard data for frontend display. |
| `GET` | `/recurring/patterns/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `GET` /analytics/user/

> Get comprehensive analytics for the authenticated user.

---

#### `GET` /analytics/productivity/

> Generate detailed productivity reports with recommendations.

---

#### `POST` /analytics/productivity/

> Generate detailed productivity reports with recommendations.

---

#### `GET` /analytics/patterns/

> Analyze and retrieve task patterns using AI.

---

#### `POST` /analytics/patterns/

> Analyze and retrieve task patterns using AI.

---

#### `GET` /analytics/system/

> System-wide metrics for monitoring and admin dashboard.

---

#### `GET` /analytics/export/

> Export analytics data in various formats.

---

#### `GET` /analytics/dashboard/

> Aggregate dashboard data for frontend display.

---

#### `GET` /recurring/patterns/

> ViewSet for Task model with all required endpoints.

**Action:** `recurring_patterns`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

## Collaboration

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/collaboration/sessions/` | Manage real-time collaboration sessions for planni |
| `POST` | `/collaboration/sessions/` | Manage real-time collaboration sessions for planni |
| `PUT` | `/collaboration/sessions/` | Manage real-time collaboration sessions for planni |
| `DELETE` | `/collaboration/sessions/` | Manage real-time collaboration sessions for planni |
| `GET` | `/collaboration/workspaces/` | Manage team workspaces for larger collaboration. |
| `POST` | `/collaboration/workspaces/` | Manage team workspaces for larger collaboration. |
| `GET` | `/collaboration/collaborators/` | Manage and search for collaborators. |
| `GET` | `/collaboration/invitations/` | Manage task collaboration invitations. |
| `POST` | `/collaboration/invitations/` | Manage task collaboration invitations. |
| `POST` | `/collaboration/invitations/<uuid:invitation_id>/respond/` | Respond to a task invitation (accept/decline). |
| `DELETE` | `/collaboration/invitations/<uuid:invitation_id>/` | Cancel a sent invitation. |
| `PATCH` | `/collaboration/collaborations/<uuid:collaboration_id>/` | Update or remove a collaboration. |
| `DELETE` | `/collaboration/collaborations/<uuid:collaboration_id>/` | Update or remove a collaboration. |
| `GET` | `/collaboration/users/search/` | Search for users to invite for collaboration. |

### Detailed Documentation

#### `GET` /collaboration/sessions/

> Manage real-time collaboration sessions for planning and brainstorming.

---

#### `POST` /collaboration/sessions/

> Manage real-time collaboration sessions for planning and brainstorming.

---

#### `PUT` /collaboration/sessions/

> Manage real-time collaboration sessions for planning and brainstorming.

---

#### `DELETE` /collaboration/sessions/

> Manage real-time collaboration sessions for planning and brainstorming.

---

#### `GET` /collaboration/workspaces/

> Manage team workspaces for larger collaboration.

---

#### `POST` /collaboration/workspaces/

> Manage team workspaces for larger collaboration.

---

#### `GET` /collaboration/collaborators/

> Manage and search for collaborators.

---

#### `GET` /collaboration/invitations/

> Manage task collaboration invitations.

---

#### `POST` /collaboration/invitations/

> Manage task collaboration invitations.

---

#### `POST` /collaboration/invitations/<uuid:invitation_id>/respond/

> Respond to a task invitation (accept/decline).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `invitation_id` | uuid | Required path parameter |

---

#### `DELETE` /collaboration/invitations/<uuid:invitation_id>/

> Cancel a sent invitation.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `invitation_id` | uuid | Required path parameter |

---

#### `PATCH` /collaboration/collaborations/<uuid:collaboration_id>/

> Update or remove a collaboration.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `collaboration_id` | uuid | Required path parameter |

---

#### `DELETE` /collaboration/collaborations/<uuid:collaboration_id>/

> Update or remove a collaboration.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `collaboration_id` | uuid | Required path parameter |

---

#### `GET` /collaboration/users/search/

> Search for users to invite for collaboration.

---

## General

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | The default basic root view for DefaultRouter |
| `GET` | `/<drf_format_suffix:format>` | The default basic root view for DefaultRouter |
| `GET` | `/` | The default basic root view for DefaultRouter |
| `GET` | `/<drf_format_suffix:format>` | The default basic root view for DefaultRouter |

### Detailed Documentation

#### `GET` /

> The default basic root view for DefaultRouter

---

#### `GET` /<drf_format_suffix:format>

> The default basic root view for DefaultRouter

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | drf_format_suffix | Required path parameter |

---

#### `GET` /

> The default basic root view for DefaultRouter

---

#### `GET` /<drf_format_suffix:format>

> The default basic root view for DefaultRouter

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | drf_format_suffix | Required path parameter |

---

## Import/Export

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/import/csv/` | ViewSet for Task model with all required endpoints |
| `POST` | `/import/json/` | ViewSet for Task model with all required endpoints |
| `POST` | `/import/todoist/` | ViewSet for Task model with all required endpoints |
| `GET` | `/export/csv/` | ViewSet for Task model with all required endpoints |
| `GET` | `/export/json/` | ViewSet for Task model with all required endpoints |
| `GET` | `/export/pdf/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `POST` /import/csv/

> ViewSet for Task model with all required endpoints.

**Action:** `import_csv`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /import/json/

> ViewSet for Task model with all required endpoints.

**Action:** `import_json`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /import/todoist/

> ViewSet for Task model with all required endpoints.

**Action:** `import_todoist`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /export/csv/

> ViewSet for Task model with all required endpoints.

**Action:** `export_csv`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /export/json/

> ViewSet for Task model with all required endpoints.

**Action:** `export_json`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /export/pdf/

> ViewSet for Task model with all required endpoints.

**Action:** `export_pdf`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

## Notifications

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notifications/preferences/` | Manage user notification preferences. |
| `POST` | `/notifications/preferences/` | Manage user notification preferences. |
| `PUT` | `/notifications/preferences/` | Manage user notification preferences. |
| `GET` | `/notifications/history/` | View and manage notification history. |
| `DELETE` | `/notifications/history/` | View and manage notification history. |
| `POST` | `/notifications/mark-read/` | Mark notifications as read/unread. |
| `PUT` | `/notifications/mark-read/` | Mark notifications as read/unread. |

### Detailed Documentation

#### `GET` /notifications/preferences/

> Manage user notification preferences.

---

#### `POST` /notifications/preferences/

> Manage user notification preferences.

---

#### `PUT` /notifications/preferences/

> Manage user notification preferences.

---

#### `GET` /notifications/history/

> View and manage notification history.

---

#### `DELETE` /notifications/history/

> View and manage notification history.

---

#### `POST` /notifications/mark-read/

> Mark notifications as read/unread.

---

#### `PUT` /notifications/mark-read/

> Mark notifications as read/unread.

---

## Projects

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/^projects/` | ViewSet for Project model with all required endpoi |
| `POST` | `/^projects/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `POST` | `/^projects\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/check_name/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/check_name\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/` | ViewSet for Project model with all required endpoi |
| `PUT` | `/^projects/(?P<pk>[^/.]+)/` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/` | ViewSet for Project model with all required endpoi |
| `DELETE` | `/^projects/(?P<pk>[^/.]+)/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `PUT` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `DELETE` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/children/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/children\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/independent/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/independent\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/make_independent/` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/make_independent\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/move/` | ViewSet for Project model with all required endpoi |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/move\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/` | ViewSet for Section model with all required endpoi |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/check_name/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/check_name\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed/` | ViewSet for Section model with all required endpoi |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `PUT` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `PATCH` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `DELETE` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `PUT` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `PATCH` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `DELETE` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `GET` | `/collaboration/shared-projects/` | Manage shared projects and team collaboration. |
| `POST` | `/collaboration/shared-projects/` | Manage shared projects and team collaboration. |
| `PUT` | `/collaboration/shared-projects/` | Manage shared projects and team collaboration. |
| `GET` | `/collaboration/projects/` | Get all collaborative projects for the current use |
| `POST` | `/collaboration/projects/join/` | Join a project using access_id. |
| `GET` | `/collaboration/projects/<uuid:project_id>/collaborators/` | Manage collaborators for a project. |
| `PATCH` | `/collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/` | Update or remove a project collaborator. |
| `DELETE` | `/collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/` | Update or remove a project collaborator. |
| `GET` | `/collaboration/projects/<uuid:project_id>/access-id/` | Manage project access_id. |
| `POST` | `/collaboration/projects/<uuid:project_id>/access-id/` | Manage project access_id. |
| `POST` | `/collaboration/projects/<uuid:project_id>/transfer/` | Transfer project ownership to another collaborator |
| `POST` | `/quick-actions/archive-project/<int:project_id>/` | ViewSet for Project model with all required endpoi |
| `GET` | `/search/projects/` | ViewSet for Project model with all required endpoi |
| `GET` | `/templates/project/` | ViewSet for Project model with all required endpoi |

### Detailed Documentation

#### `GET` /^projects/

> ViewSet for Project model with all required endpoints.

**Action:** `list`

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^projects/

> ViewSet for Project model with all required endpoints.

**Action:** `create`

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `GET` /^projects\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `list`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^projects\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `create`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `GET` /^projects/check_name/

> ViewSet for Project model with all required endpoints.

**Action:** `check_name`

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/check_name\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `check_name`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<pk>[^/.]+)/

> ViewSet for Project model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^projects/(?P<pk>[^/.]+)/

> ViewSet for Project model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)/

> ViewSet for Project model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `DELETE` /^projects/(?P<pk>[^/.]+)/

> ViewSet for Project model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `ProjectSerializer`

---

#### `GET` /^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `DELETE` /^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

---

#### `GET` /^projects/(?P<pk>[^/.]+)/children/

> ViewSet for Project model with all required endpoints.

**Action:** `children`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<pk>[^/.]+)/children\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `children`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<pk>[^/.]+)/independent/

> ViewSet for Project model with all required endpoints.

**Action:** `independent`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<pk>[^/.]+)/independent\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `independent`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)/make_independent/

> ViewSet for Project model with all required endpoints.

**Action:** `make_independent`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)/make_independent\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `make_independent`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)/move/

> ViewSet for Project model with all required endpoints.

**Action:** `move`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `PATCH` /^projects/(?P<pk>[^/.]+)/move\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `move`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections/

> ViewSet for Section model with all required endpoints.

**Action:** `list`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^projects/(?P<project_pk>[^/.]+)/sections/

> ViewSet for Section model with all required endpoints.

**Action:** `create`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `list`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `create`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections/check_name/

> ViewSet for Section model with all required endpoints.

**Action:** `check_name`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections/check_name\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `check_name`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed/

> ViewSet for Section model with all required endpoints.

**Action:** `get_or_create_completed`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `POST` /^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `get_or_create_completed`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `PATCH` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `DELETE` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |

**Response:** `SectionSerializer`

---

#### `GET` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `PATCH` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `DELETE` /^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_pk` | string | Required path parameter |
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

---

#### `GET` /collaboration/shared-projects/

> Manage shared projects and team collaboration.

---

#### `POST` /collaboration/shared-projects/

> Manage shared projects and team collaboration.

---

#### `PUT` /collaboration/shared-projects/

> Manage shared projects and team collaboration.

---

#### `GET` /collaboration/projects/

> Get all collaborative projects for the current user.

---

#### `POST` /collaboration/projects/join/

> Join a project using access_id.

---

#### `GET` /collaboration/projects/<uuid:project_id>/collaborators/

> Manage collaborators for a project.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |

---

#### `PATCH` /collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/

> Update or remove a project collaborator.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |
| `collaborator_id` | uuid | Required path parameter |

---

#### `DELETE` /collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/

> Update or remove a project collaborator.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |
| `collaborator_id` | uuid | Required path parameter |

---

#### `GET` /collaboration/projects/<uuid:project_id>/access-id/

> Manage project access_id.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |

---

#### `POST` /collaboration/projects/<uuid:project_id>/access-id/

> Manage project access_id.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |

---

#### `POST` /collaboration/projects/<uuid:project_id>/transfer/

> Transfer project ownership to another collaborator.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | uuid | Required path parameter |

---

#### `POST` /quick-actions/archive-project/<int:project_id>/

> ViewSet for Project model with all required endpoints.

**Action:** `archive`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | int | Required path parameter |

**Request Body:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

**Response:** `ProjectSerializer`

---

#### `GET` /search/projects/

> ViewSet for Project model with all required endpoints.

**Action:** `search`

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /templates/project/

> ViewSet for Project model with all required endpoints.

**Action:** `templates`

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

## Recurring

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/recurring/create/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `POST` /recurring/create/

> ViewSet for Task model with all required endpoints.

**Action:** `create_recurring`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

## Scheduler

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/scheduler/generate/` | Generate an optimized schedule from tasks. |
| `POST` | `/scheduler/generate/` | Generate an optimized schedule from tasks. |
| `GET` | `/scheduler/preview/` | Preview schedule for a single day without persisti |
| `POST` | `/scheduler/score/` | Calculate urgency score for a single task. |
| `GET` | `/scheduler/workload/` | Analyze workload distribution across the planning  |

### Detailed Documentation

#### `GET` /scheduler/generate/

> Generate an optimized schedule from tasks.

---

#### `POST` /scheduler/generate/

> Generate an optimized schedule from tasks.

---

#### `GET` /scheduler/preview/

> Preview schedule for a single day without persisting.

---

#### `POST` /scheduler/score/

> Calculate urgency score for a single task.

---

#### `GET` /scheduler/workload/

> Analyze workload distribution across the planning horizon.

---

## Search

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/search/global/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `GET` /search/global/

> ViewSet for Task model with all required endpoints.

**Action:** `global_search`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

## Sections

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/^sections/` | ViewSet for Section model with all required endpoi |
| `POST` | `/^sections/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^sections\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `POST` | `/^sections\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `GET` | `/^sections/check_name/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^sections/check_name\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `POST` | `/^sections/get_or_create_completed/` | ViewSet for Section model with all required endpoi |
| `POST` | `/^sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `GET` | `/^sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `PUT` | `/^sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `PATCH` | `/^sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `DELETE` | `/^sections/(?P<pk>[^/.]+)/` | ViewSet for Section model with all required endpoi |
| `GET` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `PUT` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `PATCH` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |
| `DELETE` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Section model with all required endpoi |

### Detailed Documentation

#### `GET` /^sections/

> ViewSet for Section model with all required endpoints.

**Action:** `list`

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^sections/

> ViewSet for Section model with all required endpoints.

**Action:** `create`

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^sections\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `list`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^sections\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `create`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^sections/check_name/

> ViewSet for Section model with all required endpoints.

**Action:** `check_name`

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^sections/check_name\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `check_name`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^sections/get_or_create_completed/

> ViewSet for Section model with all required endpoints.

**Action:** `get_or_create_completed`

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `POST` /^sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `get_or_create_completed`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `GET` /^sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `PATCH` /^sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `DELETE` /^sections/(?P<pk>[^/.]+)/

> ViewSet for Section model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `SectionSerializer`

---

#### `GET` /^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `PATCH` /^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `SectionSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

**Response:** `SectionSerializer`

---

#### `DELETE` /^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Section model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `SectionSerializer`

---

## Tasks

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/^tasks/` | ViewSet for Task model with all required endpoints |
| `POST` | `/^tasks/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `POST` | `/^tasks\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_date_range/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_date_range\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_due_date/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_due_date\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_priority/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_priority\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_view/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/by_view\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/completed/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/completed\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/counts/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/counts\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/due_in_days/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/due_in_days\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/overdue/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/overdue\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/(?P<pk>[^/.]+)/` | ViewSet for Task model with all required endpoints |
| `PUT` | `/^tasks/(?P<pk>[^/.]+)/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/` | ViewSet for Task model with all required endpoints |
| `DELETE` | `/^tasks/(?P<pk>[^/.]+)/` | ViewSet for Task model with all required endpoints |
| `GET` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PUT` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `DELETE` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/completion/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/completion\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/make_unsectioned/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/make_unsectioned\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_project/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_project\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_section/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_section\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/total_completion/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/total_completion\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/views/` | ViewSet for Task model with all required endpoints |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/views\.(?P<format>[a-z0-9]+)/?` | ViewSet for Task model with all required endpoints |
| `GET` | `/^projects/(?P<pk>[^/.]+)/task_count/` | ViewSet for Project model with all required endpoi |
| `GET` | `/^projects/(?P<pk>[^/.]+)/task_count\.(?P<format>[a-z0-9]+)/?` | ViewSet for Project model with all required endpoi |
| `POST` | `/ai/quick-task/` | Quick single-task creation with smart defaults. |
| `GET` | `/collaboration/tasks/<uuid:task_id>/collaborators/` | Manage collaborators for a task. |
| `GET` | `/collaboration/shared-tasks/` | List tasks shared with the user. |
| `GET` | `/collaboration/tasks/<uuid:task_id>/assign/` | Assign users to a task. |
| `POST` | `/collaboration/tasks/<uuid:task_id>/assign/` | Assign users to a task. |
| `POST` | `/quick-actions/complete-task/<int:task_id>/` | ViewSet for Task model with all required endpoints |
| `POST` | `/quick-actions/star-task/<int:task_id>/` | ViewSet for Task model with all required endpoints |
| `POST` | `/bulk/tasks/update/` | ViewSet for Task model with all required endpoints |
| `POST` | `/bulk/tasks/delete/` | ViewSet for Task model with all required endpoints |
| `POST` | `/bulk/tasks/move/` | ViewSet for Task model with all required endpoints |
| `GET` | `/search/tasks/` | ViewSet for Task model with all required endpoints |
| `GET` | `/templates/task/` | ViewSet for Task model with all required endpoints |
| `POST` | `/recurring/pause/<int:task_id>/` | ViewSet for Task model with all required endpoints |
| `POST` | `/time/start/<int:task_id>/` | ViewSet for Task model with all required endpoints |
| `POST` | `/time/stop/<int:task_id>/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `GET` /^tasks/

> ViewSet for Task model with all required endpoints.

**Action:** `list`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^tasks/

> ViewSet for Task model with all required endpoints.

**Action:** `create`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /^tasks\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `list`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /^tasks\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `create`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /^tasks/by_date_range/

> ViewSet for Task model with all required endpoints.

**Action:** `by_date_range`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_date_range\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `by_date_range`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_due_date/

> ViewSet for Task model with all required endpoints.

**Action:** `by_due_date`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_due_date\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `by_due_date`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_priority/

> ViewSet for Task model with all required endpoints.

**Action:** `by_priority`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_priority\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `by_priority`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_view/

> ViewSet for Task model with all required endpoints.

**Action:** `by_view`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/by_view\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `by_view`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/completed/

> ViewSet for Task model with all required endpoints.

**Action:** `completed`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/completed\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `completed`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/counts/

> ViewSet for Task model with all required endpoints.

**Action:** `counts`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/counts\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `counts`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/due_in_days/

> ViewSet for Task model with all required endpoints.

**Action:** `due_in_days`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/due_in_days\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `due_in_days`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/overdue/

> ViewSet for Task model with all required endpoints.

**Action:** `overdue`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/overdue\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `overdue`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^tasks/(?P<pk>[^/.]+)/

> ViewSet for Task model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^tasks/(?P<pk>[^/.]+)/

> ViewSet for Task model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/

> ViewSet for Task model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `DELETE` /^tasks/(?P<pk>[^/.]+)/

> ViewSet for Task model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `TaskSerializer`

---

#### `GET` /^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `retrieve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `PUT` /^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `partial_update`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `DELETE` /^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `destroy`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/completion/

> ViewSet for Task model with all required endpoints.

**Action:** `completion`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/completion\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `completion`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/make_unsectioned/

> ViewSet for Task model with all required endpoints.

**Action:** `make_unsectioned`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/make_unsectioned\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `make_unsectioned`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/move_to_project/

> ViewSet for Task model with all required endpoints.

**Action:** `move_to_project`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/move_to_project\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `move_to_project`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/move_to_section/

> ViewSet for Task model with all required endpoints.

**Action:** `move_to_section`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/move_to_section\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `move_to_section`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/total_completion/

> ViewSet for Task model with all required endpoints.

**Action:** `total_completion`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/total_completion\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `total_completion`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/views/

> ViewSet for Task model with all required endpoints.

**Action:** `views`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `PATCH` /^tasks/(?P<pk>[^/.]+)/views\.(?P<format>[a-z0-9]+)/?

> ViewSet for Task model with all required endpoints.

**Action:** `views`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /^projects/(?P<pk>[^/.]+)/task_count/

> ViewSet for Project model with all required endpoints.

**Action:** `task_count`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /^projects/(?P<pk>[^/.]+)/task_count\.(?P<format>[a-z0-9]+)/?

> ViewSet for Project model with all required endpoints.

**Action:** `task_count`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | string | Required path parameter |
| `format` | string | Required path parameter |

**Response:** `ProjectSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | CharField | No | (read-only)  |
| `taskCount` | IntegerField | No | (read-only)  |
| `hasChildren` | BooleanField | No | (read-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |
| `access_id` | CharField | No | (read-only) Unique shareable code for joining the project |
| `is_collaborative` | BooleanField | No | Whether the project is in collaboration mode |
| `collaborator_count` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /ai/quick-task/

> Quick single-task creation with smart defaults.

---

#### `GET` /collaboration/tasks/<uuid:task_id>/collaborators/

> Manage collaborators for a task.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | uuid | Required path parameter |

---

#### `GET` /collaboration/shared-tasks/

> List tasks shared with the user.

---

#### `GET` /collaboration/tasks/<uuid:task_id>/assign/

> Assign users to a task.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | uuid | Required path parameter |

---

#### `POST` /collaboration/tasks/<uuid:task_id>/assign/

> Assign users to a task.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | uuid | Required path parameter |

---

#### `POST` /quick-actions/complete-task/<int:task_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `complete`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | int | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /quick-actions/star-task/<int:task_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `star`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | int | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /bulk/tasks/update/

> ViewSet for Task model with all required endpoints.

**Action:** `bulk_update`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /bulk/tasks/delete/

> ViewSet for Task model with all required endpoints.

**Action:** `bulk_delete`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /bulk/tasks/move/

> ViewSet for Task model with all required endpoints.

**Action:** `bulk_move`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /search/tasks/

> ViewSet for Task model with all required endpoints.

**Action:** `search`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `GET` /templates/task/

> ViewSet for Task model with all required endpoints.

**Action:** `templates`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `POST` /recurring/pause/<int:task_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `pause_recurring`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | int | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /time/start/<int:task_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `start_timer`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | int | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `POST` /time/stop/<int:task_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `stop_timer`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | int | Required path parameter |

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

## Templates

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/templates/save/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `POST` /templates/save/

> ViewSet for Task model with all required endpoints.

**Action:** `save_as_template`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

## Time Tracking

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/time/log/` | ViewSet for Task model with all required endpoints |
| `GET` | `/time/report/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `POST` /time/log/

> ViewSet for Task model with all required endpoints.

**Action:** `log_time`

**Request Body:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

**Response:** `TaskSerializer`

---

#### `GET` /time/report/

> ViewSet for Task model with all required endpoints.

**Action:** `time_report`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

## Webhooks

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/webhooks/list/` | ViewSet for Task model with all required endpoints |
| `DELETE` | `/webhooks/delete/<str:webhook_id>/` | ViewSet for Task model with all required endpoints |

### Detailed Documentation

#### `GET` /webhooks/list/

> ViewSet for Task model with all required endpoints.

**Action:** `list_webhooks`

**Response:** `TaskSerializer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | CharField | No | (read-only)  |
| `section_id` | CharField | No | (read-only)  |
| `due_date` | DateField | Yes |  |
| `completed` | BooleanField | No |  |
| `totally_completed` | BooleanField | No |  |
| `current_view` | SerializerMethodField | No | (read-only)  |
| `piority` | CharField | Yes |  |
| `reminder_date` | DateTimeField | No |  |
| `completed_date` | DateTimeField | No | (read-only)  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |

---

#### `DELETE` /webhooks/delete/<str:webhook_id>/

> ViewSet for Task model with all required endpoints.

**Action:** `delete_webhook`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `webhook_id` | str | Required path parameter |

**Response:** `TaskSerializer`

---
