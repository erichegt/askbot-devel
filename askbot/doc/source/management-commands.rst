==========================
Askbot management commands
==========================

There are a number of command line utilities help the forum administrator
perform a range of tasks such as add or revoke administration privileges, back up and restore
the forum data, fix database errors if such occur, etc.

To run these commands there is a general pattern::

    cd project_directory
    python manage.py some_command [possible arguments and parameters]

I.e. the commands are generally run from the project directory (the same 
one that contains your settings.py file) and they may use additional parameters and options.

Data and User administration commands
=====================================

The bulk of the management commands fall into this group and will probably be the most frequently used.

+---------------------------------+-------------------------------------------------------------+
| command                         | purpose                                                     |
+=================================+=============================================================+
| `add_admin <user_id>`           | Turn user into an administrator                             |
|                                 | `<user_id>` is a numeric user id of the account             |
+---------------------------------+-------------------------------------------------------------+
| `remove_admin <user_id>`        | Remove admin status from a user account - the opposite of   |
|                                 | the `add_admin` command                                     |
+---------------------------------+-------------------------------------------------------------+
| `dump_forum [--dump-name        | Save forum contents into a file. `--dump-name` parameter is |
| some_name`]                     | optional                                                    |
+---------------------------------+-------------------------------------------------------------+
| `load_forum <file_name>`        | Load forum data from a file saved by the `dump_forum`       |
|                                 | command                                                     |
+---------------------------------+-------------------------------------------------------------+
| `rename_tags --from <from_tags> | Rename, merge or split tags. User ID is the id of the user  |
| --to <to_tags> --user-id        | who will be assigned as the performer of the retag action.  |
| <user_id>`                      | If more than is in the `--from` or the `--to` parameters    |
|                                 | then that parameter quoted, e.g. `--to "tag1 tag2".         |
+---------------------------------+-------------------------------------------------------------+

Batch jobs
==========

Batch jobs are those that should be run periodically. A program called `cron` can run these commands at the specified times (please look up futher information about `cron` elsewhere).

+----------------------+-------------------------------------------------------------+
| command              | purpose                                                     |
+======================+=============================================================+
| `send_email_alerts`  | Dispatches email alerts to the users according to           |
|                      | their subscription settings. This command does not          |
|                      | send iinstant" alerts because those are sent automatically  |
|                      | and do not require a separate command.                      |
|                      | The most frequent alert setting that can be served by this  |
|                      | command is "daily", therefore running `send_email_alerts`   |
|                      | more than twice a day is not necessary.                     |
+----------------------+-------------------------------------------------------------+

Data repair commands
====================

Under certain circumstances (especially when using MySQL database with MyISAM storage engine or when venturing to adapt the software to your needs) some records in the database tables may become internally inconsistent. The commands from this section will help fix those issues:

* `add_missing_subscriptions` - adds default values of email subscription settings to users that lack them
* `fix_answer_counts` - recalculates answer counts for all questions
* `fix_revisionless_posts` - adds a revision record to posts that lack them

The commands are safe to run at any time, also they do not require additional parameters. In the future all these will be replaced with just one simple command.
