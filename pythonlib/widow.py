import re
import requests
from bloomfilter import BloomFilter
from threading import Thread, Lock
from urlparse import urlparse, urljoin
import random
from console import Console

# class: Widow
# author: szech696
# description: Widow is a general purpose threaded Spider that recursively crawls via the Depth First Search algorithim
class Widow(object):
	bloomfilter = None
	size = None
	proxies = None
	agentList = None
	maxLevel = None
	url = None
	threadLock = None
	checkThreadLock = None
	# Only None fragmented URLS are allowed. To allow Fragmented URLS, add: '#' to the allowed characters in the regex
	LINK_REGEX = re.compile(r'<a\shref\=[\"\']([~\/\w_\-\=\.\%\&\!\+\?\[\]\(\)@;]*?)[\"\']')
	# Only allowed extensions
	WHITE_LIST_REGEX = re.compile(r'([\.(php)html])$')
	# Checks for an extension
	FILE_EXTENSION_REGEX = re.compile(r'(\.[A-Za-z]+)$')
	netloc = None
	workers = None
	totalThreads = None
	crawledPages = None
	verbose = None
	console = None
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


	# function: __init__
	# param: int	- the maximum depth this spider should crawl
	# description: constructor
	def __init__(self,maxLevel=4):
		proxies = None
		self.size = 100000000
		self.bloomfilter = BloomFilter(self.size)
		self.maxLevel = maxLevel
		self.threadLock = Lock()
		self.checkThreadLock = Lock()
		self.totalThreads = 0
		self.crawledPages =0
		self.verbose = True 
		self.console = Console()

	# function: crawl
	# param: theads
	# description: Begins the crawling processes of Widow
	def crawl(self,threads=1):
		threads_still_alive = True
		self.workers = list()
		self.totalThreads = threads
		headers = self.__getHeaders__()
		response = requests.get(self.url,headers=headers,proxies=self.proxies)
		links = self.__findLinks__(response)
		self.netloc = urlparse(response.url)[1]
		for index in range(threads-1):
			# Meant to finish right away. Most of the actual thread creation within: self.__checkOnThreads__
			self.workers.append(Thread(target=self.__depthFirst__,args=([],)))
		# This thread will branch into many threads from within __checkOnThreads__
		self.workers.append(Thread(target=self.__depthFirst__, args=(links,)))	
		for thread in self.workers:
			with self.checkThreadLock:
				try:
					thread.start()
				except RuntimeError:
					pass
		# Not very elegant, but owell
		for thread in self.workers:
			try:
				thread.join()
			except RuntimeError:
				pass
		while threads_still_alive:
			threads_still_alive = False
			for thread in self.workers:
				try:
					thread.join()
				except RuntimeError:
					pass
			for thread in self.workers:
				if thread.isAlive():
					threads_still_alive = True

	# function: __depthFirst__
	# param: [str]	- the links the thread using this function still needs to parse
	# param: int	- the current level in this crawl
	# description: recusively crawls with the depth first search algorithim
	def __depthFirst__(self, links, currentLevel=0):
		links = self.__checkOnThreads__(links,currentLevel)
		for link in links:
			# If this link is not being tracked, and current level is less then the max level, and the netloc is within the orgininal netloc
			if not self.bloomfilter.inArray(link) and currentLevel < self.maxLevel and self.netloc == urlparse(link)[1]:
				with self.threadLock:
					self.bloomfilter.append(link)
				headers = self.__getHeaders__()
				if self.verbose == True:
					with self.threadLock:
						message = self.console.getTimeString()
						message += self.console.format(' Crawled: %s',['dim'])%(self.console.format(link,['bold','yellow']))	
						print(message)
				response = requests.get(link,headers=headers,proxies=self.proxies)
				newLinks = self.__findLinks__(response)
				self.parse(response)
				self.__depthFirst__(newLinks, currentLevel+1)
	
	# function: __checkOnThreads__
	# description: Checks to see if any threads are available to split the load
	def __checkOnThreads__(self,links,currentLevel):
		for index in range(len(self.workers)):
			with self.checkThreadLock:
				if not self.workers[index].isAlive() and len(links) > len(self.workers):	
					self.workers.remove(self.workers[index])
					newThread = Thread(target=self.__depthFirst__,args=(links[len(links)/2:],currentLevel))
					self.workers.append(newThread)
					newThread.start()
					links = links[0:len(links)/2]
					break
		return links

	# function: __findLinks__
	# param: response
	# return: [str]		- Returns an array of links
	# description: Finds all the links from the response
	def __findLinks__(self,response):
		links = list()
		if self.LINK_REGEX.search(response.text):
			groups = self.LINK_REGEX.findall(response.text)
			for link in groups:
				if len(link) > 0:
					# if there is a file extension on the page
					if self.FILE_EXTENSION_REGEX.search(link):
						# then it must be valid with [(php)html]
						if self.WHITE_LIST_REGEX.search(link):
							links.append(urljoin(response.url,link))
					# No, file extension, adding link
					else:
						links.append(urljoin(response.url,link))
		return links

	# function: __getHeaders__
	# description: returns the headers to be used with the next GET
	def __getHeaders__(self):
		headers = {'Connection':'close','User-Agent':random.choice(self.userAgents)}
		return headers

	# function: parse - Override me
	# param: response	
	# description: Used to parse all response objects. Override for custom functionality
	def parse(self, response):
		self.crawledPages += 1	

