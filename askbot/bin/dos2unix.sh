#please take care not to dos2unix anything in your .git directory
#because that will probably break your repo
dos2unix `find . -name '*.py'`
dos2unix `find . -name '*.po'`
dos2unix `find . -name '*.js'`
dos2unix `find . -name '*.css'`
dos2unix `find . -name '*.txt'`
dos2unix `find ./sphinx -type f`
dos2unix `find ./cron -type f`
dos2unix settings_local.py.dist
dos2unix README
dos2unix INSTALL
