from widow import Widow
from console import Console
import re
from threading import Lock
from time import time
from message import Message

# class: LoginSpider
# description: This spider is responsible for finding logins on a domain, and stores them to: login_urls
class LoginSpider(Widow):
	CLEANUP_REGEX = re.compile(r'[(\s\s)|\t|\n]+')
	FORM_REGEX = re.compile(r'<form(.*?)<\/form>',re.I)	
	LOGIN_FORM_REGEX = re.compile(r'input\stype\=[\"\']password[\"\']',re.I)
	TEXT_FIELD_REGEX = re.compile(r'input\stype\=[\"\'](text)[\"\']',re.I)
	WORD_REGEX = None
	minimumWordLength = None
	maximumWordLength = None
	login_urls = None
	wordlist = None
	lastUpdate = None
	updateTime = None
	message = Message()
	statsLock = None
	
	def __init__(self,depth,minimumWordLength,maximumWordLength):
		Widow.__init__(self,depth)
		self.minimumWordLength = minimumWordLength
		self.maximumWordLength = maximumWordLength
		self.WORD_REGEX = re.compile(r'[\'\"\s>]([a-zA-Z]{%d,%d})[\s\.<\?\!\'\"\,]'%(self.minimumWordLength,self.maximumWordLength))
		self.login_urls = list()
		self.wordlist = list()
		self.updateTime = 10
		self.verbose = False
		self.statsLock = Lock()

	# function: parse - Overriden
	# param: Response	- The Response object to parse
	# description: Parses the response object, for loot this spider seeks
	def parse(self,response):
		Widow.parse(self,response)
		forms = list()
		html = self.CLEANUP_REGEX.subn(' ',response.text)[0]
		if self.FORM_REGEX.search(html):
			forms = self.FORM_REGEX.findall(html)	
			for form in forms:
				if self.LOGIN_FORM_REGEX.search(form):
					fields = self.LOGIN_FORM_REGEX.findall(form)
					if len(fields) == 1:
						if response.url not in self.login_urls:
							self.login_urls.append(response.url)
		if self.WORD_REGEX.search(html):
			words = self.WORD_REGEX.findall(html)
			for word in words:
				if word not in self.wordlist:
					self.wordlist.append(word)	
		self.showStatistics()

	# function: showStatistics
	# description: Show statistics for this spider, how many pages crawled, how many logins found
	def showStatistics(self):
		if not self.lastUpdate:
			self.lastUpdate = 0
		if (time()-self.lastUpdate) > self.updateTime:
			self.lastUpdate = time()
			timeString = self.message.format(self.message.getTimeString(),['white'])
			pagesCrawled = self.message.format(str(self.crawledPages),['white'])	
			totalLoginsFound = len(self.login_urls)
			totalLoginsFound = self.message.format(str(totalLoginsFound),['green'])
			totalWordsFound = self.message.format(str(len(self.wordlist)),['green'])
			message = self.message.infoMessage("Statistics ")
			message += self.message.format("pages-crawled: %s",['dim'])%pagesCrawled
			message += self.message.format(" total-logins-forms-found: %s",['dim'])%totalLoginsFound
			message += self.message.format(" total-words-found: %s",['dim'])%totalWordsFound
			with self.statsLock:
				print(message)
