#!/usr/bin/python

import os,sys,threading,Queue,time,ConfigParser,random
import tarfile

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
		config = ConfigParser.ConfigParser()
		config.read(workdir+'/website.conf/'+self.domain)
		try:
			webroot=config.get('tar', 'webroot')
		except:
			tar_thread=threading.Thread( target=tarJob, name="tar-"+self.domain, args=(self.domain, webroot) )
		else:
			tar_thread=threading.Thread( target=tarJob, name="tar-"+self.domain, args=(self.domain, webroot) )
			tar_thread.daemon=False
			tar_thread.start()
			#tar_thread.join()
		try:
			mysql_db=config.get('mysql', 'db')
		except:
			tar_thread=threading.Thread( target=tarJob, name="tar-"+self.domain, args=(self.domain, webroot) )
		else:
			mysql_thread=threading.Thread( target=mysqlJob, name="mysql-"+self.domain, args=(self.domain, ) )
			mysql_thread.daemon=False
			mysql_thread.start()
			#mysql_thread.join()
		while ( tar_thread.isAlive() or mysql_thread.isAlive() ):
			print "Waiting %s" % self.domain
			time.sleep(1)
		start_domainThread()
			

def tarJob(domain, webroot):
	time.sleep (random.randint(2,10))
	tar = tarfile.open(workdir+'/archives/'+domain+".tar.gz", "w:gz")
	tar.add(webroot)
	tar.close()
	print "Done tar %s %s" % (domain, webroot)

def mysqlJob(domain):
	time.sleep(random.randint(1,5))
	print "Done SQL %s" % domain

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

#time.sleep(5)
#print threading.enumerate()
