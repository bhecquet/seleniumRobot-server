from django.core.management.base import BaseCommand
from variableServer.models import Variable

class Command(BaseCommand):
    help = "Save all protected variables to update algorithm"

    def handle(self, *args, **options):
        for variable in Variable.objects.filter(protected=True):
            print(f"{variable.id} - {variable.value}")
            variable.save()
        
        
        