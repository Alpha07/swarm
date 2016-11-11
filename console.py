import time
import sys

# class: Console
# description: Used to help format strings to the terminal, *NOTE* only compatible with specific terminals, although
#		 rare if not compatible with a modern day terminal.
class Console(object):
	FORMAT_DICT = {	'red':'\033[31m',
			'green':'\033[32m',
			'yellow':'\033[33m',
			'blue':'\033[34m',
			'magenta':'\033[35m',
			'cyan':'\033[36m',
			'l_gray':'\033[37m',
			'd_gray':'\033[90m',
			'l_red':'\033[91m',
			'l_green':'\033[92m',
			'l_yellow':'\033[93m',
			'l_blue':'\033[94m',
			'l_magenta':'\033[95m',
			'l_cyan':'\033[96m',
			'white':'\033[97m',
			'normal':'\033[0m',
			'default_bg':'\033[49m',
			'black_bg':'\33[40m',
			'red_bg':'\033[41m',
			'green_bg':'\033[42m',
			'yellow_bg':'\033[43m',
			'blue_bg':'\033[44m',
			'magenta_bg':'\033[45m',
			'cyan_bg':'\033[46m',
			'l_gray_bg':'\033[47m',
			'd_gray_bg':'\033[100m',
			'l_red_bg':'\033[101m',
			'l_green_bg':'\033[102m',
			'l_yellow_bg':'\033[103m',
			'l_blue_bg':'\033[104m',
			'l_magenta_bg':'\033[105m',
			'l_cyan_bg':'\033[106m',
			'l_white_bg':'\033[107m',
			'underline':'\033[4m',
			'bold':'\033[1m',
			'blink':'\033[5m',
			'dim':'\033[2m',
			'hidden':'\033[8m',
			'invert':'\0337m'
			}			
	
	# function: getFormatKeys
	# return: [string] 	- valid keys for format()
	# description: returns valid keys for format()
	def getFormatKeys(self):
		return self.FORMAT_DICT.keys()
			
	# function: format 
	# param: (string)	- The string to format
	# param: [string, ...] 	- Array of keys from self.FORMAT_DICT.keys() to format the string with
	# return: string	- The formatted string
	# description: Formats the given string with the given keys from FORMAT_DICT, and returns the newly formatted string
	def format(self, string, format_keys = []):
		for key in format_keys:
			string = self.FORMAT_DICT[key] + string + self.FORMAT_DICT['normal']	
		return string
	
	# function: getTimeString
	# return: string 	- '[hour:min]'
	# description: formats the hour and minute as a human friendly readable string, in the format '[hour:min]'	
	def getTimeString(self):
		return '[' + str(time.localtime(time.time())[3]) + ':' + str(time.localtime(time.time())[4]) + ']'

	# function: progress
	# param: float 	- Percentage of the progress bar (0.0-100.0)
	# param: char 	- The character to fill the bar with
	# param: int	- The amount of characters in the bar
	# description: Creates a progress bar in the terminal
	def progress(self, percentage = 0.0, barchar = '=', size=100):
		total_progress = float(float(percentage/101)*float(size))
		progressbar = ''
		for index in range(int(total_progress)):
			progressbar += barchar 
		progressbar = str(percentage+1) + '% ' + progressbar
		sys.stdout.write('\r' + progressbar)
		sys.stdout.flush()		

