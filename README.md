# DISCLAIMER
**Swarm is for education/research purposes only. The author takes NO responsibility and/or liability for how you choose to use any of the tools/source code/any files provided.
 The author and anyone affiliated with will not be liable for any losses and/or damages in connection with use of ANY files provided with Swarm.
 By using Swarm or any files included, you understand that you are AGREEING TO USE AT YOUR OWN RISK. Once again Swarm and ALL files included are for EDUCATION and/or RESEARCH purposes ONLY.
 Swarm is ONLY intended to be used on your own pentesting labs, or with explicit consent from the owner of the property being tested.** 


#About Swarm 
**Swarm is a Bruteforcing tool for bruteforcing html logins**
###Some Notable Features
* Multi-Threaded
* Randomized user agents
* Supports TOR
* By-pass logins via SQL Injections
* Easy to inherit from to create different types of bruteforcing tools

##Getting Started
To use, you must first give the script execute permissions, via
```shell
sudo chmod 755 swarm		
```	
For all options
```shell
sudo ./swarm --help
``` 
##Basic example of how to use on Damn Vulnerable Web App
```shell
sudo ./swarm --url='http://localhost/dvwa/login.php' --user-file='usernames.txt' --pass-file='passwords.txt' --verbose --threads=1 
```
## DEPENDENCIES
```shell
pip install bitarray
pip install requests
pip install -U requests[socks]
pip install pexpect
apt-get install tor
```
