import os

from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = 'Does some stuff'

    option_list = BaseCommand.option_list + (
        make_option('-u', '--users', type="int", default=None, dest='users',
            help='Specifies the number of users to add to the db'),
        make_option('--review-requests', type="int", nargs=2, default=None,
            dest='review-requests',
            help='Specifies the range of review requests for each user.'),
        make_option('--diffs', default=None, dest='diffs',
            help='Specifies the range of diffs for each user.'),
        make_option('--diff-comments', default=None, dest='diff-comments',
            help='Specifies the range of review requests for each user.')
              )


    def handle_noargs(self, **options):
        users = options.get('users', None)
        review_requests = options.get('review-requests', None)

        if users:
            self.stdout.write("The number of users=" + str(users) + "\n")

####### Parses the command args as 40:50 Looking for a better way########
#
#        if review_requests:
#            req_range = review_requests.partition(":")
#            self.stdout.write("first number is="+req_range[0]+"\n" \
#                + "second number=" + req_range[2] + "\n")
#            try:
#                start = int(req_range[0])
#            except ValueError:
#                self.stdout.write("The first arg of review-requests needs " \
#                    + "to be an int\n")
#                exit()
#
#            #If second value in range is empty, set all to first number
#            if req_range[2]=='':
#                self.stdout.write("Missing a second argument\n")
#                end = start
#            else:
#                try:
#                    end = int(req_range[2])
#                except ValueError:
#                    self.stdout.write("The second arg of review-requests " \
#                        + "needs to be an int\n")
#                    exit()
#
#            self.stdout.write("Here is the range of review-requests: " \
#                + str(start) + " and " + str(end) + ";\n")
#
#
