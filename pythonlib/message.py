from console import Console


# class: Message
# description: Responsible for building specialized strings to log to user
class Message(Console):
	
	def __init__(self):
		Console.__init__(self)

	# function: criticalMessage
	# param: str	- The message to format into a critical message
	# return: str	- The newly formatted string
	# description: Formats the message into a critical message
	def criticalMessage(self, message):
		string = self.getTimeString()	
		string += self.format(" [!!] %s "%message,['red','bold'])
		return string

	# function: infoMessage
	# param: str	- The message to format into a info message
	# return: str	- The newly formatted string
	# description: Formats the message into a info message
	def infoMessage(self, message):
		string = self.getTimeString()		
		string += self.format(" [*] %s "%message,['yellow'])
		return string

	# function: successMessage
	# param: str	- The message to format into a success message
	# return: str	- The newly formatted string
	# description: Formats the message into a success message
	def successMessage(self, message):
		string = self.getTimeString()			
		string += self.format(" [+] %s "%message,['green','bold'])
		return string

	# function: failedMessage
	# param: str	- The message to format into a failed message
	# return: str	- The newly formatted string
	# description: Formats the message into a failed message
	def failedMessage(self, message):
		string = self.getTimeString()				
		string += self.format(" [-] %s "%message,['red'])
		return string
