from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import json

# Initialize model
llm = OllamaLLM(model="llama3", temperature=0.7)

# Task planning prompt
prompt = PromptTemplate.from_template("""You are a personal task planner AI.

User Context: {user_context}
Goal: {goal}
Timeframe: {timeframe}

Generate a structured daily plan with specific tasks, priorities, and time blocks.
Return as JSON with format:
{{
  "days": [
    {{"day": 1, "tasks": [{{"task": "...", "priority": "high/medium/low", "time": "HH:MM-HH:MM"}}]}}
  ]
}}
""")

# Create chain using LCEL (LangChain Expression Language)
chain = prompt | llm

# Example usage
user_context = """
- Software engineer
- Works 9AM-5PM
- Prefers coding in morning
- Gym at 6PM
- Sleeps at 11PM
"""

result = chain.invoke({
    "user_context": user_context,
    "goal": "Finish AI research paper",
    "timeframe": "3 days"
})

print(result)

# Parse and use the plan
try:
    plan = json.loads(result)
    for day in plan['days']:
        print(f"\nDay {day['day']}:")
        for task in day['tasks']:
            print(f"  [{task['priority']}] {task['time']}: {task['task']}")
except:
    print("Raw plan:", result)