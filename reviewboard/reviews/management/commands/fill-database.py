import os

from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand

class Command(LabelCommand):

    help = 'Does some stuff'

    option_list = BaseCommand.option_list + (
        make_option('--date', default=None, dest='date',
            help='Specifies if we shall not add date'),
        make_option('--format', default=None, dest='format',
            help='Specifies the output serialization format for fixtures.')
            )

    def handle_label(self, labels, **options):
        for label in labels:
            search, pks = label, ''
            if '--' in label:
                search, pks = label.split('--',1)
            self.stdout.write("search="+search+", pks="+pks+";\n")


#        if label=='test':
#            self.stdout.write('You just wrote test\n')
#        else:
#            self.stdout.write('You wrote something other than a provided option\n')
#
