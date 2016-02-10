[tar]
webroot=/var
webroot_exclude=
[mysql]
db=example1.com
[postgresql]
db=testdb
user=backup_usr
passwd=backup_pass

