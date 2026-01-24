# API Quick Reference

**Generated:** 2026-01-24 01:19:26

## AI & Chat

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/ai/process/` | - | - |
| `GET` | `/ai/insights/` | - | - |
| `POST` | `/ai/insights/` | - | - |
| `GET` | `/ai/patterns/` | - | - |
| `POST` | `/ai/patterns/` | - | - |
| `POST` | `/ai/suggestions/` | - | - |
| `PUT` | `/ai/suggestions/` | - | - |
| `POST` | `/ai/batch/` | - | - |
| `POST` | `/ai/stream/` | - | - |
| `POST` | `/ai/chat/` | - | - |
| `GET` | `/ai/chat/<str:session_id>/history/` | path: session_id | - |
| `DELETE` | `/ai/chat/<str:session_id>/history/` | path: session_id | - |
| `GET` | `/ai/suggestions/<str:session_id>/` | path: session_id | - |
| `POST` | `/ai/suggestions/<str:session_id>/` | path: session_id | - |
| `POST` | `/ai/intent/` | - | - |
| `POST` | `/ai/intent/execute/` | - | - |
| `GET` | `/ai/intent/list/` | - | - |
| `GET` | `/ai/intent/session/<str:session_id>/` | path: session_id | - |
| `DELETE` | `/ai/intent/session/<str:session_id>/` | path: session_id | - |
| `POST` | `/ai/extract/` | - | - |
| `POST` | `/ai/batch-create/` | - | - |

## Account

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/account/register/` | - | - |
| `POST` | `/account/login/` | - | - |
| `GET` | `/account/profile/` | - | - |
| `PATCH` | `/account/update/` | - | - |
| `POST` | `/account/change-password/` | - | - |
| `GET` | `/account/list/` | - | - |
| `DELETE` | `/account/delete/` | - | - |
| `POST` | `/webhooks/register/` | body: TaskSerializer | TaskSerializer |

## Analytics

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/analytics/user/` | - | - |
| `GET` | `/analytics/productivity/` | - | - |
| `POST` | `/analytics/productivity/` | - | - |
| `GET` | `/analytics/patterns/` | - | - |
| `POST` | `/analytics/patterns/` | - | - |
| `GET` | `/analytics/system/` | - | - |
| `GET` | `/analytics/export/` | - | - |
| `GET` | `/analytics/dashboard/` | - | - |
| `GET` | `/recurring/patterns/` | - | TaskSerializer |

## Collaboration

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/collaboration/sessions/` | - | - |
| `POST` | `/collaboration/sessions/` | - | - |
| `PUT` | `/collaboration/sessions/` | - | - |
| `DELETE` | `/collaboration/sessions/` | - | - |
| `GET` | `/collaboration/workspaces/` | - | - |
| `POST` | `/collaboration/workspaces/` | - | - |
| `GET` | `/collaboration/collaborators/` | - | - |
| `GET` | `/collaboration/invitations/` | - | - |
| `POST` | `/collaboration/invitations/` | - | - |
| `POST` | `/collaboration/invitations/<uuid:invitation_id>/respond/` | path: invitation_id | - |
| `DELETE` | `/collaboration/invitations/<uuid:invitation_id>/` | path: invitation_id | - |
| `PATCH` | `/collaboration/collaborations/<uuid:collaboration_id>/` | path: collaboration_id | - |
| `DELETE` | `/collaboration/collaborations/<uuid:collaboration_id>/` | path: collaboration_id | - |
| `GET` | `/collaboration/users/search/` | - | - |

## General

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/` | - | - |
| `GET` | `/<drf_format_suffix:format>` | path: format | - |
| `GET` | `/` | - | - |
| `GET` | `/<drf_format_suffix:format>` | path: format | - |

## Import/Export

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/import/csv/` | body: TaskSerializer | TaskSerializer |
| `POST` | `/import/json/` | body: TaskSerializer | TaskSerializer |
| `POST` | `/import/todoist/` | body: TaskSerializer | TaskSerializer |
| `GET` | `/export/csv/` | - | TaskSerializer |
| `GET` | `/export/json/` | - | TaskSerializer |
| `GET` | `/export/pdf/` | - | TaskSerializer |

