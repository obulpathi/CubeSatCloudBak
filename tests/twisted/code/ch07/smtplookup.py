from twisted.mail import relaymanager

mxCalc = relaymanager.MXCalculator()

def getSMTPServer(emailAddress):
    username, domain = emailAddress.split("@")
    return mxCalc.getMX(domain).addCallback(__gotMXRecord)

def __gotMXRecord(mxRecord):
    return mxRecord.exchange

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys
    address = sys.argv[1]

    def printServer(server):
        print server
        reactor.stop()

    def handleError(error):
        print >> sys.stderr, error.getErrorMessage()
        reactor.stop()

    getSMTPServer(address).addCallback(printServer).addErrback(handleError)
    reactor.run()

    



