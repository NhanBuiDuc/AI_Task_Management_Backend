# File: tasks_api/agents/intent_agent.py
"""
Intent-Based Task Agent - Uses predefined intent mappings for safe, efficient task management.
The LLM predicts intent IDs from a fixed list, then we execute corresponding handlers.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import json
import logging
import requests
import uuid
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field as dataclass_field

from .intent_registry import (
    INTENT_REGISTRY,
    IntentAction,
    ActionType,
    IntentCategory,
    PredictedIntent,
    IntentExecutionResult,
    build_compact_intent_list,
    get_intent_by_id,
)

# LangChain imports
LANGCHAIN_AVAILABLE = False
try:
    from langchain_ollama import OllamaLLM
    LANGCHAIN_AVAILABLE = True
except ImportError:
    OllamaLLM = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================

@dataclass
class TokenReport:
    """Token usage report for LLM requests"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'model': self.model,
            'latency_ms': round(self.latency_ms, 2)
        }


class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Maintains conversation state"""
    session_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    pending_intents: List[PredictedIntent] = Field(default_factory=list)
    last_intent_id: Optional[str] = None


class ExtractedTask(BaseModel):
    """Single extracted task from user input"""
    title: str
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: str = "medium"


class AgentResponse(BaseModel):
    """Response from intent agent"""
    success: bool
    intent: str = "chat"  # create/query/complete/update/delete/chat
    message: str
    tasks: List[ExtractedTask] = Field(default_factory=list)
    query_type: Optional[str] = None  # today/all/overdue/search
    data: Dict[str, Any] = Field(default_factory=dict)
    needs_confirmation: bool = False
    session_id: Optional[str] = None
    token_report: Optional[Dict[str, Any]] = None

    # Legacy fields for backward compatibility
    intent_id: Optional[str] = None
    extracted_params: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Intent-Based Task Agent
# =============================================================================

class IntentAgent:
    """
    Intent-based agent that predicts user intent from a fixed list.
    Much more efficient and safer than generating arbitrary actions.
    """

    # Flexible system prompt - Extracts ALL tasks from user input
    SYSTEM_PROMPT = """You are a task extraction assistant. Extract ALL tasks from user input. Be FLEXIBLE and HELPFUL.

TODAY={today}
USER_TASKS={tasks_context}

