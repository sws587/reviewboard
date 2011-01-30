import os

from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = 'Does some stuff'

    option_list = BaseCommand.option_list + ( 
        make_option('-u', '--users', type="int", default=None, dest='users',
            help='Specifies the number of users to add to the db'),
        make_option('--review-requests', default=None, dest='review-requests',
            help='Specifies the range of review requests for each user.'),
        make_option('--diffs', default=None, dest='diffs',
            help='Specifies the range of diffs for each user.'),
        make_option('--diff-comments', default=None, dest='diff-comments',
            help='Specifies the range of review requests for each user.')
        )

    def handle_noargs(self, **options):
        users = options.get('users', None)
        review_requests = options.get('review-requests', None)
        diffs = options.get('diffs', None)
        diff_comments = options.get('diff-comments', None)

        if users:
            self.stdout.write("The number of users=" + str(users) + "\n")

        if review_requests:
            req_min, req_max = self.parseCommand("review_requests", review_requests)
            self.stdout.write("You entered a range from " + str(req_min) + \
                    " to " + str(req_max) + "\n" )

        if diffs:
            diff_min, diff_max = self.parseCommand("diffs", diffs)
            self.stdout.write("You entered a range from " + str(diff_min) + \
                " to " + str(diff_max) + "\n")
        
        if diff_comments:
            diff_com_min, diff_com_max = self.parseCommand("diff-comments", diff_comments)
            self.stdout.write("You entered a range from " + str(diff_com_min) + \
                " to " + str(diff_com_max) + "\n")
            

    def parseCommand(self, com_arg, com_string):
        try:
            min_range, max_range = [ int(item.strip()) for item in com_string.split(":")]
            return min_range, max_range
        except ValueError:
            print "You failed to provide \"" + com_arg + "\" with two values of type int."
            exit()


