#!/usr/bin/env python3

import os
import sys
import time
import threading
import subprocess
import configparser
from boto3 import client as S3Client

config = configparser.ConfigParser()
config.read('/etc/backup.conf')

workdir = config.get('general', 'workdir')
date = time.strftime("%Y-%m-%d")
incfile = workdir + "/files.snar"
buffer_size = 32

s3 = S3Client(
            's3',
            aws_access_key_id=config.get('amazon', 'aws_access_key_id'),
            aws_secret_access_key=config.get('amazon', 'aws_secret_access_key'),
            region_name=config.get('amazon', 'region')
        )

if (len(sys.argv) > 1 and sys.argv[1] == "-f") or not os.path.isfile(incfile):
    mode = "full"
else:
    mode = "inc"


class filesThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = False
        self.name = "files-backup"

    def run(self):
        print("%s: started %s - %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), self.name, mode))
        paths = config.get('files', 'paths').split(',')
        exclude = config.get('files', 'exclude').split(',')
        tar_comm = ["nice", "-n", "19", "tar", "-zcf", '-', '--listed-incremental=' + incfile]
        if mode == "full":
            tar_comm.append('--level=0')
        for x in exclude:
            tar_comm.append('--exclude=' + x)
        for p in paths:
            tar_comm.append(p)
        devnull = open(os.devnull, 'w')
        with subprocess.Popen(tar_comm, stdout=subprocess.PIPE, stderr=devnull).stdout as dataStream:
            s3.upload_fileobj(dataStream, config.get('amazon', 'bucket'), 'files_' + mode + '_' + date + '.tar.gz')
        devnull.close()
        print("%s: files uploaded" % time.strftime('%Y-%m-%d %H:%M:%S'))


class mysqlThread(threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self.daemon = False
                self.name = "mysql-backup"

        def run(self):
            print("%s: started %s " % (time.strftime('%Y-%m-%d %H:%M:%S'), self.name))
            for db in config.get('mysql', 'databases').split(','):
                with subprocess.Popen("mysqldump -u"
                                      + config.get('mysql', 'user')
                                      + " -p" + config.get('mysql', 'password')
                                      + " -h" + config.get('mysql', 'host')
                                      + " --hex-blob --add-drop-table "
                                      + db
                                      + "|bzip2", stdout=subprocess.PIPE, shell=True).stdout as dataStream:
                    s3.upload_fileobj(dataStream, config.get('amazon', 'bucket'), "mysql_" + db + '_' + date + ".bz2")
                print("%s: %s database saved to cloud" % (time.strftime('%Y-%m-%d %H:%M:%S'), db))

mysql_t = mysqlThread()
files_t = filesThread()

files_t.start()
mysql_t.start()
