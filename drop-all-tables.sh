mysql_username=''
mysql_database=''
mysqldump -u $mysql_username -p --add-drop-table --no-data $mysql_database | grep ^DROP 
#| mysql -u[USERNAME] -p[PASSWORD] [DATABASE]
