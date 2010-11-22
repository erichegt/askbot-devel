"""
module for deploying askbot
"""
import os.path
from askbot.utils import console
from askbot.deployment import messages
from askbot.deployment import path_utils

def startforum():
    """basic deployment procedure
    asks user several questions, then either creates
    new deployment (in the case of new installation)
    or gives hints on how to add askbot to an existing
    Django project
    """
    #ask 
    print messages.DEPLOY_PREAMBLE

    directory = None #directory where to put stuff
    create_new = False #create new django project or not
    where_to_deploy_msg = messages.WHERE_TO_DEPLOY
    while directory is None:

        directory = raw_input(where_to_deploy_msg + ' ')

        where_to_deploy_msg = messages.WHERE_TO_DEPLOY_QUIT

        directory = os.path.normpath(directory)
        directory = os.path.abspath(directory)

        if os.path.isfile(directory):
            print messages.CANT_INSTALL_INTO_FILE % {'path':directory}
            directory = None
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

    help_file = os.path.join(directory, 'askbot', 'doc', 'INSTALL')
    if create_new:
        path_utils.create_path(directory)
        path_utils.deploy_into(directory, new_project = True)
        print messages.HOW_TO_DEPLOY_NEW % {'help_file': help_file}
    else:
        path_utils.deploy_into(directory, new_project = False)
        print messages.HOW_TO_ADD_ASKBOT_TO_DJANGO % {'help_file': help_file}
