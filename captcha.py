# Going to use Selenium to solve Captchas

import re

class CaptchaSolver(object):
	def __init__(self):
		pass

	def detect(self,response):
		pass

# class: ReCaptchaSolver
# description: class to solve ReCaptcha type
class ReCaptchaSolver(CaptchaSolver):
	DETECT_REGEX = re.compile(r'recaptcha')	
	def __init__(self):
		pass
	
	# function: detect
	# param: response
	# return: Boolean
	# description: True if this type of captcha was found in the response object
	def detect(self,response):
		success = False
		if self.DETECT_REGEX.search(response.text):
			success = True
		return success

	def solve(self,response):
		pass
