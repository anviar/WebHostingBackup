#!/usr/bin/python

import os,sys,time,threading,subprocess
import ConfigParser
import boto3
from boto3.s3.transfer import S3Transfer

config = ConfigParser.ConfigParser()
config.read('/etc/backup.conf')

workdir=config.get('general', 'workdir')+'/restore'
keep_mode=config.getboolean('general', 'keep')

if not os.path.isdir(workdir):
	try:
		os.mkdir(workdir)
	except:
		print ('Workdir not found:'+workdir)

amazon_client = boto3.client(
			's3',
			aws_access_key_id=config.get('amazon', 'aws_access_key_id'),
			aws_secret_access_key=config.get('amazon', 'aws_secret_access_key'),
			region_name=config.get('amazon', 'region')
		)
amazon_transfer = S3Transfer( amazon_client )
class filesThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = False
		self.name = "files-restore"
	def run(self):
		files=[]
		if len(sys.argv) > 1:
		        datestamp=sys.argv[1]
		else:
		        datestamp=None
		for key in sorted(amazon_client.list_objects(Bucket=config.get('amazon', 'bucket'),Prefix="files_")['Contents'], key=lambda k: k['LastModified'], reverse=True):
			if datestamp is not None:
				if key['Key'].endswith(datestamp+".tar.gz"):
					datestamp=None
				else:
					continue
			files.insert(0,key['Key'])
			if key['Key'].startswith("files_full"):
				break
		for afile in files:
			if not os.path.isfile(workdir+'/'+afile):
				print "%s: Downloading %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), afile)
				amazon_transfer.download_file(config.get('amazon', 'bucket'),afile,workdir+'/'+afile)
			print "%s: Unpacking %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), afile)
	                tar_comm=["tar","--directory=/","-xf",workdir+'/'+afile]
	                for path in config.get('files','restore').split(','):
        	                tar_comm.append(path[1:])
			devnull = open(os.devnull, 'w')
			subprocess.call(tar_comm,stderr=devnull)
			devnull.close()
			if not keep_mode:
				print "%s: Removing %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), afile)
				os.remove(workdir+'/'+afile)

class mysqlThread(threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self.daemon = False
                self.name = "mysql-backup"
        def run(self):
		for db in config.get('mysql', 'databases').split(','):
	                if len(sys.argv) > 1:
	                        datestamp=sys.argv[1]
			else:
				datestamp=str('')

			afile=amazon_client.list_objects(Bucket=config.get('amazon', 'bucket'),Prefix='mysql_'+db+'_'+datestamp,Delimiter='/')['Contents'][-1]['Key']
			if not os.path.isfile(workdir+'/'+db+'.sql.bz2'):
				print "%s: Downloading %s as %s " % (time.strftime('%Y-%m-%d %H:%M:%S'), afile, db+'.sql.bz2')
				amazon_transfer.download_file(config.get('amazon', 'bucket'),afile,workdir+'/'+db+'.sql.bz2')
			print "%s: Restoring DB %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), db)
			mysql_decompressor=subprocess.Popen(["bzcat",workdir+'/'+db+'.sql.bz2'],stdout=subprocess.PIPE)
			mysql_restore=subprocess.Popen(["mysql","-u"+config.get('mysql', 'user'),"-p"+config.get('mysql', 'password'),db],stdin=mysql_decompressor.stdout)
			mysql_decompressor.stdout.close()
			mysql_restore.communicate()
			if not keep_mode:
				print "%s: Removing %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), db+'.sql.bz2')
				os.remove(workdir+'/'+db+'.sql.bz2')

files_t=filesThread()
mysql_t=mysqlThread()

files_t.start()
mysql_t.start()


