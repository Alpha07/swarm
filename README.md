`
SWARM IS FOR EDUCATION PURPOSES ONLY, THE AUTHOR TAKES NO RESPONSIBLITY OF ACTIONS/USE OF SWARM OR ANY FILES INCLUDED WITH.
BY USING SWARM OR ANY FILES INCLUDED WITH, THE USER TAKES FULL RESPONSIBILITY OF THEIR ACTIONS.

Swarm is used to bruteforce html login forms. 
to use, you must first give the script execute permissions, via: 
	sudo chmod 764 swarm		- This gives root execute permissions
				  OR
	sudo chmod 755 swarm		- This gives execute and read permissions to everyone
	
to use swarm:
	sudo ./swarm --help



DEPENDENCIES:
	folder contents		- all the files within swarm directory
	bitarray		- used with bloomfilter
		pip install bitarray
	requests		- how swarm makes POST requests
		pip install requests
	requests[socks]		- allows tor to be used with swarm
		pip install -U requests[socks]
	tor			- If you want to use tor, tor must be installed
		apt-get install tor	- on Debian
		yum --install tor	- on Red Hat Based linux
`
