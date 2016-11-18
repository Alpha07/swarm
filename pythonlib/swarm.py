from console import Console
from hive import HttpHive
from login_spider import LoginSpider
import requests
import random
import re

# class: Swarm
# description: This is The main driving class of the swarm bruteforcer
class Swarm(object):
	VERSION = 0.021
	UPDATE_REGEX = re.compile(r'VERSION.*\">([\d\.]+)') 
	username = None
	usernameFile = None
	passwordFile = None
	target = None
	threads = None
	verbose = None
	updateTime = None
	checkTor = None
	useTor = None
	useSqlInjections = None
	shouldCrawl = None
	depth = None
	author = None
	killSignal = None
	console = None
	spider = None
	hive = None
	proxies = None

	# function: __init__
	# param: username(str)			- The username to use for the bruteforce
	# param: usenameFile(str)		- The username file to use for the bruteforce
	# param: passwordFile(str)		- The password file to use for the bruteforce
	# param: target(str)			- The URL to bruteforce
	# param: threads(int)			- Total threads to use for the processj
	# param: verbose(Boolean)		- Verbose output or not
	# param: tor(Boolean)			- Use tor or not
	# param: checkTor(Boolean)		- Only continue if tor is enabled
	# param: useSqlInjections(Boolean)	- Use SQL injections during this bruteforce attempt
	# param: shouldCrawl(Boolean)		- Should Crawl or not
	# param: depth(int)			- Crawl depth
	# param: updateTime(int)		- Time to show statistics in seconds
	# description: Constructor
	def __init__(self,username,usernameFile,passwordFile,target,threads,verbose,tor,checkTor,useSqlInjections,shouldCrawl,depth,updateTime):
		self.username = username
		self.usernameFile = usernameFile
		self.passwordFile = passwordFile
		self.target = target
		self.threads = threads
		self.verbose = verbose
		self.updateTime = updateTime
		self.checkTor = checkTor
		self.useTor = tor
		self.useSqlInjections = useSqlInjections
		self.shouldCrawl = shouldCrawl
		self.author = "szech696"
		self.depth = depth
		self.killSignal = False
		self.console = Console()
		self.proxies = None
