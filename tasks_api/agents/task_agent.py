# tasks_api/agents/task_agent.py
"""
Efficient Task Agent with conversation support and task suggestions.
Handles natural language for CRUD operations on tasks with minimal tokens.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
import json
import logging
import requests
import uuid
from datetime import datetime, timedelta
from enum import Enum

# LangChain imports
LANGCHAIN_AVAILABLE = False
try:
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    OllamaLLM = None
    PromptTemplate = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class ActionType(str, Enum):
    """Task actions that can be performed"""
    READ = "read"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    COMPLETE = "complete"


class ResponseType(str, Enum):
    """Type of agent response"""
    ACTIONS = "actions"          # Has database actions to execute
    CLARIFY = "clarify"          # Needs clarification from user
    SUGGEST = "suggest"          # Has task suggestions for approval
    CHAT = "chat"                # General conversation response


# =============================================================================
# Pydantic Models
# =============================================================================

class TaskAction(BaseModel):
    """Single task action with all necessary data"""
    action: ActionType
    task_id: Optional[str] = None  # Required for update/delete/complete/read
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    due_date: Optional[str] = None  # YYYY-MM-DD
    due_time: Optional[str] = None  # HH:MM
    duration: Optional[int] = None  # minutes
    frequency: Optional[str] = None
    # For read queries
    query_type: Optional[str] = None  # "count", "list", "due_date", "details"
    query_filter: Optional[str] = None  # "today", "overdue", "all", specific task name


class TaskSuggestion(BaseModel):
    """Task suggestion waiting for user approval"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    category: str = "personal"
    priority: int = 3
    due_date: Optional[str] = None
    duration: int = 30
    frequency: str = "once"
    reason: str = ""  # Why this task is suggested


class AgentResponse(BaseModel):
    """Complete response from the agent"""
    type: ResponseType
    message: str  # User-friendly message
    actions: List[TaskAction] = Field(default_factory=list)
    suggestions: List[TaskSuggestion] = Field(default_factory=list)
    clarify_options: List[str] = Field(default_factory=list)  # Options for clarification
    context_key: Optional[str] = None  # To track conversation context


class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Maintains conversation state"""
    session_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    pending_suggestions: List[TaskSuggestion] = Field(default_factory=list)
    awaiting_clarification: bool = False
    clarification_topic: Optional[str] = None


# =============================================================================
# Legacy Models (for backward compatibility)
# =============================================================================

class TaskItem(BaseModel):
    """Legacy task item for backward compatibility"""
    title: str
    category: str = "personal"
    priority: int = 3
    frequency: str = "once"
    duration: int = 30
    time_preference: str = "anytime"
    energy_level: str = "medium"
    due_date: Optional[str] = None
    due_time: Optional[str] = None


class TaskExtractionOutput(BaseModel):
    """Legacy output format for backward compatibility"""
    tasks: List[TaskItem] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    total_estimated_time: int = 0
    feasibility_score: float = 8.0


# =============================================================================
# Main Task Agent
# =============================================================================

class TaskAgent:
    """
    Efficient Task Agent with conversation support.
    Processes natural language and returns structured actions or suggestions.
    """

    # Compact system prompt - optimized for token efficiency
    SYSTEM_PROMPT = """Task assistant. Parse user input, return JSON only.

TODAY={today}
TASKS={tasks_context}

OUTPUT FORMAT:
{{"type":"actions|clarify|suggest","message":"user response","actions":[...],"suggestions":[...],"clarify_options":[...]}}

ACTIONS (when user wants to do something):
- read: {{"action":"read","query_type":"count|list|due_date","query_filter":"today|overdue|task_name"}}
- insert: {{"action":"insert","title":"x","category":"work|education|health|personal|social|finance","priority":1-5,"due_date":"YYYY-MM-DD","duration":mins}}
- update: {{"action":"update","task_id":"id|null","title":"task to find","due_date":"new date",...}}
- delete: {{"action":"delete","task_id":"id|null","title":"task to find"}}
- complete: {{"action":"complete","task_id":"id|null","title":"task to find"}}

