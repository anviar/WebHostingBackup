#!/usr/bin/python

import os,sys,threading,Queue,time,ConfigParser,subprocess,random

workdir=os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) > 1:
	try:
		maxJobs=int(sys.argv[1])
	except ValueError:
		maxJobs=1
		print "Warrning: wrong number of threads \"%s\"" % sys.argv[1]
else:
	maxJobs=1

class domainThread(threading.Thread):
	def __init__(self, domain):
		threading.Thread.__init__(self)
		self.daemon = False
		self.domain = domain
		self.name = "mainthread-"+domain
	def run(self):
		print "Processing %s - %s" % (self.domain,self.name)
		child_threads = []
		config = ConfigParser.ConfigParser()
		config.read(workdir+'/website.conf/'+self.domain)
		try:
			webroot=config.get('tar', 'webroot')
		except:
			pass
		else:
			tar_thread=threading.Thread( target=tarJob, name="tar-"+self.domain, args=(self.domain, webroot) )
			tar_thread.daemon=False
			child_threads.append(tar_thread)
		try:
			mysql_db=config.get('mysql', 'db')
		except:
			pass
		else:
			mysql_thread=threading.Thread( target=mysqlJob, name="mysql-"+self.domain, args=(self.domain,mysql_db) )
			mysql_thread.daemon=False
			child_threads.append(mysql_thread)
		for thread in child_threads:
			thread.start()
		for thread in child_threads:
			thread.join()
		start_domainThread()
			

def tarJob(domain, webroot):
	devnull = open(os.devnull, 'w')
	subprocess.call(["tar","-zcf",workdir+'/archives/'+domain+".tar.gz",webroot],stderr=devnull)
	devnull.close()
	print "Done tar %s %s" % (domain, webroot)

def mysqlJob(domain, db):
	sql_file=open(workdir+'/archives/'+domain+".sql.bz2", "wb")
	mysql_dump=subprocess.Popen(["mysqldump",db], stdout=subprocess.PIPE)
	mysql_compressor=subprocess.Popen("bzip2", stdin=mysql_dump.stdout, stdout=sql_file)
	mysql_dump.stdout.close()
	mysql_compressor.communicate()
	sql_file.close()
	print "Done MySQL %s" % domain

def start_domainThread():
	if not wQueue.empty():
		domain=wQueue.get()
		t=domainThread ( domain )
		t.start()

wQueue=Queue.Queue()
domains=os.listdir(os.path.dirname(os.path.realpath(__file__))+'/website.conf')
for domain in domains:
	wQueue.put(domain)

# Initiating main threads
count=0
while count < maxJobs:
	start_domainThread()
	count += 1

