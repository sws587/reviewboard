import os
import random
import string
import sys
from optparse import make_option

from django import forms
from django import db
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand
from django.db import transaction

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
            help='The number of comments per diff [min:max]'),
        make_option('-p', '--password', type="string", default=None,
            dest='password', help='The login password for users created')
        )

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        users = options.get('users', None)
        review_requests = options.get('review-requests', None)
        diffs = options.get('diffs', None)
        reviews = options.get('reviews', None)
        diff_comments = options.get('diff-comments', None)
        password = options.get('password', None)
        num_of_requests = None
        num_of_diffs = None
        num_of_reviews = None
        num_of_diff_comments = None
        random.seed()

        verbose = True  # Generate details as program runs

        if review_requests:
            num_of_requests = self.parseCommand("review_requests",
                review_requests)

            # setup repository
            repo_dir = str(os.path.abspath(sys.argv[0] +
                '/../scmtools/testdata/git_repo'))

            # throw exception on error so transaction reverts
            try:
                if not os.path.exists(repo_dir):
                    raise ValueError("No path to repository")
            except ValueError:
                print >> sys.stderr, "The path to the repository " +\
                    "does not exist\n"
                exit()

            test_repository = Repository.objects.create(
                name="Test Repository", path=repo_dir,
                tool=Tool.objects.get(name="Git")
                )

            self.repository = test_repository

        if diffs:
            num_of_diffs = self.parseCommand("diffs", diffs)

            # CREATE THE DIFF DIRECTORY LOCATIONS
            diff_dir_tmp = str(os.path.abspath(sys.argv[0] +
                '/../reviews/management/commands/diffs'))

            # throw exception on error so transaction reverts
            try:
                if not os.path.exists(diff_dir_tmp):
                    raise ValueError("Diff dir Error")
            except ValueError:
                print >> sys.stderr, "The path to the diffs " +\
                    "does not exist\npath:", diff_dir_tmp
                exit()

            diff_dir = diff_dir_tmp + '/'  # add trailing slash

            #Get a list of the appropriate files
            files = []
            for chosen_file in os.listdir(diff_dir):
                if '.diff' in chosen_file:
                    files.append(chosen_file)

            #Check for any diffs in the files
            try:
                if len(files) == 0:
                    raise ValueError("No diff files")
            except ValueError:
                print >> sys.stderr, "There are no " + \
                    "diff files in this directory"
                exit()

        if reviews:
            num_of_reviews = self.parseCommand("reviews", reviews)

        if diff_comments:
            num_of_diff_comments = self.parseCommand("diff-comments",
                diff_comments)

        # users is required for any other operation
        try:
            if not users:
                raise ValueError("User Error")
        except ValueError:
            print >> sys.stderr, "You must add at least 1 user\n"
            exit()

        # START ADDING DATA TO THE DATABASE
        for i in range(1, users + 1):
            new_user = User.objects.create(
                username=self.randUsername(),  # avoids having to flush db
                first_name="Testing", last_name="Thomas",
                email="test@email.com",
                #default password = test1
                password="sha1$21fca$4ecf8335b1bd3331ad3f216c7a35029787be261a",
                is_staff=False, is_active=True, is_superuser=False,
                last_login="2011-01-16 21:47:17.529855",
                date_joined="2011-01-16 21:47:17.529855")

            if password:
                new_user.set_password(password)
                new_user.save()

            Profile.objects.create(
                user=new_user,
                first_time_setup_done=True, collapsed_diffs=True,
                wordwrapped_diffs=True, syntax_highlighting=True,
                show_submitted=True)

            #Review Requests
            req_val = self.pickRandomValue(num_of_requests)

            if verbose:
                self.stdout.write("\nFor user " + str(i) + ": " +\
                    str(new_user.username) +\
                    "\n============================\n")

            for j in range(0, req_val):

                if verbose:
                    self.stdout.write("Request #" + str(j) +\
                        ":\n")

                review_request = ReviewRequest.objects.create(new_user,
                    None)
                review_request.public = True
                review_request.summary = self.lorem_ipsum("summary")
                review_request.description = self.lorem_ipsum("description")
                review_request.shipit_count = 0
                review_request.repository = test_repository
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
                        self.stdout.write(str(i) + ":\tDiff #" + str(k) +\
                            ":\n")

                    random_number = random.randint(0, len(files) - 1)
                    file_to_open = diff_dir + files[random_number]
                    filename = open(file_to_open, 'r')
                    form = UploadDiffForm(
                        review_request.repository, filename)
                    cur_diff = form.create(filename, None, diffset_history)
                    review_request.diffset_history = diffset_history
                    review_request.save()
                    review_request.publish(new_user)
                    filename.close()

                    # add the reviews if any
                    review_val = self.pickRandomValue(num_of_reviews)

                    for l in range(0, review_val):

                        if verbose:
                            self.stdout.write(str(i) + ":" + str(j) +\
                            ":\t\tReview #" + str(l) + ":\n")

                        reviews = Review.objects.create(
                            review_request=review_request,
                            user=new_user)

                        reviews.publish(new_user)

                        # add comments if any
                        comment_val = self.pickRandomValue(
                            num_of_diff_comments)

                        for m in range(0, comment_val):

                            if verbose:
                                self.stdout.write(str(i) + ":" + str(j) +\
                                ":\t\t\tComments #" +\
                                str(m) + "\n")

                            file_diff = cur_diff.files.order_by('id')[0]

                            # choose random lines to comment
                            # Max lines: should be mod'd in future to read diff
                            max_lines = 220
                            first_line = random.randrange(1, max_lines - 1)
                            remain_lines = max_lines - first_line
                            num_lines = random.randrange(1, remain_lines)

                            diff_comment = Comment.objects.create(
                                filediff=file_diff,
                                text="comment number " + str(m + 1),
                                first_line=first_line,
                                num_lines=num_lines)

                            review_request.publish(new_user)

                            reviews.comments.add(diff_comment)
                            reviews.save()
                            reviews.publish(new_user)

                            db.reset_queries()

                        # No comments, so have previous layer clear queries
                        if comment_val == 0:
                            db.reset_queries()

                    if review_val == 0:
                        db.reset_queries()

                if diff_val == 0:
                    db.reset_queries()

            if req_val == 0:
                db.reset_queries()

            # generate output as users & data is created
            # This can be simplified: here until required output is outlined
            output = "\nuser " + new_user.username + " created successfully"

            if req_val != 0:
                output += " with " + str(req_val) + " requests"

            output += "\n"
            self.stdout.write(output)

    # Parse the values given in the command line
    def parseCommand(self, com_arg, com_string):
        try:
            return tuple((int(item.strip()) for item in com_string.split(':')))
        except ValueError:
            print >> sys.stderr, "You failed to provide \"" + com_arg \
                + "\" with one or two values of type int.\n" +\
                "Example: --" + com_arg + "=2:5"
            exit()

    # Used to generate random usernames so no flushing needed
    def randUsername(self):
        return ''.join(random.choice(string.ascii_lowercase)
            for x in range(0, random.randrange(5, 9)))

    # This acts like a condition check in the program, value is a tuple
    def pickRandomValue(self, value):
        if not value:
            return 0

        if len(value) == 1:
            return value[0]

        return random.randrange(value[0], value[1])

    # Create some random text for summary/description
    def lorem_ipsum(self, ipsum_type):

        if ipsum_type == "description":
            max_size = 100
        else:
            max_size = 6

        lorem_vocab = \
        ['Lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur',
        'Nullam', 'quis', 'erat', 'libero.', 'Ut', 'vel', 'velit', 'augue, ',
        'risus.', 'Curabitur', 'dignissim', 'luctus', 'dui, ', 'et',
        'tristique', 'id.', 'Etiam', 'blandit', 'adipiscing', 'molestie.',
        'libero', 'eget', 'lacus', 'adipiscing', 'aliquet', 'ut', 'eget',
        'urna', 'dui', 'auctor', 'id', 'varius', 'eget', 'consectetur',
        'Sed', 'ornare', 'fermentum', 'erat', 'ut', 'consectetur', 'diam',
        'in.', 'Aliquam', 'eleifend', 'egestas', 'erat', 'nec', 'semper.',
        'a', 'mi', 'hendrerit', 'vestibulum', 'ut', 'vehicula', 'turpis.',
        'habitant', 'morbi', 'tristique', 'senectus', 'et', 'netus', 'et',
        'fames', 'ac', 'turpis', 'egestas.', 'Vestibulum', 'purus', 'odio',
        'quis', 'consequat', 'non, ', 'vehicula', 'nec', 'ligula.', 'In',
        'ipsum', 'in', 'volutpat', 'ipsum.', 'Morbi', 'aliquam', 'velit',
        'molestie', 'suscipit.', 'Morbi', 'dapibus', 'nibh', 'vel',
        'justo', 'nibh', 'facilisis', 'tortor, ', 'sit', 'amet', 'dictum',
        'amet', 'arcu.', 'Quisque', 'ultricies', 'justo', 'non', 'neque',
        'nibh', 'tincidunt.', 'Curabitur', 'sit', 'amet', 'sem', 'quis',
        'vulputate.', 'Mauris', 'a', 'lorem', 'mi.', 'Donec', 'dolor',
        'interdum', 'eu', 'scelerisque', 'vel', 'massa.', 'Vestibulum',
        'risus', 'vel', 'ipsum', 'suscipit', 'laoreet.', 'Proin', 'congue',
        'blandit.', 'Aenean', 'aliquet', 'auctor', 'nibh', 'sit', 'amet',
        'Vestibulum', 'ante', 'ipsum', 'primis', 'in', 'faucibus', 'orci',
        'posuere', 'cubilia', 'Curae;', 'Donec', 'lacinia', 'tincidunt',
        'facilisis', 'nisl', 'eu', 'fermentum.', 'Ut', 'nec', 'laoreet',
        'magna', 'egestas', 'nulla', 'pharetra', 'vel', 'egestas', 'tellus',
        'Pellentesque', 'sed', 'pharetra', 'orci.', 'Morbi', 'eleifend, ',
        'interdum', 'placerat,', 'mi', 'dolor', 'mollis', 'libero',
        'quam', 'posuere', 'nisl.', 'Vivamus', 'facilisis', 'aliquam',
        'condimentum', 'pulvinar', 'egestas.', 'Lorem', 'ipsum', 'dolor',
        'consectetur', 'adipiscing', 'elit.', 'In', 'hac', 'habitasse',
        'Aenean', 'blandit', 'lectus', 'et', 'dui', 'tincidunt', 'cursus',
        'Suspendisse', 'ipsum', 'dui, ', 'accumsan', 'eget', 'imperdiet',
        'est.', 'Integer', 'porta, ', 'ante', 'ac', 'commodo', 'faucibus',
        'molestie', 'risus, ', 'a', 'imperdiet', 'eros', 'neque', 'ac',
        'nisi', 'leo', 'pretium', 'congue', 'eget', 'quis', 'arcu.', 'Cras']

        return ' '.join(random.choice(lorem_vocab)
            for x in range(0, max_size))
