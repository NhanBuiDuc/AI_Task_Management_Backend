# tasks_api\management\commands\test_categorize_tasks.py

from django.core.management.base import BaseCommand
from tasks_api.tasks import categorize_tasks_by_due_date

class Command(BaseCommand):
    help = 'Test the automatic task categorization function'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Testing automatic task categorization...')
        )

        try:
            # Run the task categorization function directly
            result = categorize_tasks_by_due_date()

            self.stdout.write(
                self.style.SUCCESS(f'Task completed successfully: {result}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running task categorization: {str(e)}')
            )

        self.stdout.write('')
        self.stdout.write('Task categorization test completed.')