#		self.checkVersion()

	# function: getCrawlingMessage
	# return: str
	# description: Gets the crawling message
	def getCrawlingMessage(self):
		message = ""
		messageDict = {	"Depth":self.depth,
				"Using-Tor":False,
				"Threads":self.threads}
		message = self.getLogo()
		if self.useTor:
			messageDict["Using-Tor"] = self.checkIfTorEnabled()
		message += self.console.format('Author: %s\n',['dim'])%self.console.format(self.author,['magenta'])
		message += self.console.format('Target: %s\n',['dim'])%self.console.format(self.target,['yellow'])	
		for key in sorted(messageDict.keys()):
			if messageDict[key]:
				message += self.console.format(key+": %s\n",['dim'])%(self.console.format(str(messageDict[key]),['white','bold']))
			else:
				message += self.console.format(key+": %s\n",['dim'])%(self.console.format("None",['red','bold']))
		return message

	# function: getBruteforcingMessage
	# return: str
	# description: Gets the bruteforcing message
	def getBruteforcingMessage(self):
		message = ""
		messageDict = {	"Threads":self.threads,
				"Username":self.username,
				"Username-File":self.usernameFile,
				"Password-File":self.passwordFile,
				"Using-Tor":self.useTor,
				"Attempting SQL-Injection":self.useSqlInjections }
		message = self.getLogo()
		message += self.console.format('Author: %s\n',['dim'])%self.console.format(self.author,['magenta'])
		message += self.console.format('Target: %s\n',['dim'])%self.console.format(self.target,['yellow'])	
		message += self.console.format('Base-Payload: %s\n',['dim'])%self.console.format(str(self.hive.examplePayload),['red','normal'])	
		for key in sorted(messageDict.keys()):
			if messageDict[key] or messageDict[key] == False:
				message += self.console.format(key+": %s\n",['dim'])%(self.console.format(str(messageDict[key]),['white','bold']))
			else:
				message += self.console.format(key+": %s\n",['dim'])%(self.console.format("None",['red','bold']))
		if not self.hive.examplePayload:
			message = self.criticalSignal("No login forms found on: %s\n"%self.target)
			self.killSignal = True
		return message

	# function: startCrawling
	# description: Starts the crawling process of Swarm
	def startCrawling(self):
		message = self.getCrawlingMessage()	
		print(message)
		validateDict = self.getValidateDict()
		message = ''
		for key in validateDict.keys():
			if validateDict[key]:
				if key == 'url-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'depth-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'tor-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'tor-message':
					try:
						message += validateDict[key] 
					except TypeError:
						pass
		if self.killSignal:	
			message += self.criticalSignal("There were errors exiting")
			print(message)
			exit()	
		print(message)
		self.spider = LoginSpider(self.depth)
		self.spider.url = self.target
		self.spider.updateTime = self.updateTime
		self.spider.proxies = self.proxies
		self.spider.crawl(self.threads)
		message = self.successMessage("Finished Crawling %d pages, and found %d login forms\n"%(self.spider.crawledPages,len(self.spider.login_urls)))
		for url in self.spider.login_urls:
			message += '\t%s\n'%url
		print(message)

	# function: startBruteforcing
	# description: Starts the bruteforcing process of Swarm
	def startBruteforcing(self):
		validateDict = self.getValidateDict()
		message = ''
		for key in sorted(validateDict.keys()):
			if validateDict[key]:
				if key == 'url-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'user-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'pass-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
				if key == 'tor-error-message':
					message += validateDict[key] + '\n'
					self.killSignal = True
		if self.killSignal:	
			message += self.criticalSignal("There were errors exiting")
			print(message)
			exit()
		self.hive = HttpHive()	
		self.hive.target = self.target
		self.hive.usernameFile = self.usernameFile
		self.hive.username = self.username
		self.hive.passwordFile = self.passwordFile
		self.hive.proxies = self.proxies
		self.hive.setup()	
		message = self.getBruteforcingMessage()
		try:
			message += validateDict['tor-message']
		except TypeError:
			pass
		if self.killSignal:
			message += self.criticalSignal("There were errors exiting")
			print(message)
			exit()
		print(message)
		self.hive.testSQLInjections = self.useSqlInjections
		self.hive.verbose = self.verbose
		self.hive.start(self.threads)	
		self.hive.showPostStatisticsMessage()
	
	# function: checkTor
	# return: Boolean
	# description: Verifies tor is in use
	def checkIfTorEnabled(self):
		isUsingTor = False
		self.proxies = {'http':'socks5://localhost:9050','https':'socks5://localhost:9050'}
		try:
			response = requests.get('https://check.torproject.org/', proxies=self.proxies)
                        if HttpHive.CHECK_TOR_REGEX.search(response.text):
                        	isUsingTor = True
                except Exception as e:
                	print(e)
		return isUsingTor
	
	# function: getLogo
	# return: str
	# description: returns a random logo from swarm-data
	def getLogo(self):
		logo = ''
        	for line in open('./data/swarm-data','r').readlines():
               		logo += line
        	logos = logo.split('(-$-)')
        	logo = random.choice(logos)
        	logo = logo + "\n"
		logo = self.console.format(logo,['yellow','bold'])
		logo += self.console.format("SWARM\n",['magenta','bold'])
        	return logo

	# function: getBasePayload
	# return: str
	# description: Returns the base-payload, for HttpHive Object
	def getBasePayload(self):
		payload = ''
		return payload
	
	# function: getValidateDict
	# return: dict
	# description: Does a last check on settings before swarm begins, and returns a dictionary of messages, all messages besides
	#	check-tor-message should be regarded as errors, check-tor-message can be both an error and informative message
	#	Example is if tor is being used, and checkTor is True, then the message will be informative that tor is being used properly
	def getValidateDict(self):
		validateDict = dict()
		validateDict['url-error-message'] = None
		validateDict['user-error-message'] = None
		validateDict['pass-error-message'] = None
		validateDict['depth-error-message'] = None
		validateDict['tor-error-message'] = None
		validateDict['tor-message'] = None
		if not self.username:
			if not self.usernameFile:
				validateDict['user-error-message'] = self.criticalSignal('username file was not specified. Please specify with --user-file=<FILE>') 
		if not self.passwordFile:
			validateDict['pass-error-message'] = self.criticalSignal('password file was not specified. Please specify with --pass-file=<FILE>') 	
		if self.shouldCrawl == True:
			if not self.depth:
				validateDict['depth-error-message'] = self.criticalSignal('the maximum depth was not specified. Please specify with --crawl=<DEPTH>')	
		if not self.target:
			validateDict['url-error-message'] = self.criticalSignal('no url specified. Please specify with --url=<URL>')		
		if self.useTor == True or self.checkTor == True:
			if not self.checkIfTorEnabled() or not self.useTor:
				validateDict['tor-error-message'] = self.criticalSignal('It appears tor is not working properly. Did you use --tor? You could be missing dependencies')
			else:
				validateDict['tor-message'] = self.successMessage("It appears tor is working properly")
		return validateDict

	# function: criticalSignal
	# param: str		- The message to format to critical	
	# return: str		- The orginal message formatted as critical
	# description: Sends the critical message to swarm to exit, and returns a relevant message to display to the user
	def criticalSignal(self,message):
		criticalmessage = self.console.getTimeString()
		criticalmessage += self.console.format(' [!!] %s'%message,['red','bold'])
		return criticalmessage	
	
	# function: successLog
	# param: str		- The message to format to successful format
	# return: str		- The orginal message formatted as successful
	# description: Sends a succuess message to be formatted as succues, and returns a relevant message to display to the user
	def successMessage(self,message):
		successLog = self.console.getTimeString()
		successLog += self.console.format(' [+] %s'%message,['green','bold'])
		return successLog
	
	# function: checkVersion
	# description: Checks for new versions of swarm, notifies the user if one is available
	def checkVersion(self):
		try:
			response = requests.get('https://github.com/szech696/swarm/blob/master/pythonlib/swarm.py')	
			if self.UPDATE_REGEX.search(response.text):
				version = self.UPDATE_REGEX.findall(response.text)[0]
				if float(version) > self.VERSION:
					message = self.successMessage("Version %s available, update at https://github.com/szech696/swarm/\n"%version)
					print(message)
		except:
			pass
