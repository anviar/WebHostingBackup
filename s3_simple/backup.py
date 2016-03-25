#!/usr/bin/python

import os,sys,time,threading,subprocess
import ConfigParser,boto3
from boto3.s3.transfer import S3Transfer

config = ConfigParser.ConfigParser()
config.read('/etc/backup.conf')

workdir=config.get('general', 'workdir')
date=time.strftime("%Y-%m-%d")
incfile=workdir+"/files.snar"

transfer = S3Transfer( boto3.client(
			's3',
			aws_access_key_id=config.get('amazon', 'aws_access_key_id'),
			aws_secret_access_key=config.get('amazon', 'aws_secret_access_key'),
			region_name=config.get('amazon', 'region')
		))

if ( len(sys.argv) > 1 and sys.argv[1] == "-f" ) or not os.path.isfile(incfile):
	mode="full"
else:
	mode="inc"

class filesThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = False
		self.name = "files-backup"
	def run(self):
		print "%s: started %s - %s" % (time.strftime('%Y-%m-%d %H:%M:%S'),self.name,mode)
		paths=config.get('files','paths').split(',')
		exclude=config.get('files','exclude').split(',')
		tar_comm=["tar","-zcf",workdir+'/files.tar.gz','--listed-incremental='+incfile]
		if mode == "full":
			tar_comm.append('--level=0')
		for x in exclude:
			tar_comm.append('--exclude='+x)
		for p in paths:
			tar_comm.append(p)
		devnull = open(os.devnull, 'w')
		subprocess.call(tar_comm,stderr=devnull)
		devnull.close()
		print "%s: files saved on disk" % time.strftime('%Y-%m-%d %H:%M:%S')
		transfer.upload_file(workdir+'/files.tar.gz', config.get('amazon', 'bucket'), 'files_'+mode+'_'+date+'.tar.gz' )
		print "%s: files uploaded" % time.strftime('%Y-%m-%d %H:%M:%S')

class mysqlThread(threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self.daemon = False
                self.name = "mysql-backup"
        def run(self):
                print "%s: started %s " % (time.strftime('%Y-%m-%d %H:%M:%S'),self.name)
		databases=config.get('mysql', 'databases').split(',')
		dbuser=config.get('mysql', 'user')
		dbpass=config.get('mysql', 'password')
		for db in databases:
			sql_file=open(workdir+'/'+db+".sql.bz2", "wb+")
			mysql_dump=subprocess.Popen(["mysqldump","-u"+dbuser,"-p"+dbpass,db], stdout=subprocess.PIPE)
			mysql_compressor=subprocess.Popen("bzip2", stdin=mysql_dump.stdout, stdout=sql_file)
			mysql_dump.stdout.close()
			mysql_compressor.communicate()
			sql_file.close()
			print "%s: %s database saved on disk" % (time.strftime('%Y-%m-%d %H:%M:%S'),db)
		for db in databases:
			transfer.upload_file(workdir+'/'+db+".sql.bz2", config.get('amazon', 'bucket'), "mysql_"+db+'_'+date+".bz2" )
			print "%s: %s database uploaded" % (time.strftime('%Y-%m-%d %H:%M:%S'),db)


mysql_t=mysqlThread()
files_t=filesThread()

files_t.start()
mysql_t.start()

