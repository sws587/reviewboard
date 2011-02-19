import os, random, sys
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand
from django.utils.encoding import smart_unicode

from reviewboard.accounts.models import Profile
from reviewboard.diffviewer.diffutils import DEFAULT_DIFF_COMPAT_VERSION
from reviewboard.diffviewer.models import FileDiff, DiffSet, DiffSetHistory
from reviewboard.reviews.models import ReviewRequest
from reviewboard.scmtools.models import Repository, Tool
from reviewboard.scmtools.core import PRE_CREATION, UNKNOWN, FileNotFoundError

class Command(NoArgsCommand):
    help = 'Does some stuff'

    option_list = BaseCommand.option_list + ( 
        make_option('-u', '--users', type="int", default=None, dest='users',
            help='The number of users to add'),
        make_option('--review-requests', default=None, dest='review-requests',
            help='The number of review requests per user [min:max]'),
        make_option('--diffs', default=None, dest='diffs',
            help='The number of diff per review request [min:max]'),
        make_option('--diff-comments', default=None, dest='diff-comments',
            help='The number of comments per diff [min:max]')
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

            #TEMPORARY TEXT OUTPUT
            self.stdout.write("You entered review-request range: " + str(req_min) + \
                    " to " + str(req_max) + "\n" )

        if diffs:
            diff_min, diff_max = self.parseCommand("diffs", diffs)
            #TEMPORARY OUTPUT
            self.stdout.write("You entered a range from " + str(diff_min) + \
                " to " + str(diff_max) + "\n")

        if diff_comments:
            diff_com_min, diff_com_max = self.parseCommand("diff-comments", diff_comments)
            #TEMPORARY OUTPUT
            self.stdout.write("You entered a range from " + str(diff_com_min) + \
                " to " + str(diff_com_max) + "\n")

        if users:
            #TEMPORARY OUTPUT
            self.stdout.write("The number of users=" + str(users) + "\n")
            
            if req_min:
                #path to the test repository based from this script
                repo_dir = str(os.path.abspath(sys.argv[0] + 
                    'manage.py/../scmtools/testdata/git_repo'))
                if not os.path.exists(repo_dir):
                    self.stdout.write("The path to the repository does not exist\n")
                    return

                self.stdout.write("this is the repo directory:\n" + repo_dir + "\n" )
                self.stdout.write("SCMTOOL: " + str(Tool.objects.get(name="Git")) + "\n")

                #Setup a repository
                test_repository = Repository.objects.create(
                    name="Test Repository", path=repo_dir, 
                    tool=Tool.objects.get(name="Git")
                    )

                self.repository = test_repository

            for i in range(1, users+1):
                new_user=User.objects.create(
                    username=self.randUsername(), #temporary to avoid having to flush
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
                if not req_min == None or not req_max == None:
                    req_val = random.randrange(req_min, req_max)

                    for k in range(1,req_val+1):
                        review_request=ReviewRequest.objects.create(new_user,None)
                        review_request.public=True
                        review_request.summary="TEST v0.16 summary"
                        review_request.description="TEST v0.16 is a description"
                        review_request.shipit_count=0
                        review_request.repository=test_repository
                        #set the targeted reviewer to be the superuser or 1st defined user
                        review_request.target_people.add(User.objects.get(id__exact="1"))
                        review_request.save()

                        tool = self.repository.get_scmtool()
                        # Grab the base directory if there is one.
                        ## NOT SURE WHAT THIS IS SUPPOSED TO DO, IT DOESN"T SEEM TO GET DIRECTORY
                        if not tool.get_diffs_use_absolute_paths():
                            try:
                                basedir = smart_unicode(self.cleaned_data['basedir'].strip())
                            except AttributeError:
                                raise NoBaseDirError(_('The "Base Diff Path" field is required'))
                        else:
                            basedir = ''

                        diff_dir = str(os.path.abspath(sys.argv[0] + 
                            'manage.py/../scmtools/testdata'))
                        if not os.path.exists(diff_dir):
                            self.stdout.write("The path to the repository does not exist\n")
                            return

                        self.stdout.write('the base dir= ' + basedir)

                        self.stdout.write("hellooo mcfly\n")

                        diff_file =open(diff_dir + '/git_newfile.diff', 'r')

                        parent_diff_file = None
                        diffset_history = None

                        diffset_history = DiffSetHistory.objects.create(
                            name="git_newfile.diff"
                            )

                        diffset_history.save()

                         # Parse the diff
                        files = list(self._process_files(
                            diff_file, diff_dir, check_existance=(not parent_diff_file)))

                        if len(files) == 0:
                            raise EmptyDiffError(_("The diff file is empty"))

                        # Sort the files so that header files come before implementation.
                        files.sort(cmp=self._compare_files, key=lambda f: f.origFile)

                        # Parse the parent diff
                        parent_files = {}

                        # This is used only for tools like Mercurial that use atomic changeset
                        # IDs to identify all file versions but not individual file version
                        # IDs.
                        parent_changeset_id = None

                        if parent_diff_file:
                            # If the user supplied a base diff, we need to parse it and
                            # later apply each of the files that are in the main diff
                            for f in self._process_files(parent_diff_file, diff_dir,
                                                         check_existance=True):
                                parent_files[f.origFile] = f

                                # Store the original changeset ID if we have it; this should
                                # be the same for all files.
                                if f.origChangesetId:
                                    parent_changeset_id = f.origChangesetId

                        diffset = DiffSet(name=diff_file.name, revision=0,
                                          basedir=diff_dir,
                                          history=diffset_history,
                                          diffcompat=DEFAULT_DIFF_COMPAT_VERSION)
                        diffset.repository = self.repository
                        diffset.save()

                        for f in files:
                            if f.origFile in parent_files:
                                parent_file = parent_files[f.origFile]
                                parent_content = parent_file.data
                                source_rev = parent_file.origInfo
                            else:
                                parent_content = ""

                                if (tool.diff_uses_changeset_ids and
                                    parent_changeset_id and
                                    f.origInfo != PRE_CREATION):
                                    source_rev = parent_changeset_id
                                else:
                                    source_rev = f.origInfo

                            dest_file = os.path.join(diff_dir, f.newFile).replace("\\", "/")

                            if f.deleted:
                                status = FileDiff.DELETED
                            else:
                                status = FileDiff.MODIFIED

                            filediff = FileDiff(diffset=diffset,
                                                source_file=f.origFile,
                                                dest_file=dest_file,
                                                source_revision=smart_unicode(source_rev),
                                                dest_detail=f.newInfo,
                                                diff=f.data,
                                                parent_diff=parent_content,
                                                binary=f.binary,
                                                status=status)
                            filediff.save()


#                        diff_dir=str(os.path.abspath(sys.argv[0] + 
#                                'manage.py/../scmtools/testdata'))

#                       if not diff_min == None or not diff_max==None:
#                            diff_val = random.randrange(diff_min, diff_max)
#                            self.stdout.write("diffval="+str(diff_val)+"\n")

#                            diff_set=DiffSet.objects.create(
#                                name="git_newfile.diff",
#                                revision=1,
#                                basedir=diff_dir,
#                                history=diff_hist,
#                                repository=test_repository,
#                                )
#                            diff_set.save()
                            
#                            src_dir = str(os.path.abspath(sys.argv[0] + 
#                                'manage.py/../scmtools/testdata/git_newfile.diff'))

#                            file_diff = FileDiff.objects.create(
#                                diffset=diff_set,
#                                source_file=src_dir,
#                                dest_file=src_dir,
#                                diff=src_dir,
#                                dest_detail="(working copy)",
#                                source_revision='PRE-CREATION',
#                                status='M'
#                                )

#                            file_diff.save()

                        review_request.diffset_history=diffset_history
                        review_request.save()

                #generate output as users & data is created
                output = "username=" + new_user.username + ", userId=" + \
                    str(new_user.id)

                try:
                   output += ", requests=" + str(req_val)
                except NameError:
                    pass

                output += "\n"

                self.stdout.write(output)


    #Parse the values given in the command line
    def parseCommand(self, com_arg, com_string):
        try:
            return (int(item.strip()) for item in com_string.split(':'))
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

#COPIED DIRECTLY FROM diffviewer/forms.py
    def _process_files(self, file, basedir, check_existance=False):
        tool = self.repository.get_scmtool()

        for f in tool.get_parser(file.read()).parse():
            f2, revision = tool.parse_diff_revision(f.origFile, f.origInfo)
            if f2.startswith("/"):
                filename = f2
            else:
                filename = os.path.join(basedir, f2).replace("\\", "/")

            # FIXME: this would be a good place to find permissions errors
            if (revision != PRE_CREATION and
                revision != UNKNOWN and
                not f.binary and
                not f.deleted and
                (check_existance and
                 not tool.file_exists(filename, revision))):
                raise FileNotFoundError(filename, revision)

            f.origFile = filename
            f.origInfo = revision

            yield f


    def _compare_files(self, filename1, filename2):
        """
        Compares two files, giving precedence to header files over source
        files. This allows the resulting list of files to be more
        intelligently sorted.
        """
        if filename1.find('.') != -1 and filename2.find('.') != -1:
            basename1, ext1 = filename1.rsplit('.', 1)
            basename2, ext2 = filename2.rsplit('.', 1)

            if basename1 == basename2:
                if ext1 in self.HEADER_EXTENSIONS and \
                   ext2 in self.IMPL_EXTENSIONS:
                    return -1
                elif ext1 in self.IMPL_EXTENSIONS and \
                     ext2 in self.HEADER_EXTENSIONS:
                    return 1

        return cmp(filename1, filename2) 
