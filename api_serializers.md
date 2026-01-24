# API Serializers (Data Models)

**Generated:** 2026-01-24 01:19:26

## Account Serializers

### AccountLoginSerializer

> Serializer for account login.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username_or_email` | CharField | Yes |  |
| `password` | CharField | Yes | (write-only)  |

---

### AccountRegisterSerializer

> Serializer for account registration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | CharField | Yes |  |
| `email` | EmailField | Yes |  |
| `password` | CharField | Yes | (write-only)  |
| `display_name` | CharField | No |  |

---

### AccountSerializer

> Serializer for Account model (read operations).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `username` | CharField | Yes |  |
| `email` | EmailField | Yes |  |
| `display_name` | CharField | No |  |
| `avatar_url` | URLField | No |  |
| `is_active` | BooleanField | No |  |
| `last_login` | DateTimeField | No | (read-only)  |
| `timezone` | CharField | No |  |
| `theme` | CharField | No |  |
| `created_at` | DateTimeField | No | (read-only)  |

---

### AccountUpdateSerializer

> Serializer for updating account profile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | CharField | No |  |
| `avatar_url` | URLField | No |  |
| `timezone` | CharField | No |  |
| `theme` | CharField | No |  |

---

## Collaboration Serializers

### InvitationResponseSerializer

> Serializer for responding to an invitation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | ChoiceField | Yes |  Choices: [accept, decline] |

---

### UpdateCollaborationPermissionSerializer

> Serializer for updating collaboration permission.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `permission` | ChoiceField | Yes |  Choices: [view, edit, admin] |

---

## Other Serializers

### ChangePasswordSerializer

> Serializer for changing password.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_password` | CharField | Yes | (write-only)  |
| `new_password` | CharField | Yes | (write-only)  |

---

### CollaboratorSerializer

> Serializer for collaborator info (subset of Account).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `username` | CharField | No | (read-only)  |
| `email` | EmailField | No | (read-only)  |
| `display_name` | CharField | No | (read-only)  |
| `avatar_url` | URLField | No | (read-only)  |

---

### TransferOwnershipSerializer

> Serializer for transferring project ownership.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_owner_id` | UUIDField | Yes |  |

---

## Project Serializers

### CreateProjectInvitationSerializer

> Serializer for creating project invitations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | UUIDField | Yes |  |
| `invitee_id` | UUIDField | No |  |
| `invitee_email` | EmailField | No |  |
| `role` | ChoiceField | No |  Choices: [moderator, collaborator] |
| `message` | CharField | No |  |

---

### CreateProjectSerializer

> Serializer for creating projects.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | UUIDField | No | (write-only)  |
| `name` | CharField | Yes |  |
| `parent_id` | UUIDField | No | (write-only)  |
| `icon` | CharField | No |  |
| `color` | CharField | No |  |

---

### JoinProjectSerializer

> Serializer for joining a project via access_id.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_id` | CharField | Yes |  |

---

### ProjectCollaborationSerializer

> Serializer for ProjectCollaboration model with role-based access.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `project_id` | CharField | No | (read-only)  |
| `project_name` | CharField | No | (read-only)  |
| `project_owner` | CollaboratorSerializer | No | (read-only)  |
| `collaborator_id` | CharField | No | (read-only)  |
| `collaborator` | CollaboratorSerializer | No | (read-only)  |
| `role` | ChoiceField | No | Role determines permissions within the project Choices: [moderator, collaborator] |
| `is_active` | BooleanField | No |  |
| `joined_at` | DateTimeField | No | (read-only)  |
| `created_at` | DateTimeField | No | (read-only)  |

---

### ProjectInvitationSerializer

> Serializer for ProjectInvitation model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `project_id` | CharField | No | (read-only)  |
| `project_name` | CharField | No | (read-only)  |
| `invited_by` | CollaboratorSerializer | No | (read-only)  |
| `invitee` | CollaboratorSerializer | No | (read-only)  |
| `invitee_email` | EmailField | No | Email for inviting non-registered users |
| `role` | ChoiceField | No |  Choices: [moderator, collaborator] |
| `status` | ChoiceField | No | (read-only)  Choices: [pending, accepted, declined, expired, cancelled] |
| `message` | CharField | No | Optional message from the inviter |
| `expires_at` | DateTimeField | No | When the invitation expires |
| `responded_at` | DateTimeField | No | (read-only)  |
| `created_at` | DateTimeField | No | (read-only)  |