CLARIFY (when input is ambiguous):
{{"type":"clarify","message":"What type of X?","clarify_options":["option1","option2","option3"]}}

SUGGEST (when planning/brainstorming):
{{"type":"suggest","message":"Here's a plan","suggestions":[{{"title":"x","category":"y","reason":"why"}}]}}

DATE CALC: tomorrow=+1, this week=nearest weekday, next week=+7, in N days=+N

INPUT:{input}
JSON:"""

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = None
        self.conversations: Dict[str, ConversationContext] = {}

        if LANGCHAIN_AVAILABLE:
            self.llm = OllamaLLM(
                model=model_name,
                base_url=base_url,
                temperature=0.2,  # Lower for more consistent output
                num_predict=1500,  # Reduced token limit
            )
            logger.info(f"TaskAgent initialized: {model_name}")
        else:
            logger.warning("LangChain unavailable - using fallback")

    def chat(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_tasks: Optional[List[Dict]] = None
    ) -> AgentResponse:
        """
        Main chat method - handles all user interactions.

        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            user_tasks: Current user's tasks for context

        Returns:
            AgentResponse with actions, suggestions, or clarification request
        """
        # Get or create conversation context
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self._get_or_create_context(session_id)

        # Add user message to history
        context.messages.append(ConversationMessage(role="user", content=user_input))

        # Check if this is a response to clarification
        if context.awaiting_clarification:
            return self._handle_clarification_response(context, user_input, user_tasks)

        # Check if accepting/rejecting suggestions
        if context.pending_suggestions:
            suggestion_response = self._check_suggestion_response(context, user_input)
            if suggestion_response:
                return suggestion_response

        # Process with LLM
        try:
            response = self._process_with_llm(context, user_input, user_tasks)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            response = self._fallback_processing(user_input)

        # Add assistant response to history
        context.messages.append(ConversationMessage(role="assistant", content=response.message))

        # Update context state based on response type
        if response.type == ResponseType.CLARIFY:
            context.awaiting_clarification = True
            context.clarification_topic = user_input
        elif response.type == ResponseType.SUGGEST:
            context.pending_suggestions = response.suggestions

        response.context_key = session_id
        return response

    def _get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing or create new conversation context"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(session_id=session_id)
        return self.conversations[session_id]

    def _build_tasks_context(self, user_tasks: Optional[List[Dict]]) -> str:
        """Build compact task context string"""
        if not user_tasks:
            return "none"

        # Only include essential info, limit to 10 tasks
        tasks_str = []
        for t in user_tasks[:10]:
            name = t.get('name', t.get('title', ''))[:30]
            due = t.get('due_date', '')[:10] if t.get('due_date') else ''
            tid = str(t.get('id', ''))[:8]
            tasks_str.append(f"{tid}:{name}:{due}")

        return "|".join(tasks_str) if tasks_str else "none"

    def _build_history_context(self, context: ConversationContext) -> str:
        """Build compact conversation history"""
        if len(context.messages) <= 1:
            return ""

        # Only last 4 messages for context
        recent = context.messages[-5:-1]  # Exclude current message
        history = []
        for msg in recent:
            role = "U" if msg.role == "user" else "A"
            content = msg.content[:100]  # Truncate long messages
            history.append(f"{role}:{content}")

        return "\nHISTORY:" + "|".join(history) if history else ""

    def _process_with_llm(
        self,
        context: ConversationContext,
        user_input: str,
        user_tasks: Optional[List[Dict]]
    ) -> AgentResponse:
        """Process input through LLM"""
        if not self.llm:
            return self._fallback_processing(user_input)

        today = datetime.now().strftime("%Y-%m-%d(%a)")
        tasks_ctx = self._build_tasks_context(user_tasks)
        history_ctx = self._build_history_context(context)

        prompt = self.SYSTEM_PROMPT.format(
            today=today,
            tasks_context=tasks_ctx,
            input=user_input + history_ctx
        )

        # Call LLM
        raw_response = self.llm.invoke(prompt)

        # Parse response
        return self._parse_llm_response(raw_response, user_input)

    def _parse_llm_response(self, raw: str, original_input: str) -> AgentResponse:
        """Parse LLM JSON response into AgentResponse"""
        import re

        try:
            # Clean response
            raw = raw.strip()
            raw = re.sub(r'//.*?(?=\n|$)', '', raw)
            raw = re.sub(r',\s*([}\]])', r'\1', raw)

            # Find JSON
            start = raw.find('{')
            end = raw.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = raw[start:end]
                data = json.loads(json_str)

                # Parse response type
                resp_type = ResponseType(data.get('type', 'actions'))

                # Parse actions
                actions = []
                for act in data.get('actions', []):
                    try:
                        actions.append(TaskAction(**act))
                    except Exception as e:
                        logger.warning(f"Invalid action: {e}")

                # Parse suggestions
                suggestions = []
                for sug in data.get('suggestions', []):
                    try:
                        suggestions.append(TaskSuggestion(**sug))
                    except Exception as e:
                        logger.warning(f"Invalid suggestion: {e}")

                return AgentResponse(
                    type=resp_type,
                    message=data.get('message', 'Done.'),
                    actions=actions,
                    suggestions=suggestions,
                    clarify_options=data.get('clarify_options', [])
                )

            raise ValueError("No JSON found")

        except Exception as e:
            logger.error(f"Parse error: {e}, raw: {raw[:200]}")
            return self._fallback_processing(original_input)

    def _handle_clarification_response(
        self,
        context: ConversationContext,
        user_input: str,
        user_tasks: Optional[List[Dict]]
    ) -> AgentResponse:
        """Handle user's response to a clarification question"""
        context.awaiting_clarification = False
        original_topic = context.clarification_topic or ""
        context.clarification_topic = None

        # Combine original topic with clarification
        combined_input = f"{original_topic}. User chose: {user_input}"

        return self._process_with_llm(context, combined_input, user_tasks)

    def _check_suggestion_response(
        self,
        context: ConversationContext,
        user_input: str
    ) -> Optional[AgentResponse]:
        """Check if user is responding to suggestions"""
        input_lower = user_input.lower().strip()

        # Accept all suggestions
        if input_lower in ['yes', 'ok', 'accept', 'accept all', 'yes all', 'confirm']:
            actions = []
            for sug in context.pending_suggestions:
                actions.append(TaskAction(
                    action=ActionType.INSERT,
                    title=sug.title,
                    description=sug.description,
                    category=sug.category,
                    priority=sug.priority,
                    due_date=sug.due_date,
                    duration=sug.duration,
                    frequency=sug.frequency
                ))

            count = len(actions)
            context.pending_suggestions = []

            return AgentResponse(
                type=ResponseType.ACTIONS,
                message=f"Added {count} tasks to your schedule.",
                actions=actions
            )

        # Reject all
        if input_lower in ['no', 'cancel', 'reject', 'nevermind', 'no thanks']:
            context.pending_suggestions = []
            return AgentResponse(
                type=ResponseType.CHAT,
                message="No problem, suggestions discarded. What else can I help with?"
            )

        # Accept specific by number
        if input_lower.startswith('accept ') or input_lower.replace(',', ' ').replace(' ', '').isdigit():
            # Parse numbers like "1,2,3" or "accept 1 2 3"
            nums = re.findall(r'\d+', input_lower)
            indices = [int(n) - 1 for n in nums]  # Convert to 0-indexed

            actions = []
            accepted_titles = []

            for i in indices:
                if 0 <= i < len(context.pending_suggestions):
                    sug = context.pending_suggestions[i]
                    actions.append(TaskAction(
                        action=ActionType.INSERT,
                        title=sug.title,
                        description=sug.description,
                        category=sug.category,
                        priority=sug.priority,
                        due_date=sug.due_date,
                        duration=sug.duration,
                        frequency=sug.frequency
                    ))
                    accepted_titles.append(sug.title)

            context.pending_suggestions = []

            if actions:
                return AgentResponse(
                    type=ResponseType.ACTIONS,
                    message=f"Added: {', '.join(accepted_titles)}",
                    actions=actions
                )

        # Not a suggestion response, continue normal processing
        return None

    def _fallback_processing(self, user_input: str) -> AgentResponse:
        """Rule-based fallback when LLM unavailable"""
        input_lower = user_input.lower()
        actions = []
        suggestions = []

        # Detect read queries
        if any(w in input_lower for w in ['how many', 'count', 'list', 'show', 'what tasks']):
            query_filter = "today" if "today" in input_lower else "all"
            if "overdue" in input_lower:
                query_filter = "overdue"

            actions.append(TaskAction(
                action=ActionType.READ,
                query_type="count" if "how many" in input_lower else "list",
                query_filter=query_filter
            ))
            return AgentResponse(
                type=ResponseType.ACTIONS,
                message="Fetching your tasks...",
                actions=actions
            )

        # Detect insert
        if any(w in input_lower for w in ['add', 'create', 'schedule', 'new task', 'remind']):
            # Extract task titles (simple approach)
            tasks_to_add = self._extract_tasks_simple(user_input)
            for title in tasks_to_add:
                actions.append(TaskAction(
                    action=ActionType.INSERT,
                    title=title,
                    category=self._guess_category(title),
                    priority=3
                ))

            if actions:
                return AgentResponse(
                    type=ResponseType.ACTIONS,
                    message=f"Adding {len(actions)} task(s).",
                    actions=actions
                )

        # Detect update
        if any(w in input_lower for w in ['update', 'change', 'move', 'reschedule', 'postpone']):
            actions.append(TaskAction(
                action=ActionType.UPDATE,
                title=user_input  # Will need to be parsed further
            ))
            return AgentResponse(
                type=ResponseType.ACTIONS,
                message="Updating task...",
                actions=actions
            )

        # Detect complete
        if any(w in input_lower for w in ['done', 'complete', 'finish', 'mark as done']):
            actions.append(TaskAction(
                action=ActionType.COMPLETE,
                title=user_input
            ))
            return AgentResponse(
                type=ResponseType.ACTIONS,
                message="Marking task as complete...",
                actions=actions
            )

        # Detect delete
        if any(w in input_lower for w in ['delete', 'remove', 'cancel task']):
            actions.append(TaskAction(
                action=ActionType.DELETE,
                title=user_input
            ))
            return AgentResponse(
                type=ResponseType.ACTIONS,
                message="Deleting task...",
                actions=actions
            )

        # Detect planning/ambiguous
        if any(w in input_lower for w in ['plan', 'help me', 'i want to', 'healthier', 'productive', 'better']):
            return AgentResponse(
                type=ResponseType.CLARIFY,
                message="I'd like to help! Could you be more specific about what you want to achieve?",
                clarify_options=[
                    "Create a workout routine",
                    "Plan my work schedule",
                    "Organize my daily tasks",
                    "Something else"
                ]
            )

        # Default: unclear input
        return AgentResponse(
            type=ResponseType.CHAT,
            message="I can help you manage tasks. Try: 'add task', 'show my tasks', 'mark X as done', or tell me what you're planning.",
        )

    def _extract_tasks_simple(self, text: str) -> List[str]:
        """Simple task extraction from text"""
        # Remove common prefixes
        text = re.sub(r'^(add|create|schedule|remind me to)\s+', '', text, flags=re.IGNORECASE)

        # Split by common delimiters
        if ' and ' in text.lower():
            parts = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)
        elif ',' in text:
            parts = text.split(',')
        else:
            parts = [text]

        return [p.strip() for p in parts if p.strip()]

    def _guess_category(self, title: str) -> str:
        """Guess category from task title"""
        title_lower = title.lower()
        if any(w in title_lower for w in ['gym', 'exercise', 'workout', 'run', 'yoga']):
            return "health"
        if any(w in title_lower for w in ['study', 'homework', 'learn', 'class', 'exam']):
            return "education"
        if any(w in title_lower for w in ['meeting', 'report', 'email', 'call', 'presentation']):
            return "work"
        if any(w in title_lower for w in ['clean', 'groceries', 'laundry', 'cook']):
            return "personal"
        return "personal"

    # =========================================================================
    # Suggestion Management
    # =========================================================================

    def get_pending_suggestions(self, session_id: str) -> List[TaskSuggestion]:
        """Get pending suggestions for a session"""
        context = self.conversations.get(session_id)
        return context.pending_suggestions if context else []

    def accept_suggestion(self, session_id: str, suggestion_id: str) -> Optional[TaskAction]:
        """Accept a specific suggestion by ID"""
        context = self.conversations.get(session_id)
        if not context:
            return None

        for i, sug in enumerate(context.pending_suggestions):
            if sug.id == suggestion_id:
                action = TaskAction(
                    action=ActionType.INSERT,
                    title=sug.title,
                    description=sug.description,
                    category=sug.category,
                    priority=sug.priority,
                    due_date=sug.due_date,
                    duration=sug.duration,
                    frequency=sug.frequency
                )
                context.pending_suggestions.pop(i)
                return action

        return None

    def modify_suggestion(
        self,
        session_id: str,
        suggestion_id: str,
        modifications: Dict
    ) -> Optional[TaskSuggestion]:
        """Modify a pending suggestion"""
        context = self.conversations.get(session_id)
        if not context:
            return None

        for sug in context.pending_suggestions:
            if sug.id == suggestion_id:
                for key, value in modifications.items():
                    if hasattr(sug, key):
                        setattr(sug, key, value)
                return sug

        return None

    def clear_suggestions(self, session_id: str) -> None:
        """Clear all pending suggestions for a session"""
        context = self.conversations.get(session_id)
        if context:
            context.pending_suggestions = []

    # =========================================================================
    # Session Management
    # =========================================================================

    def clear_session(self, session_id: str) -> None:
        """Clear a conversation session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

    def get_session_history(self, session_id: str) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        context = self.conversations.get(session_id)
        return context.messages if context else []

    # =========================================================================
    # Legacy Support
    # =========================================================================

    def process_intentions(self, user_input: str, context: Optional[Dict] = None) -> TaskExtractionOutput:
        """
        Legacy method for backward compatibility.
        Converts new response format to old TaskExtractionOutput.
        """
        user_tasks = context.get('user_tasks') if context else None
        response = self.chat(user_input, user_tasks=user_tasks)

        tasks = []
        for action in response.actions:
            if action.action == ActionType.INSERT:
                tasks.append(TaskItem(
                    title=action.title or "Task",
                    category=action.category or "personal",
                    priority=action.priority or 3,
                    frequency=action.frequency or "once",
                    duration=action.duration or 30,
                    due_date=action.due_date,
                    due_time=action.due_time
                ))

        for sug in response.suggestions:
            tasks.append(TaskItem(
                title=sug.title,
                category=sug.category,
                priority=sug.priority,
                frequency=sug.frequency,
                duration=sug.duration,
                due_date=sug.due_date
            ))

        return TaskExtractionOutput(
            tasks=tasks,
            insights=[response.message],
            total_estimated_time=sum(t.duration for t in tasks),
            feasibility_score=8.0
        )

    def validate_ollama_connection(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False

            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            return any(self.model_name in name for name in model_names)
        except Exception as e:
            logger.error(f"Ollama check failed: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except:
            return []


# Import for re module used in methods
import re
