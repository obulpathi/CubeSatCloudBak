from twisted.web import client
import urllib

def slashdotLogin(username, password):
    postdata = urllib.urlencode({'unickname': username,
                                 'upasswd': password})
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'Content-Length': len(postdata)}
    return client.getPage('http://slashdot.org/users.pl',
                               method='POST',
                               postdata=postdata,
                               headers=headers).addCallback(
        _gotResponse).addErrback(_gotError)

def _gotResponse(response):
    print "GOT RESPONSE"
    print response

def _gotError(err):
    print "ERROR!"
    print err

from twisted.internet import reactor
print reactor
slashdotLogin('test', 'test')
reactor.run()
print "DONE"