RULES:
1. EXTRACT ALL TASKS mentioned in the input as a list.
2. "I want to X, Y, and Z" = 3 separate tasks.
3. "I need to X and Y" = 2 separate tasks.
4. Even single statements like "learn coding" = 1 task.
5. For queries (show tasks, what's today), return intent only with empty tasks list.
6. Always try to create tasks from user intentions.

OUTPUT JSON FORMAT:
{{"intent":"create|query|complete|update|delete|chat","tasks":[{{"title":"...","due_date":"...","due_time":"...","priority":"medium"}}],"query_type":"today|all|overdue|search","message":"friendly response"}}

TASK FIELDS:
- title: task description (REQUIRED)
- due_date: today/tomorrow/monday/2026-01-24 (optional)
- due_time: 10pm/14:00/9am (optional)
- priority: low/medium/high/urgent (default: medium)

DATE SHORTCUTS: today={today}, tomorrow=next day, tonight=today

EXAMPLES:
"I want to learn coding, go to gym, and call mom" -> {{"intent":"create","tasks":[{{"title":"learn coding"}},{{"title":"go to gym"}},{{"title":"call mom"}}],"message":"Adding 3 tasks"}}
"learn python and practice guitar tomorrow" -> {{"intent":"create","tasks":[{{"title":"learn python"}},{{"title":"practice guitar","due_date":"tomorrow"}}],"message":"Adding 2 tasks"}}
"insert a task at 10pm today to take out trash" -> {{"intent":"create","tasks":[{{"title":"take out trash","due_date":"today","due_time":"10pm"}}],"message":"Adding task for today at 10pm"}}
"remind me to buy groceries and pick up laundry" -> {{"intent":"create","tasks":[{{"title":"buy groceries"}},{{"title":"pick up laundry"}}],"message":"Adding 2 tasks"}}
"I need to finish the report by friday" -> {{"intent":"create","tasks":[{{"title":"finish the report","due_date":"friday"}}],"message":"Adding task due Friday"}}
"what tasks today" -> {{"intent":"query","tasks":[],"query_type":"today","message":"Here are your tasks for today"}}
"show all my tasks" -> {{"intent":"query","tasks":[],"query_type":"all","message":"Here are all your tasks"}}
"show my schedule" -> {{"intent":"query","tasks":[],"query_type":"today","message":"Here are your tasks"}}
"mark homework as done" -> {{"intent":"complete","tasks":[{{"title":"homework"}}],"message":"Marking homework as complete"}}
"delete the meeting task" -> {{"intent":"delete","tasks":[{{"title":"meeting"}}],"message":"Deleting meeting task"}}

INPUT:{input}
JSON:"""

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = None
        self.conversations: Dict[str, ConversationContext] = {}
        self.last_token_report: Optional[TokenReport] = None

        if LANGCHAIN_AVAILABLE:
            self.llm = OllamaLLM(
                model=model_name,
                base_url=base_url,
                temperature=0.1,  # Very low for consistent intent selection
                num_predict=400,  # Need room for intent + params + message
                timeout=30,  # 30 second timeout for LLM calls
            )
            logger.info(f"IntentAgent initialized: {model_name}")
        else:
            logger.warning("LangChain unavailable - using fallback")

    def predict_intent(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_tasks: Optional[List[Dict]] = None
    ) -> AgentResponse:
        """
        Extract tasks and intent from user input.

        Args:
            user_input: User's natural language message
            session_id: Session ID for conversation tracking
            user_tasks: User's current tasks for context

        Returns:
            AgentResponse with extracted tasks and intent
        """
        # Get or create session
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self._get_or_create_context(session_id)
        context.messages.append(ConversationMessage(role="user", content=user_input))

        # Reset token report
        self.last_token_report = None

        # Try LLM extraction
        try:
            result = self._extract_with_llm(user_input, user_tasks, context)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            result = self._fallback_extraction(user_input)

        # Build response
        response = AgentResponse(
            success=True,
            intent=result.get('intent', 'chat'),
            message=result.get('message', 'Processing...'),
            tasks=[ExtractedTask(**t) for t in result.get('tasks', []) if t.get('title')],
            query_type=result.get('query_type'),
            data=result.get('data', {}),
            needs_confirmation=result.get('intent') == 'delete',
            session_id=session_id,
            token_report=self.last_token_report.to_dict() if self.last_token_report else None,
            # Legacy compatibility
            intent_id=self._map_intent_to_legacy(result),
            extracted_params=result.get('tasks', [{}])[0] if result.get('tasks') else {}
        )

        # Store assistant response
        context.messages.append(ConversationMessage(role="assistant", content=response.message))

        return response

    def _map_intent_to_legacy(self, result: Dict) -> str:
        """Map new intent format to legacy intent_id"""
        intent = result.get('intent', 'chat')
        query_type = result.get('query_type', '')

        if intent == 'query':
            mapping = {
                'today': 'tasks-today-list',
                'all': 'tasks-all-list',
                'overdue': 'tasks-overdue-list',
                'upcoming': 'tasks-upcoming-list',
                'search': 'task-search',
            }
            return mapping.get(query_type, 'tasks-today-list')
        elif intent == 'create':
            tasks = result.get('tasks', [])
            if len(tasks) > 1:
                return 'tasks-create-multiple'
            elif tasks and (tasks[0].get('due_date') or tasks[0].get('due_time')):
                return 'task-create-with-date'
            return 'task-create-simple'
        elif intent == 'complete':
            return 'task-complete'
        elif intent == 'delete':
            return 'task-delete'
        elif intent == 'update':
            return 'task-update-due-date'
        return 'chat-general'

    def _extract_with_llm(
        self,
        user_input: str,
        user_tasks: Optional[List[Dict]],
        context: ConversationContext
    ) -> Dict:
        """Use LLM to extract tasks from input"""
        today = datetime.now().strftime("%Y-%m-%d(%a)")
        tasks_ctx = self._build_tasks_context(user_tasks)

        # Add conversation history if exists
        history = ""
        if len(context.messages) > 1:
            recent = context.messages[-4:-1]
            history_parts = [f"{'U' if m.role == 'user' else 'A'}:{m.content[:50]}" for m in recent]
            history = f"\nHISTORY: {' | '.join(history_parts)}"

        prompt = self.SYSTEM_PROMPT.format(
            today=today,
            tasks_context=tasks_ctx,
            input=user_input + history
        )

        # Call Ollama API directly to get token counts
        raw, token_report = self._call_ollama_with_tokens(prompt)
        self.last_token_report = token_report

        return self._parse_extraction_response(raw, user_input)

    def _parse_extraction_response(self, raw: str, original_input: str) -> Dict:
        """Parse LLM response into task extraction result"""
        try:
            raw = raw.strip()
            # Clean JSON
            raw = re.sub(r'//.*?(?=\n|$)', '', raw)
            raw = re.sub(r',\s*([}\]])', r'\1', raw)

            # Find JSON
            start = raw.find('{')
            end = raw.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = raw[start:end]
                data = json.loads(json_str)

                # Ensure tasks is a list
                if 'tasks' not in data:
                    data['tasks'] = []
                elif not isinstance(data['tasks'], list):
                    data['tasks'] = [data['tasks']]

                return data

            raise ValueError("No JSON found")

        except Exception as e:
            logger.error(f"Parse error: {e}, raw: {raw[:200]}")
            return self._fallback_extraction(original_input)

    def _fallback_extraction(self, user_input: str) -> Dict:
        """Fallback when LLM fails - try to extract a simple task"""
        # Check if it looks like a query
        query_words = ['show', 'list', 'what', 'how many', 'schedule', 'agenda']
        if any(word in user_input.lower() for word in query_words):
            return {
                'intent': 'query',
                'tasks': [],
                'query_type': 'today',
                'message': "Here are your tasks"
            }

        # Otherwise treat as a task creation
        return {
            'intent': 'create',
            'tasks': [{'title': user_input.strip()}],
            'message': f"Adding task: {user_input.strip()}"
        }

    def _get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(session_id=session_id)
        return self.conversations[session_id]

    def _build_tasks_context(self, user_tasks: Optional[List[Dict]]) -> str:
        """Build compact task context"""
        if not user_tasks:
            return "none"

        tasks_str = []
        for t in user_tasks[:10]:
            name = t.get('name', t.get('title', ''))[:25]
            due = str(t.get('due_date', ''))[:10]
            tasks_str.append(f"{name}|{due}")

        return ";".join(tasks_str) if tasks_str else "none"

    def _predict_with_llm(
        self,
        user_input: str,
        user_tasks: Optional[List[Dict]],
        context: ConversationContext
    ) -> PredictedIntent:
        """Use LLM to predict intent with token tracking"""
        today = datetime.now().strftime("%Y-%m-%d(%a)")
        tasks_ctx = self._build_tasks_context(user_tasks)
        intent_list = build_compact_intent_list()

        # Add conversation history if exists
        history = ""
        if len(context.messages) > 1:
            recent = context.messages[-4:-1]
            history_parts = [f"{'U' if m.role == 'user' else 'A'}:{m.content[:50]}" for m in recent]
            history = f"\nHISTORY: {' | '.join(history_parts)}"

        prompt = self.SYSTEM_PROMPT.format(
            today=today,
            tasks_context=tasks_ctx,
            intent_list=intent_list,
            input=user_input + history
        )

        # Call Ollama API directly to get token counts
        raw, token_report = self._call_ollama_with_tokens(prompt)
        self.last_token_report = token_report

        return self._parse_llm_response(raw, user_input)

    def _call_ollama_with_tokens(self, prompt: str) -> tuple:
        """Call Ollama API directly and return response with token counts"""
        start_time = time.time()
        token_report = TokenReport(model=self.model_name)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 400
                    }
                },
                timeout=30
            )

            latency_ms = (time.time() - start_time) * 1000
            token_report.latency_ms = latency_ms

            if response.status_code == 200:
                data = response.json()
                raw_response = data.get('response', '')

                # Extract token counts from Ollama response
                token_report.prompt_tokens = data.get('prompt_eval_count', 0)
                token_report.completion_tokens = data.get('eval_count', 0)
                token_report.total_tokens = token_report.prompt_tokens + token_report.completion_tokens

                # Log token report
                logger.info(
                    f"[TOKENS] prompt={token_report.prompt_tokens}, "
                    f"completion={token_report.completion_tokens}, "
                    f"total={token_report.total_tokens}, "
                    f"latency={token_report.latency_ms:.0f}ms"
                )

                return raw_response, token_report
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                # Fallback to LangChain if available
                if self.llm:
                    raw = self.llm.invoke(prompt)
                    token_report.latency_ms = (time.time() - start_time) * 1000
                    # Estimate tokens (rough: ~4 chars per token)
                    token_report.prompt_tokens = len(prompt) // 4
                    token_report.completion_tokens = len(raw) // 4
                    token_report.total_tokens = token_report.prompt_tokens + token_report.completion_tokens
                    return raw, token_report
                return "", token_report

        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            token_report.latency_ms = (time.time() - start_time) * 1000

            # Fallback to LangChain if available
            if self.llm:
                try:
                    raw = self.llm.invoke(prompt)
                    # Estimate tokens (rough: ~4 chars per token)
                    token_report.prompt_tokens = len(prompt) // 4
                    token_report.completion_tokens = len(raw) // 4
                    token_report.total_tokens = token_report.prompt_tokens + token_report.completion_tokens
                    return raw, token_report
                except Exception as e2:
                    logger.error(f"LangChain fallback failed: {e2}")

            return "", token_report

    def _parse_llm_response(self, raw: str, original_input: str) -> PredictedIntent:
        """Parse LLM response into PredictedIntent"""
        try:
            raw = raw.strip()
            # Clean JSON
            raw = re.sub(r'//.*?(?=\n|$)', '', raw)
            raw = re.sub(r',\s*([}\]])', r'\1', raw)

            # Find JSON
            start = raw.find('{')
            end = raw.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = raw[start:end]
                data = json.loads(json_str)

                return PredictedIntent(
                    intent_id=data.get('intent_id', 'chat-general'),
                    confidence=float(data.get('confidence', 0.8)),
                    extracted_params=data.get('params', {}),
                    user_message=data.get('message'),
                    clarification_needed=data.get('intent_id') == 'clarify-ambiguous',
                    clarification_message=data.get('message', '') if data.get('intent_id') == 'clarify-ambiguous' else None
                )

            raise ValueError("No JSON found")

        except Exception as e:
            logger.error(f"Parse error: {e}, raw: {raw[:200]}")
            return self._fallback_prediction(original_input)

    def _fallback_prediction(self, user_input: str) -> PredictedIntent:
        """Simple fallback when LLM fails - just return chat-general"""
        return PredictedIntent(
            intent_id='chat-general',
            user_message="I couldn't understand that. Try: 'add task X', 'show today tasks', or 'mark X as done'."
        )

    def _check_missing_params(self, intent: Optional[IntentAction], params: Dict) -> List[str]:
        """Check if required params are present"""
        if not intent:
            return []

        missing = []
        for param in intent.requires_params:
            if param not in params or not params[param]:
                missing.append(param)

        return missing

    def _build_message(self, intent: Optional[IntentAction], predicted: PredictedIntent) -> str:
        """Build user-friendly message"""
        if predicted.user_message:
            return predicted.user_message

        if not intent:
            return "I'm not sure what you mean. Could you rephrase?"

        params = predicted.extracted_params

        if intent.id == 'tasks-today-list':
            return "Here are your tasks for today."
        if intent.id == 'tasks-today-count':
            return "Counting your tasks for today..."
        if intent.id == 'task-create-simple':
            return f"I'll add '{params.get('title', 'task')}' to your list."
        if intent.id == 'task-create-with-date':
            return f"I'll add '{params.get('title', 'task')}' due {params.get('due_date', 'soon')}."
        if intent.id == 'task-complete':
            return f"Marking '{params.get('task_name', 'task')}' as complete."
        if intent.id == 'task-delete':
            return f"I'll delete '{params.get('task_name', 'task')}'. Are you sure?"

        return f"Processing: {intent.description}"

    # =========================================================================
    # Session Management
    # =========================================================================

    def get_session_history(self, session_id: str) -> List[ConversationMessage]:
        """Get conversation history"""
        ctx = self.conversations.get(session_id)
        return ctx.messages if ctx else []

    def clear_session(self, session_id: str) -> None:
        """Clear a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

    # =========================================================================
    # Utility
    # =========================================================================

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
