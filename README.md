```python
# DISCLAIMER:
# Swarm is for education/research purposes only. The author takes NO responsibility and/or liability for how you choose to use any of the tools/source code/any files provided.
# The author and anyone affiliated with will not be liable for any losses and/or damages in connection with use of ANY files provided with Swarm.
# By using Swarm or any files included, you understand that you are AGREEING TO USE AT YOUR OWN RISK. Once again Swarm and ALL files included are for EDUCATION and/or RESEARCH purposes ONLY.
# Swarm is ONLY intended to be used on your own pentesting labs, or with explicit consent from the owner of the property being tested. 
# 
# Getting Started:
# to use, you must first give the script execute permissions, via: 
#	sudo chmod 764 swarm		- This gives root execute permissions
#				  OR
#	sudo chmod 755 swarm		- This gives execute and read permissions to everyone
#	
# For all options:
#	sudo ./swarm --help
# 
# Basic example of how to use on "Damn Vulnerable Web App":
# sudo ./swarm --url='http://localhost/dvwa/login.php' --user-file='usernames.txt' --pass-file='passwords.txt' --verbose --threads=1 
#
# DEPENDENCIES:
#	folder contents		- all the files within swarm directory
#	bitarray		- used with bloomfilter
#		pip install bitarray
#	requests		- how swarm makes POST/GET requests
#		pip install requests
#	requests[socks]		- allows tor to be used with swarm
#		pip install -U requests[socks]
#	pexpect			- Used in SSHHive for ssh login attempts
#		pip install pexpect
#	tor			- If you want to use tor, tor must be installed
#		apt-get install tor	- on Debian
#		yum --install tor	- on Red Hat Based linux
#
#
```
