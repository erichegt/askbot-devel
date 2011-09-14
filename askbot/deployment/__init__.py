"""
module for deploying askbot
"""
import os.path
from optparse import OptionParser
from askbot.utils import console
from askbot.deployment import messages
from askbot.deployment import path_utils

def askbot_setup():
    """basic deployment procedure
    asks user several questions, then either creates
    new deployment (in the case of new installation)
    or gives hints on how to add askbot to an existing
    Django project
    """
    parser = OptionParser(usage="%prog [options]")
    
    parser.add_option("-v", "--verbose",
                      dest="verbosity",
                      type="int",
                      default=1,
                      help="verbosity level available values 0, 1, 2."
                     )

    parser.add_option("-n",
                      dest="name",
                      default=None,
                      help="Destination name"
                     )

    parser.add_option("-d", "--db-name",
                      dest="database_name",
                      default=None,
                      help="The database name"
                     )

    parser.add_option("-u", "--db-user",
                      dest="database_user",
                      default=None,
                      help="The database user"
                     )

    parser.add_option("-p", "--db-password",
                      dest="database_password",
                      default=None,
                      help="the database password"
                     )

    (options, args) = parser.parse_args()
    #ask 
    if options.verbosity >= 1:
        print messages.DEPLOY_PREAMBLE

    directory = options.name #directory where to put stuff
    create_new = False #create new django project or not
    where_to_deploy_msg = messages.WHERE_TO_DEPLOY

    if directory == None:
        while directory is None:
            where_to_deploy_msg = messages.WHERE_TO_DEPLOY_QUIT
            directory = raw_input(where_to_deploy_msg + ' ')
            directory = check_directory(directory, options)
            if not directory:
                continue

            if path_utils.can_create_path(directory):
                if os.path.exists(directory):
                    if path_utils.path_is_clean_for_django(directory):
                        if path_utils.has_existing_django_project(directory):
                            message = messages.SHOULD_ADD_APP_HERE % \
                                                            {
                                                                'path': directory 
                                                            }
                            should_add_app = console.choice_dialog(
                                                    message,
                                                    choices = ['yes','no'],
                                                    invalid_phrase = messages.INVALID_INPUT
                                                )
                            if should_add_app == 'yes':
                                assert(create_new == False)
                                if path_utils.dir_name_acceptable(directory):
                                    break
                                else:
                                    print messages.format_msg_bad_dir_name(directory)
                                    directory = None
                                    continue
                            else:
                                directory = None
                                continue
                        else:
                            assert(directory != None)
                            if path_utils.dir_name_acceptable(directory):
                                create_new = True
                                break
                            else:
                                print messages.format_msg_bad_dir_name(directory)
                                directory = None
                                continue
                    else:
                        print messages.format_msg_dir_unclean_django(directory)
                        directory = None
                        continue
                else:
                    #creates dir
                    message = messages.format_msg_create(directory) 
                    should_create_new = console.choice_dialog(
                                        message, 
                                        choices = ['yes','no'],
                                        invalid_phrase = messages.INVALID_INPUT
                                    )
                    if should_create_new == 'yes':
                        if path_utils.dir_name_acceptable(directory):
                            create_new = True
                            break
                        else:
                            print messages.format_msg_bad_dir_name(directory)
                            directory = None
                            continue
                    else:
                        directory = None
                        continue
            else:
                print messages.format_msg_dir_not_writable(directory)
                directory = None
                continue

        deploy_askbot(directory, create_new, options)
    else:
        directory = check_directory(directory, options)
        create_new = True
        if directory==None:
            raise Exception("the directory you choosed is invalid")
        #TODO middle steps!
        if path_utils.can_create_path(directory):
            if os.path.exists(directory):
                if path_utils.path_is_clean_for_django(directory):
                    if path_utils.has_existing_django_project(directory):
                        if options.verbosity >= 1:
                            print "Integrating askbot to your current app"
                        create_new=False
                    else:
                        assert(directory != None)
                        if path_utils.dir_name_acceptable(directory):
                            pass
                        else:
                            raise Exception(messages.format_msg_bad_dir_name(directory))
                else:
                    raise Exception(messages.format_msg_dir_unclean_django(directory))
            else:
                if path_utils.dir_name_acceptable(directory):
                    pass
                else:
                    raise Exception(messages.format_msg_bad_dir_name(directory))
        else:
            raise Exception(messages.format_msg_dir_not_writable(directory))

        deploy_askbot(directory, create_new, options)

#separated all the directory creation process to make it more useful

def deploy_askbot(directory, create_new, options):
    '''function that copies the templates'''
    help_file = path_utils.get_path_to_help_file()
    if create_new:
        path_utils.create_path(directory)
        path_utils.deploy_into(directory, new_project = True, 
                verbosity = options.verbosity)
        if options.verbosity >= 1:
            print messages.HOW_TO_DEPLOY_NEW % {'help_file': help_file}
    else:
        path_utils.deploy_into(directory, new_project = False, 
                verbosity = options.verbosity)
        if options.verbosity >= 1:
            print messages.HOW_TO_ADD_ASKBOT_TO_DJANGO % {'help_file': help_file}

def check_directory(directory, options):
    directory = os.path.normpath(directory)
    directory = os.path.abspath(directory)

    if os.path.isfile(directory):
        directory = None
        if options.verbosity >= 1:
            print messages.CANT_INSTALL_INTO_FILE % {'path':directory}

    return directory