---

### ProjectSerializer

> Serializer for Project model matching ProjectItem interface.

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

### UpdateProjectRoleSerializer

> Serializer for updating collaborator role in a project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | ChoiceField | Yes |  Choices: [moderator, collaborator] |

---

## Section Serializers

### CreateSectionSerializer

> Serializer for creating sections.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | UUIDField | No | (write-only)  |
| `name` | CharField | Yes |  |
| `project_id` | UUIDField | No | (write-only)  |
| `current_view` | ListField | No |  |

---

### SectionSerializer

> Serializer for Section model matching SectionItem interface.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `user_id` | CharField | No | (read-only)  |
| `name` | CharField | Yes |  |
| `project_id` | CharField | No | (read-only)  |
| `current_view` | SerializerMethodField | No | (read-only)  |

---

## Task Serializers

### AssignTaskSerializer

> Serializer for assigning users to a task.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids` | ListField | Yes |  |

---

### CreateTaskInvitationSerializer

> Serializer for creating task invitations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | UUIDField | Yes |  |
| `invitee_id` | UUIDField | No |  |
| `invitee_email` | EmailField | No |  |
| `permission` | ChoiceField | No |  Choices: [view, edit, admin] |
| `message` | CharField | No |  |

---

### CreateTaskSerializer

> Serializer for creating tasks with required fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | UUIDField | No | (write-only)  |
| `name` | CharField | Yes |  |
| `description` | CharField | No |  |
| `project_id` | UUIDField | No | (write-only)  |
| `section_id` | UUIDField | No | (write-only)  |
| `due_date` | DateField | Yes |  |
| `piority` | CharField | No |  |
| `reminder_date` | DateTimeField | No |  |
| `duration_in_minutes` | IntegerField | No | Duration in minutes |
| `repeat` | ChoiceField | No | Repeat pattern for the task Choices: [every day, every week, every month, every year] |

---

### SharedTaskSerializer

> Serializer for tasks that are shared with the user.

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
| `owner` | CollaboratorSerializer | No | (read-only)  |
| `my_role` | SerializerMethodField | No | (read-only)  |
| `assigned_to_ids` | SerializerMethodField | No | (read-only)  |
| `is_assigned_to_me` | SerializerMethodField | No | (read-only)  |

---

### TaskCollaborationSerializer

> Serializer for TaskCollaboration model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `task_id` | CharField | No | (read-only)  |
| `task_name` | CharField | No | (read-only)  |
| `owner_id` | CharField | No | (read-only)  |
| `owner` | CollaboratorSerializer | No | (read-only)  |
| `collaborator_id` | CharField | No | (read-only)  |
| `collaborator` | CollaboratorSerializer | No | (read-only)  |
| `permission` | ChoiceField | No |  Choices: [view, edit, admin] |
| `is_active` | BooleanField | No |  |
| `accepted_at` | DateTimeField | No | (read-only)  |
| `created_at` | DateTimeField | No | (read-only)  |

---

### TaskInvitationSerializer

> Serializer for TaskInvitation model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUIDField | No | (read-only)  |
| `task_id` | CharField | No | (read-only)  |
| `task_name` | CharField | No | (read-only)  |
| `invited_by_id` | CharField | No | (read-only)  |
| `invited_by` | CollaboratorSerializer | No | (read-only)  |
| `invitee_id` | CharField | No | (read-only)  |
| `invitee` | CollaboratorSerializer | No | (read-only)  |
| `invitee_email` | EmailField | No | Email for inviting non-registered users |
| `permission` | ChoiceField | No |  Choices: [view, edit, admin] |
| `status` | ChoiceField | No | (read-only)  Choices: [pending, accepted, declined, expired, cancelled] |
| `message` | CharField | No | Optional message from the inviter |
| `expires_at` | DateTimeField | No | When the invitation expires |
| `responded_at` | DateTimeField | No | (read-only) When the invitee responded to the invitation |
| `created_at` | DateTimeField | No | (read-only)  |

---

### TaskSerializer

> Serializer for Task model matching TaskItem interface.

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
