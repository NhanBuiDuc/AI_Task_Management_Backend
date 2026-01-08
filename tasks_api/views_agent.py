"""
Django views for LangChain Agent integration using Ollama
Handles intention processing and task creation
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from datetime import date, timedelta
import logging

from .agents.task_agent import TaskAgent
from .models import Task, Project, Section, TaskView
from .serializers import TaskSerializer

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])  # Remove in production, add authentication
def process_intentions(request):
    """
    Process user intentions and create tasks automatically using Ollama
    
    POST /api/process-intentions/
    Body: {"intentions": "learn Chinese daily, work on thesis, go to gym"}
    """
    
    # Validate input
    user_input = request.data.get('intentions', '').strip()
    if not user_input:
        return Response({
            'success': False,
            'error': 'Intentions text is required',
            'example': 'learn Chinese daily, work on thesis 2 hours, go to gym 3 times a week'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(user_input) > 1000:
        return Response({
            'success': False,
            'error': 'Input too long. Maximum 1000 characters.',
            'current_length': len(user_input)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Initialize agent with Ollama
        agent = TaskAgent(
            model_name=getattr(settings, 'OLLAMA_MODEL_NAME', 'llama3.2'),
            base_url=getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        )
        
        # Check Ollama connection first
        if not agent.validate_ollama_connection():
            return Response({
                'success': False,
                'error': 'Ollama is not running or model not available',
                'suggestion': 'Start Ollama with: ollama serve',
                'required_model': agent.model_name,
                'available_models': agent.get_available_models()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Process intentions through AI
        logger.info(f"Processing intentions: {user_input}")
        ai_result = agent.process_intentions(user_input)
        
        # Create tasks in database
        created_tasks = []
        projects_used = set()
        
        for task_item in ai_result.tasks:
            
            # Get or create category project
            project = _get_or_create_category_project(task_item.category)
            if project:
                projects_used.add(project.name)
            
            # Create task in database
            task = Task.objects.create(
                name=task_item.title,
                description=f"Auto-generated from AI: {user_input[:100]}...",
                priority=_map_priority(task_item.priority),
                due_date=_calculate_due_date(task_item.frequency),
                duration_in_minutes=task_item.duration,
                repeat=_map_frequency(task_item.frequency),
                project=project,
                section=None  # Will be auto-assigned by model's save method
            )
            
            # Serialize task for response
            task_data = TaskSerializer(task).data
            
            # Add AI metadata to response
            task_data['ai_metadata'] = {
                'category': task_item.category,
                'time_preference': task_item.time_preference,
                'energy_level': task_item.energy_level,
                'deadline_urgency': task_item.deadline_urgency,
                'ai_priority': task_item.priority
            }
            
            created_tasks.append(task_data)
            logger.info(f"Created task: {task.name} in project: {project.name if project else 'None'}")
        
        # Prepare success response
        response_data = {
            'success': True,
            'message': f'Successfully created {len(created_tasks)} tasks from AI analysis',
            'data': {
                'created_tasks': created_tasks,
                'ai_insights': ai_result.insights,
                'total_estimated_time_per_week': ai_result.total_estimated_time,
                'feasibility_score': ai_result.feasibility_score,
                'projects_used': list(projects_used),
                'original_input': user_input,
                'processing_method': 'ollama_ai' if len(ai_result.tasks) > 0 else 'fallback'
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing intentions: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to process intentions',
            'details': str(e),
            'suggestion': 'Try simpler input like: "study English 30 minutes daily, exercise 1 hour weekly"',
            'input_received': user_input
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def agent_health_check(request):
    """
    Check if Ollama agent is working properly
    
    GET /api/agent-health/
    """
    
    try:
        # Initialize agent
        agent = TaskAgent(
            model_name=getattr(settings, 'OLLAMA_MODEL_NAME', 'llama3.2'),
            base_url=getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        )
        
        # Check Ollama connection
        is_healthy = agent.validate_ollama_connection()
        available_models = agent.get_available_models()
        
        return Response({
            'agent_status': 'healthy' if is_healthy else 'unhealthy',
            'ollama_running': len(available_models) > 0,
            'current_model': agent.model_name,
            'model_available': agent.model_name in ' '.join(available_models),
            'available_models': available_models,
            'base_url': agent.base_url,
            'timestamp': date.today().isoformat(),
            'suggestions': _get_health_suggestions(is_healthy, available_models, agent.model_name)
        })
        
    except Exception as e:
        return Response({
            'agent_status': 'error',
            'error': str(e),
            'ollama_running': False,
            'suggestions': [
                'Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh',
                'Start Ollama: ollama serve',
                'Pull model: ollama pull llama3.2'
            ]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def quick_test_agent(request):
    """
    Quick test endpoint for the AI agent
    
    POST /api/quick-test-agent/
    Body: {} (uses default test input)
    """
    
    test_input = request.data.get('test_input', 'learn programming 30 minutes daily')
    
    try:
        agent = TaskAgent()
        result = agent.process_intentions(test_input)
        
        return Response({
            'success': True,
            'test_input': test_input,
            'extracted_tasks': len(result.tasks),
            'tasks_preview': [
                {
                    'title': task.title,
                    'category': task.category,
                    'priority': task.priority,
                    'frequency': task.frequency
                }
                for task in result.tasks
            ],
            'insights': result.insights,
            'feasibility_score': result.feasibility_score
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'test_input': test_input
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_category_projects(request):
    """
    Get all AI-created category projects
    
    GET /api/category-projects/
    """
    
    try:
        # Get projects created by AI categorization
        category_names = [
            'Learning & Education',
            'Work & Career', 
            'Health & Fitness',
            'Personal Life',
            'Social & Relationships',
            'Finance & Money'
        ]
        
        category_projects = Project.objects.filter(name__in=category_names)
        
        projects_data = []
        for project in category_projects:
            task_count = project.tasks.filter(totally_completed=False).count()
            projects_data.append({
                'id': str(project.id),
                'name': project.name,
                'icon': project.icon,
                'color': project.color,
                'active_tasks': task_count,
                'created_at': project.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'category_projects': projects_data,
            'total_projects': len(projects_data)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Helper Functions
def _map_priority(ai_priority: int) -> str:
    """Map AI priority (1-5) to Django model choices"""
    mapping = {
        1: 'low',
        2: 'medium', 
        3: 'medium',
        4: 'high',
        5: 'urgent'
    }
    return mapping.get(ai_priority, 'medium')

def _map_frequency(ai_frequency: str) -> str:
    """Map AI frequency to Django model choices"""
    mapping = {
        'daily': 'every day',
        'weekly': 'every week',
        'monthly': 'every month',
        'once': None  # No repeat for one-time tasks
    }
    return mapping.get(ai_frequency)

def _calculate_due_date(frequency: str) -> date:
    """Calculate appropriate due date based on frequency"""
    today = date.today()
    
    if frequency == 'daily':
        return today + timedelta(days=1)
    elif frequency == 'weekly':
        return today + timedelta(days=7) 
    elif frequency == 'monthly':
        return today + timedelta(days=30)
    else:  # once
        return today + timedelta(days=7)  # One week for one-time tasks

def _get_or_create_category_project(category: str) -> Project:
    """Get or create project for AI-identified category"""
    
    category_config = {
        'education': {
            'name': 'Learning & Education', 
            'icon': 'book', 
            'color': '#3B82F6'
        },
        'work': {
            'name': 'Work & Career', 
            'icon': 'briefcase', 
            'color': '#EF4444'
        },
        'health': {
            'name': 'Health & Fitness', 
            'icon': 'heart', 
            'color': '#10B981'
        },
        'personal': {
            'name': 'Personal Life', 
            'icon': 'user', 
            'color': '#8B5CF6'
        },
        'social': {
            'name': 'Social & Relationships', 
            'icon': 'users', 
            'color': '#F59E0B'
        },
        'finance': {
            'name': 'Finance & Money', 
            'icon': 'dollar-sign', 
            'color': '#06B6D4'
        }
    }
    
    config = category_config.get(category, {
        'name': 'General Tasks',
        'icon': 'circle', 
        'color': '#6B7280'
    })
    
    # Get or create the project
    project, created = Project.objects.get_or_create(
        name=config['name'],
        defaults={
            'icon': config['icon'],
            'color': config['color']
        }
    )
    
    if created:
        logger.info(f"Created new category project: {config['name']}")
    
    return project

def _get_health_suggestions(is_healthy: bool, available_models: list, required_model: str) -> list:
    """Generate health check suggestions"""
    
    suggestions = []
    
    if not is_healthy:
        if not available_models:
            suggestions.extend([
                'Ollama is not running. Start with: ollama serve',
                'Install Ollama if not installed: curl -fsSL https://ollama.ai/install.sh | sh'
            ])
        elif required_model not in ' '.join(available_models):
            suggestions.extend([
                f'Required model "{required_model}" not found',
                f'Pull the model: ollama pull {required_model}',
                f'Available models: {", ".join(available_models)}'
            ])
        else:
            suggestions.append('Ollama connection issues - check logs')
    else:
        suggestions.append('✅ Agent is healthy and ready to process intentions')
    
    return suggestions