## Notifications

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/notifications/preferences/` | - | - |
| `POST` | `/notifications/preferences/` | - | - |
| `PUT` | `/notifications/preferences/` | - | - |
| `GET` | `/notifications/history/` | - | - |
| `DELETE` | `/notifications/history/` | - | - |
| `POST` | `/notifications/mark-read/` | - | - |
| `PUT` | `/notifications/mark-read/` | - | - |

## Projects

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/^projects/` | - | ProjectSerializer |
| `POST` | `/^projects/` | body: ProjectSerializer | ProjectSerializer |
| `GET` | `/^projects\.(?P<format>[a-z0-9]+)/?` | path: format | ProjectSerializer |
| `POST` | `/^projects\.(?P<format>[a-z0-9]+)/?` | path: format; body: ProjectSerializer | ProjectSerializer |
| `GET` | `/^projects/check_name/` | - | ProjectSerializer |
| `GET` | `/^projects/check_name\.(?P<format>[a-z0-9]+)/?` | path: format | ProjectSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/` | path: pk | ProjectSerializer |
| `PUT` | `/^projects/(?P<pk>[^/.]+)/` | path: pk; body: ProjectSerializer | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/` | path: pk; body: ProjectSerializer | ProjectSerializer |
| `DELETE` | `/^projects/(?P<pk>[^/.]+)/` | path: pk | 204 No Content |
| `GET` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | ProjectSerializer |
| `PUT` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: ProjectSerializer | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: ProjectSerializer | ProjectSerializer |
| `DELETE` | `/^projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | 204 No Content |
| `GET` | `/^projects/(?P<pk>[^/.]+)/children/` | path: pk | ProjectSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/children\.(?P<format>[a-z0-9]+)/?` | path: pk, format | ProjectSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/independent/` | path: pk | ProjectSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/independent\.(?P<format>[a-z0-9]+)/?` | path: pk, format | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/make_independent/` | path: pk; body: ProjectSerializer | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/make_independent\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: ProjectSerializer | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/move/` | path: pk; body: ProjectSerializer | ProjectSerializer |
| `PATCH` | `/^projects/(?P<pk>[^/.]+)/move\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: ProjectSerializer | ProjectSerializer |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/` | path: project_pk | SectionSerializer |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/` | path: project_pk; body: SectionSerializer | SectionSerializer |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?` | path: project_pk, format | SectionSerializer |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections\.(?P<format>[a-z0-9]+)/?` | path: project_pk, format; body: SectionSerializer | SectionSerializer |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/check_name/` | path: project_pk | SectionSerializer |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/check_name\.(?P<format>[a-z0-9]+)/?` | path: project_pk, format | SectionSerializer |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed/` | path: project_pk; body: SectionSerializer | SectionSerializer |
| `POST` | `/^projects/(?P<project_pk>[^/.]+)/sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?` | path: project_pk, format; body: SectionSerializer | SectionSerializer |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | path: project_pk, pk | SectionSerializer |
| `PUT` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | path: project_pk, pk; body: SectionSerializer | SectionSerializer |
| `PATCH` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | path: project_pk, pk; body: SectionSerializer | SectionSerializer |
| `DELETE` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)/` | path: project_pk, pk | 204 No Content |
| `GET` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: project_pk, pk, format | SectionSerializer |
| `PUT` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: project_pk, pk, format; body: SectionSerializer | SectionSerializer |
| `PATCH` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: project_pk, pk, format; body: SectionSerializer | SectionSerializer |
| `DELETE` | `/^projects/(?P<project_pk>[^/.]+)/sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: project_pk, pk, format | 204 No Content |
| `GET` | `/collaboration/shared-projects/` | - | - |
| `POST` | `/collaboration/shared-projects/` | - | - |
| `PUT` | `/collaboration/shared-projects/` | - | - |
| `GET` | `/collaboration/projects/` | - | - |
| `POST` | `/collaboration/projects/join/` | - | - |
| `GET` | `/collaboration/projects/<uuid:project_id>/collaborators/` | path: project_id | - |
| `PATCH` | `/collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/` | path: project_id, collaborator_id | - |
| `DELETE` | `/collaboration/projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/` | path: project_id, collaborator_id | - |
| `GET` | `/collaboration/projects/<uuid:project_id>/access-id/` | path: project_id | - |
| `POST` | `/collaboration/projects/<uuid:project_id>/access-id/` | path: project_id | - |
| `POST` | `/collaboration/projects/<uuid:project_id>/transfer/` | path: project_id | - |
| `POST` | `/quick-actions/archive-project/<int:project_id>/` | path: project_id; body: ProjectSerializer | ProjectSerializer |
| `GET` | `/search/projects/` | - | ProjectSerializer |
| `GET` | `/templates/project/` | - | ProjectSerializer |

## Recurring

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/recurring/create/` | body: TaskSerializer | TaskSerializer |

## Scheduler

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/scheduler/generate/` | - | - |
| `POST` | `/scheduler/generate/` | - | - |
| `GET` | `/scheduler/preview/` | - | - |
| `POST` | `/scheduler/score/` | - | - |
| `GET` | `/scheduler/workload/` | - | - |

