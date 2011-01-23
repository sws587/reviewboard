import os

from django.core.management.base import LabelCommand

class Command(LabelCommand):
    
    help = 'Does some stuff'

    arg = "[this]"

    def handle_label(self, label, **options):
        self.stdout.write('Here is the first command\n')

