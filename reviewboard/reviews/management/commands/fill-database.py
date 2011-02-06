import os
import random
from django.contrib.auth.models import User
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand
from reviewboard.accounts.models import Profile

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
        req_min = None
        req_max = None
        diff_min = None
        diff_max = None
        diff_com_min = None
        diff_com_max = None
        random.seed()

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

        if users:
            self.stdout.write("The number of users=" + str(users) + "\n")
            for i in range(1, users+1):
                new_user=User.objects.create(
                    username="test"+str(i), first_name="Testing", last_name="Thomas",
                    email="test@email.com", 
                    #default password = test1
                    password="sha1$21fca$4ecf8335b1bd3331ad3f216c7a35029787be261a",
                    is_staff=False, is_active=True, is_superuser=False,
                    last_login="2011-01-16 21:47:17.529855",
                    date_joined="2011-01-16 21:47:17.529855")

                #Uncomment to set a custom password
                #new_user.set_password('reviewboard1')
                #new_user.save()

                Profile.objects.create(
                    user_id=new_user.id,
                    first_time_setup_done=True, collapsed_diffs=True,
                    wordwrapped_diffs=True, syntax_highlighting=True,
                    show_submitted=True, sort_review_request_columns="",
                    sort_dashboard_columns="", sort_submitter_columns="",
                    sort_group_columns="", dashboard_columns="",
                    submitter_columns="", group_columns="")


                #Review Requests
                if not req_min == None or not req_max == None:
                    req_val = random.randrange(req_min, req_max)



                #generate output as users & data is created
                output = "username=" + new_user.username + ", userId=" + \
                    str(new_user.id)

                try:
                   output += ", requests=" + str(req_val)
                except NameError:
                    pass

                output += "\n"

                self.stdout.write(output)


    def parseCommand(self, com_arg, com_string):
        try:
            min_range, max_range = [ int(item.strip()) for item in com_string.split(":")]
            return min_range, max_range
        except ValueError:
            print "You failed to provide \"" + com_arg + "\" with two values of type int."
            exit()


