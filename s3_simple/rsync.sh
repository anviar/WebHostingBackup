#!/bin/bash

lockfile=/tmp/rsync.lock

if [[ -f ${lockfile} ]]
then
	echo "Error: lock file exist ${lockfile}"
	exit 1
else
	touch ${lockfile}
fi

echo "$(date): MySQL dump started"
for db in $(mysql --skip-column-names -e "SHOW DATABASES"|egrep -v "^performance_schema$|^information_schema$")
do
	if [[ ${db} == "mysql" ]]
	then
		mysqldump --hex-blob --add-drop-table --events --ignore-table=mysql.event ${db}|bzip2 >/opt/dnp/mysqldump/${db}.sql.bz2
	else
		mysqldump --hex-blob --add-drop-table ${db}|bzip2 >/opt/dnp/mysqldump/${db}.sql.bz2
	fi
done

cd /opt/dnp
tar -jcf /opt/dnp/mysqldump/app.tbz2 2.*

echo "$(date): data sync started"
rsync -rlp --stats --ignore-missing-args /opt/dnp/data/ rsync://standby/data
rsync -rlp --stats --ignore-missing-args /opt/dnp/mysqldump/ rsync://standby/mysqldump

echo "$(date): all done"
rm -f ${lockfile}