## Search

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/search/global/` | - | TaskSerializer |

## Sections

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/^sections/` | - | SectionSerializer |
| `POST` | `/^sections/` | body: SectionSerializer | SectionSerializer |
| `GET` | `/^sections\.(?P<format>[a-z0-9]+)/?` | path: format | SectionSerializer |
| `POST` | `/^sections\.(?P<format>[a-z0-9]+)/?` | path: format; body: SectionSerializer | SectionSerializer |
| `GET` | `/^sections/check_name/` | - | SectionSerializer |
| `GET` | `/^sections/check_name\.(?P<format>[a-z0-9]+)/?` | path: format | SectionSerializer |
| `POST` | `/^sections/get_or_create_completed/` | body: SectionSerializer | SectionSerializer |
| `POST` | `/^sections/get_or_create_completed\.(?P<format>[a-z0-9]+)/?` | path: format; body: SectionSerializer | SectionSerializer |
| `GET` | `/^sections/(?P<pk>[^/.]+)/` | path: pk | SectionSerializer |
| `PUT` | `/^sections/(?P<pk>[^/.]+)/` | path: pk; body: SectionSerializer | SectionSerializer |
| `PATCH` | `/^sections/(?P<pk>[^/.]+)/` | path: pk; body: SectionSerializer | SectionSerializer |
| `DELETE` | `/^sections/(?P<pk>[^/.]+)/` | path: pk | 204 No Content |
| `GET` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | SectionSerializer |
| `PUT` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: SectionSerializer | SectionSerializer |
| `PATCH` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: SectionSerializer | SectionSerializer |
| `DELETE` | `/^sections/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | 204 No Content |

## Tasks

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/^tasks/` | - | TaskSerializer |
| `POST` | `/^tasks/` | body: TaskSerializer | TaskSerializer |
| `GET` | `/^tasks\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `POST` | `/^tasks\.(?P<format>[a-z0-9]+)/?` | path: format; body: TaskSerializer | TaskSerializer |
| `GET` | `/^tasks/by_date_range/` | - | TaskSerializer |
| `GET` | `/^tasks/by_date_range\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/by_due_date/` | - | TaskSerializer |
| `GET` | `/^tasks/by_due_date\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/by_priority/` | - | TaskSerializer |
| `GET` | `/^tasks/by_priority\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/by_view/` | - | TaskSerializer |
| `GET` | `/^tasks/by_view\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/completed/` | - | TaskSerializer |
| `GET` | `/^tasks/completed\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/counts/` | - | TaskSerializer |
| `GET` | `/^tasks/counts\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/due_in_days/` | - | TaskSerializer |
| `GET` | `/^tasks/due_in_days\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/overdue/` | - | TaskSerializer |
| `GET` | `/^tasks/overdue\.(?P<format>[a-z0-9]+)/?` | path: format | TaskSerializer |
| `GET` | `/^tasks/(?P<pk>[^/.]+)/` | path: pk | TaskSerializer |
| `PUT` | `/^tasks/(?P<pk>[^/.]+)/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/` | path: pk; body: TaskSerializer | TaskSerializer |
| `DELETE` | `/^tasks/(?P<pk>[^/.]+)/` | path: pk | 204 No Content |
| `GET` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | TaskSerializer |
| `PUT` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `DELETE` | `/^tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` | path: pk, format | 204 No Content |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/completion/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/completion\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/make_unsectioned/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/make_unsectioned\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_project/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_project\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_section/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/move_to_section\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/total_completion/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/total_completion\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/views/` | path: pk; body: TaskSerializer | TaskSerializer |
| `PATCH` | `/^tasks/(?P<pk>[^/.]+)/views\.(?P<format>[a-z0-9]+)/?` | path: pk, format; body: TaskSerializer | TaskSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/task_count/` | path: pk | ProjectSerializer |
| `GET` | `/^projects/(?P<pk>[^/.]+)/task_count\.(?P<format>[a-z0-9]+)/?` | path: pk, format | ProjectSerializer |
| `POST` | `/ai/quick-task/` | - | - |
| `GET` | `/collaboration/tasks/<uuid:task_id>/collaborators/` | path: task_id | - |
| `GET` | `/collaboration/shared-tasks/` | - | - |
| `GET` | `/collaboration/tasks/<uuid:task_id>/assign/` | path: task_id | - |
| `POST` | `/collaboration/tasks/<uuid:task_id>/assign/` | path: task_id | - |
| `POST` | `/quick-actions/complete-task/<int:task_id>/` | path: task_id; body: TaskSerializer | TaskSerializer |
| `POST` | `/quick-actions/star-task/<int:task_id>/` | path: task_id; body: TaskSerializer | TaskSerializer |
| `POST` | `/bulk/tasks/update/` | body: TaskSerializer | TaskSerializer |
| `POST` | `/bulk/tasks/delete/` | body: TaskSerializer | TaskSerializer |
| `POST` | `/bulk/tasks/move/` | body: TaskSerializer | TaskSerializer |
| `GET` | `/search/tasks/` | - | TaskSerializer |
| `GET` | `/templates/task/` | - | TaskSerializer |
| `POST` | `/recurring/pause/<int:task_id>/` | path: task_id; body: TaskSerializer | TaskSerializer |
| `POST` | `/time/start/<int:task_id>/` | path: task_id; body: TaskSerializer | TaskSerializer |
| `POST` | `/time/stop/<int:task_id>/` | path: task_id; body: TaskSerializer | TaskSerializer |

## Templates

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/templates/save/` | body: TaskSerializer | TaskSerializer |

## Time Tracking

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `POST` | `/time/log/` | body: TaskSerializer | TaskSerializer |
| `GET` | `/time/report/` | - | TaskSerializer |

## Webhooks

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| `GET` | `/webhooks/list/` | - | TaskSerializer |
| `DELETE` | `/webhooks/delete/<str:webhook_id>/` | path: webhook_id | 204 No Content |
