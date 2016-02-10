[tar]
webroot=/var
webroot_exclude=
[mysql]
db=example.com
[postgresql]
db=testdb
user=backup_usr
passwd=backup_pass

