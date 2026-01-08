"""
LangChain-based Task Agent using Local Ollama
Handles natural language input and converts to structured tasks
"""

from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import logging
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskItem(BaseModel):
    """Structured task item extracted from user intentions"""
    title: str = Field(description="Clear, actionable task title")
    category: str = Field(description="Category: work, education, health, personal, social, finance")
    priority: int = Field(description="Priority 1-5, where 5 is highest urgency")
    frequency: str = Field(description="Frequency: daily, weekly, monthly, once")
    duration: int = Field(description="Estimated duration in minutes")
    time_preference: str = Field(description="Preferred time: morning, afternoon, evening, anytime")
    energy_level: str = Field(description="Required energy: high, medium, low")
    deadline_urgency: str = Field(description="Deadline urgency: urgent, normal, flexible")

class TaskExtractionOutput(BaseModel):
    """Complete output from task extraction process"""
    tasks: List[TaskItem]
    insights: List[str] = Field(description="Insights about the schedule and recommendations")
    total_estimated_time: int = Field(description="Total time in minutes per week")
    feasibility_score: float = Field(description="Feasibility score 0-10")

class TaskAgent:
    """
    Main Task Agent class using local Ollama for intelligent task processing
    Processes natural language intentions and converts them into structured tasks
    """
    
    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        """Initialize the agent with Ollama configuration"""
        self.model_name = model_name
        self.base_url = base_url
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.3,
            num_predict=1500,
            timeout=60
        )
        
        self.chain = self._create_processing_chain()
        logger.info(f"TaskAgent initialized with model: {model_name}")
        
    def _create_processing_chain(self) -> LLMChain:
        """Create the LangChain processing chain with structured prompts"""
        
        template = """You are an intelligent task planning assistant. Analyze the user's intentions and extract specific, actionable tasks. Return ONLY valid JSON.

User Input: {user_input}

CLASSIFICATION RULES:

Categories:
- work: Job-related, career development, professional tasks
- education: Learning, studying, courses, skill development  
- health: Exercise, medical, wellness, mental health
- personal: Home, family, self-care, hobbies
- social: Friends, relationships, networking, community
- finance: Money management, investments, budgeting

Priority Scale (1-5):
- 1: Low (nice to have, flexible timing)
- 2: Normal (regular importance)
- 3: Medium (important, should be done)
- 4: High (urgent, deadline-sensitive)
- 5: Critical (emergency, must be done immediately)

Frequency Types:
- daily: Every day activities
- weekly: 1-6 times per week
- monthly: Monthly or less frequent
- once: One-time task or project

Time Preferences:
- morning: 6AM-12PM (best for high-energy, focus tasks)
- afternoon: 12PM-5PM (meetings, administrative work)
- evening: 5PM-10PM (exercise, social, relaxing activities)
- anytime: Flexible timing

Energy Levels:
- high: Requires deep focus, creativity, physical energy
- medium: Normal concentration, moderate effort
- low: Light tasks, can be done when tired

Deadline Urgency:
- urgent: Has specific deadline or time-sensitive
- normal: Regular timeline, some flexibility
- flexible: No rush, can be rescheduled

EXAMPLES:
Input: "learn Chinese daily, work on thesis, go to gym"
Expected tasks:
1. "Study Chinese language" (education, priority 3, daily, 30 mins, morning, medium, normal)
2. "Work on graduation thesis" (education, priority 5, daily, 120 mins, morning, high, urgent)
3. "Go to gym workout" (health, priority 3, weekly, 60 mins, evening, high, normal)

Calculate total weekly time and feasibility score (0-10).

Required JSON format:
{{
    "tasks": [
        {{
            "title": "Study Chinese language",
            "category": "education",
            "priority": 3,
            "frequency": "daily",
            "duration": 30,
            "time_preference": "morning",
            "energy_level": "medium",
            "deadline_urgency": "normal"
        }}
    ],
    "insights": [
        "Balanced schedule with good variety",
        "High-energy tasks scheduled for morning"
    ],
    "total_estimated_time": 420,
    "feasibility_score": 8.5
}}

Analyze this input: {user_input}

JSON Response:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["user_input"]
        )
        
        return LLMChain(llm=self.llm, prompt=prompt, verbose=True)
    
    def process_intentions(self, user_input: str, context: Optional[Dict] = None) -> TaskExtractionOutput:
        """
        Main method to process user intentions and return structured tasks
        
        Args:
            user_input: Natural language description of user's intentions
            context: Optional context about user preferences, existing tasks, etc.
            
        Returns:
            TaskExtractionOutput with structured tasks and insights
        """
        
        logger.info(f"Processing intentions with Ollama: {user_input[:100]}...")
        
        try:
            # Add context to input if provided
            enhanced_input = self._enhance_input_with_context(user_input, context)
            
            # Process through Ollama
            result = self.chain.run(user_input=enhanced_input)
            
            # Parse JSON response
            parsed_data = self._parse_llm_response(result)
            
            # Convert to Pydantic model
            output = TaskExtractionOutput(**parsed_data)
            
            # Validate and enhance the result
            validated_result = self._validate_and_enhance_output(output)
            
            logger.info(f"Successfully processed {len(validated_result.tasks)} tasks")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error in Ollama processing: {str(e)}")
            # Fallback to rule-based processing
            return self._fallback_processing(user_input)
    
    def _enhance_input_with_context(self, user_input: str, context: Optional[Dict]) -> str:
        """Enhance user input with additional context if available"""
        
        if not context:
            return user_input
            
        enhanced = user_input
        
        # Add context about user preferences
        if context.get('work_hours'):
            enhanced += f"\nUser typically works: {context['work_hours']}"
            
        if context.get('energy_peaks'):
            enhanced += f"\nUser has peak energy during: {context['energy_peaks']}"
            
        if context.get('existing_commitments'):
            enhanced += f"\nExisting time commitments: {context['existing_commitments']} hours/week"
            
        return enhanced
    
    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response and extract JSON"""
        try:
            # Clean the response
            response = response.strip()
            
            # Find JSON in response (look for first { to last })
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                
                # Try to parse JSON
                parsed = json.loads(json_str)
                
                # Validate required fields
                if 'tasks' not in parsed:
                    raise ValueError("Missing 'tasks' field in response")
                
                return parsed
            else:
                raise ValueError("No valid JSON found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response}")
            raise ValueError("Invalid JSON in LLM response")
    
    def _validate_and_enhance_output(self, output: TaskExtractionOutput) -> TaskExtractionOutput:
        """Validate and enhance the AI output with additional logic"""
        
        # Calculate total weekly time commitment
        total_weekly_minutes = 0
        for task in output.tasks:
            if task.frequency == 'daily':
                total_weekly_minutes += task.duration * 7
            elif task.frequency == 'weekly':
                total_weekly_minutes += task.duration * 3  # Assume 3x per week average
            elif task.frequency == 'monthly':
                total_weekly_minutes += task.duration * 0.25  # Monthly divided by 4
            else:  # once
                total_weekly_minutes += task.duration * 0.1  # Spread over 10 weeks
        
        output.total_estimated_time = int(total_weekly_minutes)
        
        # Calculate feasibility score if not provided
        if output.feasibility_score == 0:
            feasibility_score = self._calculate_feasibility_score(total_weekly_minutes, output.tasks)
            output.feasibility_score = feasibility_score
        
        # Add enhanced insights
        enhanced_insights = self._generate_enhanced_insights(output.tasks, total_weekly_minutes)
        output.insights.extend(enhanced_insights)
        
        return output
    
    def _calculate_feasibility_score(self, total_minutes: int, tasks: List[TaskItem]) -> float:
        """Calculate how feasible the schedule is (0-10 scale)"""
        
        # Base score starts at 10
        score = 10.0
        
        # Time commitment penalty
        total_hours = total_minutes / 60
        if total_hours > 40:
            score -= 3.0  # Too much time commitment
        elif total_hours > 25:
            score -= 1.5  # High but manageable
        
        # High priority task overload
        high_priority_count = len([t for t in tasks if t.priority >= 4])
        if high_priority_count > 3:
            score -= 2.0
            
        # Energy level balance
        high_energy_count = len([t for t in tasks if t.energy_level == 'high'])
        if high_energy_count > 2:
            score -= 1.0
            
        # Ensure minimum score
        return max(score, 1.0)
    
    def _generate_enhanced_insights(self, tasks: List[TaskItem], total_minutes: int) -> List[str]:
        """Generate additional insights based on task analysis"""
        
        insights = []
        
        # Time commitment insight
        hours_per_week = total_minutes / 60
        if hours_per_week > 35:
            insights.append(f"⚠️ High time commitment: {hours_per_week:.1f} hours/week. Consider prioritizing tasks.")
        elif hours_per_week < 10:
            insights.append(f"✅ Manageable schedule: {hours_per_week:.1f} hours/week. Room for additional activities.")
        else:
            insights.append(f"✅ Balanced schedule: {hours_per_week:.1f} hours/week.")
        
        # Category distribution
        categories = [task.category for task in tasks]
        category_counts = {cat: categories.count(cat) for cat in set(categories)}
        
        if category_counts.get('work', 0) > 3:
            insights.append("💼 Work-heavy schedule. Consider adding personal/health activities for balance.")
        
        if 'health' not in categories:
            insights.append("🏃‍♂️ Consider adding health/fitness activities to your routine.")
            
        if 'social' not in categories:
            insights.append("👥 Consider scheduling social activities for work-life balance.")
        
        # Priority distribution
        urgent_tasks = [t for t in tasks if t.priority >= 4]
        if len(urgent_tasks) > 3:
            insights.append("🔥 Multiple high-priority tasks. Focus on 1-2 critical items first.")
        
        # Energy level recommendations
        high_energy_tasks = [t for t in tasks if t.energy_level == 'high']
        if len(high_energy_tasks) > 0:
            insights.append("⚡ Schedule high-energy tasks during your peak hours for better productivity.")
        
        return insights
    
    def _fallback_processing(self, user_input: str) -> TaskExtractionOutput:
        """
        Simple rule-based fallback when Ollama fails
        Provides basic task extraction using keyword matching
        """
        
        logger.warning("Using fallback processing due to Ollama failure")
        
        tasks = []
        insights = ["⚠️ Using simplified processing. Results may be less accurate."]
        
        # Basic keyword matching
        input_lower = user_input.lower()
        
        # Education keywords
        if any(word in input_lower for word in ['learn', 'study', 'course', 'language', 'chinese', 'english', 'thesis', 'research']):
            tasks.append(TaskItem(
                title="Study/Learning Activity",
                category="education",
                priority=3,
                frequency="daily",
                duration=60,
                time_preference="morning",
                energy_level="medium",
                deadline_urgency="normal"
            ))
        
        # Health keywords
        if any(word in input_lower for word in ['gym', 'exercise', 'workout', 'fitness', 'health', 'sport']):
            tasks.append(TaskItem(
                title="Exercise/Fitness Activity", 
                category="health",
                priority=3,
                frequency="weekly",
                duration=60,
                time_preference="evening",
                energy_level="high",
                deadline_urgency="normal"
            ))
        
        # Work keywords
        if any(word in input_lower for word in ['cv', 'resume', 'interview', 'job', 'work', 'career', 'project']):
            tasks.append(TaskItem(
                title="Career Development Task",
                category="work", 
                priority=4,
                frequency="weekly",
                duration=90,
                time_preference="afternoon",
                energy_level="medium",
                deadline_urgency="urgent"
            ))
        
        # Default task if nothing matched
        if not tasks:
            tasks.append(TaskItem(
                title="General Task",
                category="personal",
                priority=2,
                frequency="once", 
                duration=30,
                time_preference="anytime",
                energy_level="low",
                deadline_urgency="flexible"
            ))
        
        return TaskExtractionOutput(
            tasks=tasks,
            insights=insights,
            total_estimated_time=sum(task.duration for task in tasks),
            feasibility_score=7.0
        )
    
    def validate_ollama_connection(self) -> bool:
        """Validate if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.error("Ollama server is not responding")
                return False
            
            # Check if our model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            model_available = any(self.model_name in name for name in model_names)
            if not model_available:
                logger.error(f"Model {self.model_name} not found. Available: {model_names}")
                
            return model_available
            
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []