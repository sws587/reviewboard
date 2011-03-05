import os
import random
import sys
from optparse import make_option

from django import forms
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand

from reviewboard.accounts.models import Profile
from reviewboard.diffviewer.models import FileDiff, DiffSet, DiffSetHistory
from reviewboard.diffviewer.forms import UploadDiffForm
from reviewboard.reviews.models import ReviewRequest, Review, Comment
from reviewboard.scmtools.models import Repository, Tool


class Command(NoArgsCommand):
    help = 'Populates the database with the specified fields'

    option_list = BaseCommand.option_list + (
        make_option('-u', '--users', type="int", default=None, dest='users',
            help='The number of users to add'),
        make_option('--review-requests', default=None, dest='review-requests',
            help='The number of review requests per user [min:max]'),
        make_option('--diffs', default=None, dest='diffs',
            help='The number of diff per review request [min:max]'),
        make_option('--reviews', default=None, dest='reviews',
            help='The number of reviews per diff [min:max]'),
        make_option('--diff-comments', default=None, dest='diff-comments',
            help='The number of comments per diff [min:max]')
        )

    def handle_noargs(self, **options):
        users = options.get('users', None)
        review_requests = options.get('review-requests', None)
        diffs = options.get('diffs', None)
        reviews = options.get('reviews', None)
        diff_comments = options.get('diff-comments', None)
        num_of_requests = None
        num_of_diffs = None
        num_of_reviews = None
        num_of_diff_comments = None
        random.seed()

        verbose = True  #Generate details as program runs

        if review_requests:
            num_of_requests = self.parseCommand("review_requests",
                review_requests)

            # SETUP REPOSITORY
            repo_dir = str(os.path.abspath(sys.argv[0] +
                'manage.py/../scmtools/testdata/git_repo'))
            if not os.path.exists(repo_dir):
                self.stdout.write("The path to the repository does " + \
                    "not exist\n")
                return

            test_repository = Repository.objects.create(
                name="Test Repository", path=repo_dir,
                tool=Tool.objects.get(name="Git")
                )

            self.repository = test_repository

        if diffs:
            num_of_diffs = self.parseCommand("diffs", diffs)

            # CREATE THE DIFF DIRECTORY LOCATIONS
            diff_dir_tmp = str(os.path.abspath(sys.argv[0] +
                'manage.py/../reviews/management/' + \
                'commands/diffs'))
            if not os.path.exists(diff_dir_tmp):
                print >> sys.stderr, "The path to the " + \
                    "repository does not exist\n"
                self.stdout.write("dir: " + diff_dir_tmp)
                return
            diff_dir = diff_dir_tmp + '/' #add trailing slash

            #Get a list of the appropriate files
            files = []
            for chosen_file in os.listdir(diff_dir):
                if '.diff' in chosen_file:
                    files.append(chosen_file)

            #Check for any diffs in the files
            if len(files) == 0:
                print >> sys.stderr, "There are no " + \
                    "diff files in this directory"
                return

        if reviews:
            num_of_reviews = self.parseCommand("reviews", reviews)

        if diff_comments:
            num_of_diff_comments = self.parseCommand("diff-comments",
                diff_comments)

        # users is required for any other operation
        if not users:
            print >> sys.stderr, "You must add at least 1 user\n"
            exit()

        # START ADDING DATA TO THE DATABASE
        for i in range(1, users+1):
            new_user = User.objects.create(
                username=self.randUsername(), #temp to avoid flushing
                #username="test"+str(i),
                first_name="Testing", last_name="Thomas",
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
                user=new_user,
                first_time_setup_done=True, collapsed_diffs=True,
                wordwrapped_diffs=True, syntax_highlighting=True,
                show_submitted=True, sort_review_request_columns="",
                sort_dashboard_columns="", sort_submitter_columns="",
                sort_group_columns="", dashboard_columns="",
                submitter_columns="", group_columns="")

            #Review Requests
            req_val = self.pickRandomValue(num_of_requests)

            if verbose:
                self.stdout.write("\nFor user: " + str(new_user.username) +\
                    "\n============================\n")

            for j in range(0, req_val):

                if verbose:
                    self.stdout.write("Request #" + str(j) +\
                        ":\n")

                review_request = ReviewRequest.objects.create(new_user,
                    None)
                review_request.public=True
                review_request.summary="TEST v1.00 summary"
                review_request.description="TEST v1.00 is a description"
                review_request.shipit_count=0
                review_request.repository=test_repository
                #set the targeted reviewer to superuser or 1st defined
                review_request.target_people.add(
                    User.objects.get(id__exact="1"))
                review_request.save()

                # ADD THE DIFFS IF ANY TO ADD
                diff_val = self.pickRandomValue(num_of_diffs)

                # if adding diffs add history
                if diff_val > 0:
                    diffset_history = DiffSetHistory.objects.create(
                        name='testDiffFile' + str(i))
                    diffset_history.save()
                    
                # won't execute if diff_val is 0, ie: no diffs requested
                for k in range(0, diff_val):
                
                    if verbose:
                        self.stdout.write("\tDiff #" + str(k) +\
                            ":\n")

                    random_number = random.randint(0, len(files)-1)
                    file_to_open = diff_dir + files[random_number]
                    filename = open(file_to_open, 'r')
                    form = UploadDiffForm(
                        review_request.repository, filename)
                    cur_diff=form.create(filename, None, diffset_history)
                    review_request.diffset_history = diffset_history
                    review_request.publish(new_user)

                    # ADD THE REVIEWS IF ANY
                    review_val = self.pickRandomValue(num_of_reviews)

                    for l in range(0, review_val):

                        if verbose:
                            self.stdout.write("\t\tReview #" +\
                                str(l) + "\n")

                        reviews = Review.objects.create(
                            review_request=review_request,
                            user=new_user)

                        # ADD COMMENTS TO DIFFS IF ANY
                        comment_val = self.pickRandomValue(num_of_diff_comments)

                        for m in range(0, comment_val):

                            if verbose:
                                self.stdout.write("\t\t\tComments #" +\
                                str(m) + "\n")

                            #Cur_diff is a diffset #TEMPORARY
#                            self.stdout.write("cur_diff_all=" + str(cur_diff.files.all()) + "\n\n")
#                            self.stdout.write("\nCOUNT=" + str(cur_diff.files.count()) + "\n")

                            for file_diff in cur_diff.files.all():
                                break #HORRIBLE CHEAT BUT WORKS SINCE
                                      #cur_diff is most recent

                            #CHOOSE RANDOM LINES TO COMMENT
                            #Max lines: should be mod'd in future to read diff
                            max_lines = 220
                            first_line = random.randrange(1,max_lines-1)
                            remain_lines = max_lines - first_line
                            num_lines = random.randrange(1,remain_lines)

                            diff_comment = Comment.objects.create(
                                filediff=file_diff,
                                text="comment number " + str(m+1),
                                first_line=first_line,
                                num_lines=num_lines)

                            review_request.publish(new_user)

                            reviews.comments.add(diff_comment)
                            reviews.save()      #Adds to the database

                            reviews.publish(new_user)   #Publically available

            #generate output as users & data is created
            output = "\nuser " + new_user.username + " created successfully"

            try:
               output += " with " + str(req_val) + " requests"
            except NameError:
               pass

            output += "\n"
            self.stdout.write(output)


    #Parse the values given in the command line
    def parseCommand(self, com_arg, com_string):
        try:
            return tuple((int(item.strip()) for item in com_string.split(':')))
        except ValueError:
            print >> sys.stderr, "You failed to provide \"" + com_arg \
                + "\" with two values of type int."
            exit()


    #Temporary function used to generate random usernames so no flushing needed
    def randUsername(self):
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        min = 5
        max = 7
        string=''
        for x in random.sample(alphabet,random.randint(min,max)):
            string+=x
        return string


    #This acts like a condition check in the program, value is a tuple
    def pickRandomValue(self, value):
        if value:
            if len(value)==1:
                return value[0]
            else:
                return random.randrange(value[0], value[1])
        else:
            return 0
 
