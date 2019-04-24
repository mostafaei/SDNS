import telnetlib




class Connection():
    def __init__(self):
        self._user = "guest"
        self._password = "guest"
        self._tn = telnetlib.Telnet()
    def addStaticRoute(self, host, command,route):
        print '-------------inside -connection--------host-----',host
        
        self._tn.open(host)
        print "connessione telnet con host " + host
        print command
        self._tn.read_until("login: ")
        self._tn.write(self._user + "\n")
        self._tn.read_until("Password: ")
        self._tn.write(self._password + "\n")
        self._tn.read_until("$ ")
        self._tn.write(command + "\n")
        self._tn.read_until("guest: ")
        self._tn.write(self._password + "\n")
        self._tn.read_until("$ ")
        self._tn.close()
        print "connessione telnet chiusa"

    def removeStaticRoute(self):
        pass
