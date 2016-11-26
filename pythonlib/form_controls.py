import re
# class: Field
# description: Represents a field within a form
class Field:
	_name_ = None
	_value_ = None
	_type_ = None
	editable = None
	passwordFlag = None
	emailFlag = None

	# function: __init__
	# param: _name_(str)	- The name of the field
	# param: _value_(str) 	- The value of the field
	# param: _type_(str) 	- The type of the field
	# description: Constructor
	def __init__(self, _name_, _value_, _type_):
		self._name_ = _name_
		self._value_ = _value_
		self._type_ = _type_
		self.passwordFlag = False
		# This is an editable field within the form
		if self._type_ in ('text','password','email'):
			self.editable = True
			if self._type_ in 'password':
				self.passwordFlag = True
			elif self._type_ is 'email' or 'email' in self._name_.lower():
				self.emailFlag = True
				self._type_ = 'email'
		# Not editable
		else:
			self.editable = False

	# function: getFieldDict
	# return: dict		- The field as a dict
	# description: Returns the field as a dict object, suitable for using with data param of requests
	def getFieldDict(self):
		# If this field has a name, then it must be significant
		# and we will treat it as such
		if self._name_:
			return {self._name_:self._value_}
		# Else unimportant, setting it to None
		else:
			return None
	
	def __str__(self):
		return "name: %s, value: %s, type: %s, editable: %s"%(self._name_,self._value_,self._type_, str(self.editable))

# class: Form
# description: Represents a html form reconstructed for use in requests
class Form(object):
	# Regex that can be used for extracting forms
	FORM_REGEX = re.compile(r'<form(.*)<\/form>')
	# Regex responsible for capturing all inputs in a form
	INPUT_REGEX = re.compile(r'<input.*?>')
	# Regex responsible for capturing all fields within the form
	FIELD_REGEX = re.compile(r'name\=[\"\'](.*?)[\"\']|value\=[\"\'](.*?)[\"\']|type\=[\"\'](.*?)[\"\']')
	# Regex responsible for finding the method of form submission
	METHOD_REGEX = re.compile(r'method\=[\"\'](post|get)[\'\"]',re.I)
	# Regex to check if it uses an on click handle
	ON_CLICK_REGEX = re.compile(r'on.?click',re.I)
	clickFlag = None
	method = None
	fields = None
	payload = None
	form_html = None
	
	# function: __int__
	# description: constructor
	def __init__(self, form_html):
		self.fields = list()	
		self.payload = dict()
		self.clickFlag = False
		self.form_html = form_html
		self.buildForm()
		# Determining the method of form submission
		if self.METHOD_REGEX.search(form_html):
			self.method = self.METHOD_REGEX.findall(form_html)[0].upper()
		# Determining if this form contains an on-click handle
		if self.ON_CLICK_REGEX.search(form_html):
			self.clickFlag = True
	
	# function: addField
	# param: str	- the name attribute of the field
	# param: str	- the value attribute of the field
	# param: str	- the type attribute of the field
	# description: adds a field to this form
	def addField(self, fieldName, fieldValue, fieldType):
		self.fields.append(Field(fieldName,fieldValue,fieldType))	

	# function: buildForm
	# return: dict		- The form payload
	# description: Creates a payload for requests object
	def buildForm(self):
		self.payload = dict()
		fields = self.INPUT_REGEX.findall(self.form_html)
		for field in fields:
			if self.FIELD_REGEX.search(field):
				items = self.FIELD_REGEX.findall(field)
				f_name = ''
				f_value = ''
				f_type = ''
				for item in items:
					# Name field found
					if item[0]  not in (u'',''):
						f_name = item[0]
					# Value field found
					if item[1]  not in (u'',''):
						f_value = item[1]
					# Type field found
					if item[2]  not in (u'',''):
						f_type = item[2]
				# adding a new field to this forms field list
				self.addField(f_name,f_value,f_type)
		# Building form payload
		for field in self.fields:
			if field.getFieldDict() is not None:
				self.payload.update(field.getFieldDict())
		return self.payload

	# function: getEditable
	# return: list()	- All editable fields on this form
	# description: Returns a list of fields that can be filled in
	def getEditable(self):
		editable = list()
		for field in self.fields:
			if field.editable:
				editable.append(field)
		return editable

