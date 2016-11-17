from widow import Widow
from console import Console
import re
from threading import Lock
from time import time
from message import Message

# class: LoginSpider
# description: This spider is responsible for finding logins on a domain, and stores them to: login_urls
class LoginSpider(Widow):
	CLEANUP_REGEX = re.compile(r'\n')
	FORM_REGEX = re.compile(r'<form(.*?)<\/form>')	
	LOGIN_FORM_REGEX = re.compile(r'input\stype\=[\"\']password[\"\']')
	TEXT_FIELD_REGEX = re.compile(r'input\stype\=[\"\'](text)[\"\']')
	login_urls = None
	lastUpdate = None
	updateTime = None
	message = Message()
	statsLock = None
	
	def __init__(self,depth):
		Widow.__init__(self,depth)
		self.login_urls = list()
		self.updateTime = 10
		self.verbose = False
		self.statsLock = Lock()

	# function: parse - Overriden
	# param: Response	- The Response object to parse
	# description: Parses the response object, for loot this spider seeks
	def parse(self,response):
		Widow.parse(self,response)
		forms = list()
		html = self.CLEANUP_REGEX.subn('',response.text)[0]
		if self.FORM_REGEX.search(html):
			forms = self.FORM_REGEX.findall(html)	
			for form in forms:
				if self.LOGIN_FORM_REGEX.search(form):
					fields = self.LOGIN_FORM_REGEX.findall(form)
					if len(fields) == 1:
						if response.url not in self.login_urls:
							self.login_urls.append(response.url)
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
			message = self.message.infoMessage("Statistics ")
			message += self.message.format("pages-crawled: %s",['dim'])%pagesCrawled
			message += self.message.format(" total-logins-forms-found: %s",['dim'])%totalLoginsFound
			with self.statsLock:
				print(message)
