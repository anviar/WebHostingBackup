[tar]
webroot=/var
webroot_exclude=
[mysql]
db=testdb
user=backup_usr
passwd=backup_pass
[postgresql]
db=testdb
user=backup_usr
passwd=backup_pass

