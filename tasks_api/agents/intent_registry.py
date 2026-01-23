# File: tasks_api/agents/intent_registry.py
"""
Intent-Action Registry: Maps user intents to safe, predefined API actions.

The LLM predicts an intent_id, and we execute the corresponding handler.
This is safer and more efficient than having LLM generate arbitrary actions.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from django.utils import timezone


class ActionType(str, Enum):
    """Type of database action"""
    READ = "read"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    COMPLETE = "complete"


class IntentCategory(str, Enum):
    """Categories for organizing intents"""
    QUERY = "query"           # Reading/listing tasks
    CREATE = "create"         # Adding new tasks
    MODIFY = "modify"         # Updating tasks
    COMPLETE = "complete"     # Marking tasks done
    DELETE = "delete"         # Removing tasks
    SCHEDULE = "schedule"     # Scheduling operations
    ANALYTICS = "analytics"   # Stats and insights


@dataclass
class IntentAction:
    """Defines a single intent-to-action mapping"""
    id: str                              # Unique intent ID
    description: str                     # Human-readable description
    action_type: ActionType              # Type of action
    category: IntentCategory             # Category for grouping
    patterns: List[str]                  # Example user patterns (for LLM context)
    requires_params: List[str] = field(default_factory=list)  # Required extracted params
    optional_params: List[str] = field(default_factory=list)  # Optional params
    safe: bool = True                    # Is this a safe operation?


# =============================================================================
# INTENT REGISTRY - All allowed intents mapped to actions
# =============================================================================

INTENT_REGISTRY: Dict[str, IntentAction] = {
    # =========================================================================
    # QUERY INTENTS - Read operations (safe)
    # =========================================================================

    "tasks-today-list": IntentAction(
        id="tasks-today-list",
        description="List all tasks due today",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "what tasks do I have today",
            "show today's tasks",
            "today's schedule",
            "what's on my plate today",
            "what is my schedule",
            "show my schedule",
            "my schedule",
            "show my agenda",
            "my agenda",
            "what do I have today",
            "today tasks",
            "tasks for today",
            "what's today",
            "show today",
            "my plan for today",
            "today's plan"
        ]
    ),

    "tasks-today-count": IntentAction(
        id="tasks-today-count",
        description="Count how many tasks are due today",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "how many tasks today",
            "count today's tasks",
            "number of tasks for today"
        ]
    ),

    "tasks-all-list": IntentAction(
        id="tasks-all-list",
        description="List all active tasks",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "show all my tasks",
            "list all tasks",
            "what are all my tasks",
            "show all tasks",
            "all tasks",
            "list everything",
            "show everything",
            "all my tasks",
            "every task"
        ]
    ),

    "tasks-overdue-list": IntentAction(
        id="tasks-overdue-list",
        description="List overdue tasks",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "show overdue tasks",
            "what's overdue",
            "late tasks",
            "missed deadlines"
        ]
    ),

    "tasks-upcoming-list": IntentAction(
        id="tasks-upcoming-list",
        description="List upcoming tasks (next 7 days)",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "upcoming tasks",
            "what's coming up",
            "next week tasks",
            "tasks this week"
        ]
    ),

    "tasks-inbox-list": IntentAction(
        id="tasks-inbox-list",
        description="List inbox tasks (no project)",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "show inbox",
            "inbox tasks",
            "unsorted tasks"
        ]
    ),

    "task-search": IntentAction(
        id="task-search",
        description="Search for a specific task by name",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "find task about X",
            "search for X task",
            "where is my X task",
            "find X",
            "search X",
            "look for X",
            "find tasks about X",
            "search for X",
            "find task X"
        ],
        requires_params=["search_term"]
    ),

    "task-due-date-query": IntentAction(
        id="task-due-date-query",
        description="Check when a specific task is due",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "when is X due",
            "due date for X",
            "when should I finish X"
        ],
        requires_params=["task_name"]
    ),

    "tasks-by-priority": IntentAction(
        id="tasks-by-priority",
        description="List tasks by priority level",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "high priority tasks",
            "urgent tasks",
            "important tasks"
        ],
        optional_params=["priority"]
    ),

    "tasks-by-project": IntentAction(
        id="tasks-by-project",
        description="List tasks in a specific project",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "tasks in project X",
            "show X project tasks",
            "what's in project X"
        ],
        requires_params=["project_name"]
    ),

    "projects-list": IntentAction(
        id="projects-list",
        description="List all projects",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "show my projects",
            "list projects",
            "what projects do I have"
        ]
    ),

    # =========================================================================
    # CREATE INTENTS - Insert operations
    # =========================================================================

    "task-create-simple": IntentAction(
        id="task-create-simple",
        description="Create a simple task with just a title",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add task X",
            "create task X",
            "new task X",
            "remind me to X",
            "insert task X",
            "insert a task to X",
            "make a task X",
            "I want to X",
            "I need to X",
            "I should X",
            "I have to X",
            "I must X",
            "I gotta X",
            "gonna X",
            "need to X",
            "want to X"
        ],
        requires_params=["title"]
    ),

    "task-create-with-date": IntentAction(
        id="task-create-with-date",
        description="Create a task with a due date or time",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add task X for tomorrow",
            "create task X due Monday",
            "add X by next week",
            "insert task X on today",
            "insert a task for me at 10pm today to X",
            "insert a tasks for me on 10 pm today to X",
            "add task X at 3pm",
            "schedule X for 10am tomorrow",
            "remind me at 5pm to X",
            "X at 10pm",
            "X tomorrow",
            "X on Monday",
            "X by Friday",
            "do X today",
            "do X tomorrow",
            "need to X today",
            "need to X by tomorrow"
        ],
        requires_params=["title"],
        optional_params=["due_date", "due_time"]
    ),

    "task-create-with-time": IntentAction(
        id="task-create-with-time",
        description="Create a task with specific time (no date)",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add task X at 3pm",
            "create meeting at 2pm",
            "insert task at 9am to X"
        ],
        requires_params=["title"],
        optional_params=["due_time"]
    ),

    "task-create-with-priority": IntentAction(
        id="task-create-with-priority",
        description="Create a task with priority level",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add urgent task X",
            "create high priority X",
            "important: do X"
        ],
        requires_params=["title", "priority"]
    ),

    "task-create-in-project": IntentAction(
        id="task-create-in-project",
        description="Create a task in a specific project",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add task X to project Y",
            "create X in Y project"
        ],
        requires_params=["title", "project_name"]
    ),

    "task-create-recurring": IntentAction(
        id="task-create-recurring",
        description="Create a recurring task",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add daily task X",
            "create weekly X",
            "remind me every day to X"
        ],
        requires_params=["title", "frequency"]
    ),

    "tasks-create-multiple": IntentAction(
        id="tasks-create-multiple",
        description="Create multiple tasks at once",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "add tasks: X, Y, Z",
            "create multiple tasks",
            "add X and Y and Z"
        ],
        requires_params=["tasks"]  # List of task titles
    ),

    "project-create": IntentAction(
        id="project-create",
        description="Create a new project",
        action_type=ActionType.INSERT,
        category=IntentCategory.CREATE,
        patterns=[
            "create project X",
            "new project X",
            "add project X"
        ],
        requires_params=["name"]
    ),

    # =========================================================================
    # MODIFY INTENTS - Update operations
    # =========================================================================

    "task-update-due-date": IntentAction(
        id="task-update-due-date",
        description="Change a task's due date",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "move X to tomorrow",
            "reschedule X to Monday",
            "change due date of X",
            "reschedule X",
            "move X to",
            "change X due date",
            "set X due date to",
            "change due date of X to",
            "move task X to",
            "reschedule task X"
        ],
        requires_params=["task_name", "new_due_date"]
    ),

    "task-update-priority": IntentAction(
        id="task-update-priority",
        description="Change a task's priority",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "make X high priority",
            "set X to urgent",
            "lower priority of X",
            "change priority of X",
            "set X priority to",
            "make X urgent",
            "make X low priority",
            "change X to high priority",
            "set priority of X to",
            "prioritize X"
        ],
        requires_params=["task_name", "new_priority"]
    ),

    "task-update-title": IntentAction(
        id="task-update-title",
        description="Rename a task",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "rename X to Y",
            "change X task name to Y"
        ],
        requires_params=["task_name", "new_title"]
    ),

    "task-move-to-project": IntentAction(
        id="task-move-to-project",
        description="Move a task to a different project",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "move X to project Y",
            "put X in project Y"
        ],
        requires_params=["task_name", "project_name"]
    ),

    "task-postpone": IntentAction(
        id="task-postpone",
        description="Postpone a task by a duration",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "postpone X by 1 day",
            "delay X by a week",
            "push X back 2 days",
            "postpone X",
            "delay X",
            "push back X",
            "defer X",
            "move X back",
            "push X back by",
            "delay task X by"
        ],
        requires_params=["task_name", "postpone_days"]
    ),

    "tasks-bulk-postpone": IntentAction(
        id="tasks-bulk-postpone",
        description="Postpone all tasks by a duration",
        action_type=ActionType.UPDATE,
        category=IntentCategory.MODIFY,
        patterns=[
            "postpone all tasks by 1 day",
            "delay everything by a week",
            "push all tasks back"
        ],
        requires_params=["postpone_days"],
        optional_params=["filter"]  # e.g., "today's tasks"
    ),

    # =========================================================================
    # COMPLETE INTENTS - Mark done operations
    # =========================================================================

    "task-complete": IntentAction(
        id="task-complete",
        description="Mark a task as complete",
        action_type=ActionType.COMPLETE,
        category=IntentCategory.COMPLETE,
        patterns=[
            "mark X as done",
            "complete X",
            "finish X",
            "X is done",
            "I finished X",
            "I completed X",
            "done with X",
            "check off X",
            "finished X",
            "completed X",
            "I did X",
            "X is complete",
            "X is finished"
        ],
        requires_params=["task_name"]
    ),

    "tasks-complete-multiple": IntentAction(
        id="tasks-complete-multiple",
        description="Mark multiple tasks as complete",
        action_type=ActionType.COMPLETE,
        category=IntentCategory.COMPLETE,
        patterns=[
            "mark X, Y, Z as done",
            "complete X and Y",
            "finish X, Y tasks"
        ],
        requires_params=["task_names"]
    ),

    # =========================================================================
    # DELETE INTENTS - Remove operations
    # =========================================================================

    "task-delete": IntentAction(
        id="task-delete",
        description="Delete a task",
        action_type=ActionType.DELETE,
        category=IntentCategory.DELETE,
        patterns=[
            "delete task X",
            "remove X",
            "cancel X task"
        ],
        requires_params=["task_name"],
        safe=False
    ),

    "tasks-delete-completed": IntentAction(
        id="tasks-delete-completed",
        description="Delete all completed tasks",
        action_type=ActionType.DELETE,
        category=IntentCategory.DELETE,
        patterns=[
            "clear completed tasks",
            "remove done tasks",
            "delete finished tasks"
        ],
        safe=False
    ),

    # =========================================================================
    # ANALYTICS INTENTS - Stats and insights
    # =========================================================================

    "stats-summary": IntentAction(
        id="stats-summary",
        description="Get task summary/statistics",
        action_type=ActionType.READ,
        category=IntentCategory.ANALYTICS,
        patterns=[
            "show my stats",
            "task summary",
            "how am I doing",
            "productivity stats"
        ]
    ),

    "stats-completion-rate": IntentAction(
        id="stats-completion-rate",
        description="Get completion rate",
        action_type=ActionType.READ,
        category=IntentCategory.ANALYTICS,
        patterns=[
            "what's my completion rate",
            "how many tasks did I finish",
            "completion statistics"
        ]
    ),

    # =========================================================================
    # SPECIAL INTENTS - Clarification and chat
    # =========================================================================

    "clarify-ambiguous": IntentAction(
        id="clarify-ambiguous",
        description="Request clarification for ambiguous input",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "vague statements",
            "incomplete requests",
            "ambiguous input"
        ]
    ),

    "chat-general": IntentAction(
        id="chat-general",
        description="General chat not related to specific task action",
        action_type=ActionType.READ,
        category=IntentCategory.QUERY,
        patterns=[
            "general questions",
            "greetings",
            "small talk"
        ]
    ),
}


def get_intent_by_id(intent_id: str) -> Optional[IntentAction]:
    """Get an intent by its ID"""
    return INTENT_REGISTRY.get(intent_id)


def get_intents_by_category(category: IntentCategory) -> List[IntentAction]:
    """Get all intents in a category"""
    return [
        intent for intent in INTENT_REGISTRY.values()
        if intent.category == category
    ]


def get_intents_by_action_type(action_type: ActionType) -> List[IntentAction]:
    """Get all intents of a specific action type"""
    return [
        intent for intent in INTENT_REGISTRY.values()
        if intent.action_type == action_type
    ]


def get_safe_intents() -> List[IntentAction]:
    """Get all safe intents (no destructive operations)"""
    return [
        intent for intent in INTENT_REGISTRY.values()
        if intent.safe
    ]


def build_intent_prompt_context() -> str:
    """
    Build a compact prompt context listing all available intents.
    Used to help LLM predict the correct intent_id.
    """
    lines = ["AVAILABLE INTENTS:"]

    # Group by category
    for category in IntentCategory:
        category_intents = get_intents_by_category(category)
        if not category_intents:
            continue

        lines.append(f"\n[{category.value.upper()}]")
        for intent in category_intents:
            params = ""
            if intent.requires_params:
                params = f" (needs: {', '.join(intent.requires_params)})"
            lines.append(f"- {intent.id}: {intent.description}{params}")

    return "\n".join(lines)


def build_compact_intent_list() -> str:
    """Build intent list with short descriptions for LLM context"""
    lines = []
    # Group key intents by category for clarity
    categories = {
        "LIST": ["tasks-today-list", "tasks-all-list", "tasks-overdue-list", "tasks-upcoming-list", "tasks-inbox-list", "projects-list"],
        "CREATE": ["task-create-simple", "task-create-with-date", "tasks-create-multiple"],
        "COMPLETE": ["task-complete", "tasks-complete-multiple"],
        "UPDATE": ["task-update-due-date", "task-update-priority", "task-postpone"],
        "DELETE": ["task-delete"],
        "OTHER": ["task-search", "stats-summary", "chat-general", "clarify-ambiguous"]
    }

    for cat, intent_ids in categories.items():
        cat_intents = []
        for iid in intent_ids:
            intent = INTENT_REGISTRY.get(iid)
            if intent:
                params = f"({','.join(intent.requires_params)})" if intent.requires_params else ""
                cat_intents.append(f"{intent.id}{params}")
        if cat_intents:
            lines.append(f"{cat}:{','.join(cat_intents)}")

    return "\n".join(lines)


# =============================================================================
# INTENT PREDICTION OUTPUT
# =============================================================================

@dataclass
class PredictedIntent:
    """Result of intent prediction from LLM"""
    intent_id: str
    confidence: float = 1.0
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
    user_message: Optional[str] = None  # Response message to user


@dataclass
class IntentExecutionResult:
    """Result of executing an intent"""
    success: bool
    intent_id: str
    action_type: ActionType
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: Optional[str] = None
