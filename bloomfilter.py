from bitarray import bitarray
import md5

# class: BloomFilter
# description: This class is used for keeping track of a large amounts of values. 
class BloomFilter(object):
	array = None
	size = None
	
	# function: __init__
	# param: int	- The size of this bloomfilter, larger the size the more accurate the results
	# description: constructor
	def __init__(self,size):
		self.array = bitarray(size)
		self.size = size

	# function: append
	# param: string		- a string to keep track of
	# description: Adds a value to the array to track
	def append(self,string):
		(pos1,pos2) = self.__get_pos__(string)
		if not self.inArray(string):
			self.array[pos1] = True
			self.array[pos2] = True

	# function: inArray
	# param: string		- Checks if this string is currently being tracked
	# return: bool		- False (value is not being tracked) True (value is being tracked)
	# description: Checks if string is being tracked by this BloomFilter
	def inArray(self,string):
		(pos1,pos2) = self.__get_pos__(string)
		isStored = self.array[pos1] and self.array[pos2]
		return isStored 

	# function: __hash__
	# param: string		- string to hash into an integer`
	# param: offset		- offset, works as a unique key. If 2 identical strings are passed in with the same key, then the same value will be returned
	# description: Returns a integer representation of the string passed in
	def __hash__(self,string,offset):
		position = 0
		hashed_string = md5.new()
		hashed_string.update(string+str(offset))
		hex_position = hashed_string.hexdigest()	
		position = (int(hex_position,16))/len(string)
		position = (position%self.size) 		#Ensuring position falls within the correct range
		return position 

	# function: __get_pos__
	# param: string		- string to generate two unique positions 
	# description: Returns a tuple(int,int) with two unique numbers for this string
	def __get_pos__(self,string):
		positve_pos = 0
		negative_pos = 0
		positve_pos = self.__hash__(string, '*7&321^>-DRY8#--__')
		negative_pos = self.__hash__(string, '*9%&3^>21-()#@)!')
		return (positve_pos,negative_pos)	