# class: LoginForm
# description: Represents a login form
class LoginForm(Form):
	url = None
	usernameField = None
	passwordField = None	
	invalidFlag = None
	# Used to do additional tests in order to determine which field is the username, 
	# if more then one field was determinted eligible to be a username field
	USER_REGEX = re.compile(r'(user|username)|(email)|(login)|(id)',re.I)

	# function: __init__
	# param: form_html(str)		- HTML representing this form
	# param: url(str)		- URL of this form
	# description: Constructor
	def __init__(self,form_html,url):
		self.invalidFlag = False
		Form.__init__(self,form_html)
		self.url = url
		self.passwordField = self.findPasswordField()
		self.usernameField = self.findUsernameField()
		if not self.usernameField or not self.passwordField:
			self.invalidFlag = True
		
	# function: getPayload
	# param: username(str)		- The username to build this payload with
	# param: password(str)		- The password to build this payload with
	# return: dict			- A payload dict, with the url, payload, and submission type
	# description: Returns a dict containing the details of this login
	# keys: 'url', 'payload', and 'method'
	def getPayload(self,username, password):	
		payload = {'url':self.url,'payload':None,'method':self.method}
		# This is a GET submission form
		if self.method == 'GET':
			payload['payload'] = self.buildGetPayload(username,password)
		# This is a POST submission form
		elif self.method == 'POST':
			payload['payload'] = self.buildPostPayload(username,password)	
		return payload

	# function: buildGetPayload
	# param: username(str)		- The username to build this payload with
	# param: password(str)		- The password to build this payload with
	# return: str			- The payload represented as a URL str
	# description: Builds a GET request payload for a login
	def buildGetPayload(self,username,password):
		payload = "%s?%s=%s&%s=%s"%(self.url,self.usernameField,username,self.passwordField,password)
		return payload

	# function: buildPostPayload
	# param: username(str)		- The username to build this payload with
	# param: password(str)		- The password to build this payload with
	# return: dict			- The dict to to use as a payload in a requests POST submission
	# description: Builds a POST payload to use with a POST requests
	def buildPostPayload(self,username,password):
		self.payload[self.usernameField] = username
		self.payload[self.passwordField] = password
		return self.payload

	# function: findUsernameField
	# return: str		- the username field of this payload
	# description: Finds the username field of this payload
	def findUsernameField(self):
		fieldFound = None
		alreadyFound = False
		# Flags used if multiple eligible fields found
		usernameFlag = False
		emailFlag = False
		loginFlag = False
		idFlag = False
		for field in self.fields:
			if field.editable:
				if not field.passwordFlag:
					if not alreadyFound:
						fieldFound = field._name_
						alreadyFound = True
					# to many possible username fields detected, testing via flags
					else:
						self.invalidFlag = True
						if self.USER_REGEX.search(field._name_):
							results = self.USER_REGEX.findall(field._name_)[0]
							# Username field was found setting username to this field
							if results[0] is not '':
								fieldFound = field._name_
								usernameFlag = True
							# Email field was found, and usernameFlag is still false, Setting to this until usernameFlag is True
							elif results[1] is not '' and not usernameFlag:
								fieldFound = field._name_
								emailFlag = True
							# Login field was found, username and email flags are still false, Setting to this until either one of those is true
							elif results[2] is not '' and not usernameFlag and not emailFlag:
								fieldFound = field._name_
								loginFlag = True
							# ID field was found, username, email, login flags are all false, Setting to this until any of those are true
							elif results[3] is not '' and not usernameFlag and not emailFlag and not loginFlag:
								fieldFound = field._name_
								idFlag = True
		return fieldFound
	
	# function: findPasswordField
	# return: str		- the password field of this payload
	# description: Finds the password field of this payload
	def findPasswordField(self):
		fieldFound = None
		alreadyFound = False
		for field in self.fields:
			if field.passwordFlag:
				if not alreadyFound:
					fieldFound = field._name_
					alreadyFound = True
				else:
					self.invalidFlag = True
		return fieldFound
