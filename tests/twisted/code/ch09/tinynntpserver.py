from twisted.internet import reactor
from twisted.news import database, news, nntp

GROUPS = [
    'local.programming',
    'local.programming.python',
    'local.knitting',
    ]
SMTP_SERVER = 'upstream-server.com'
STORAGE_DIR = 'storage'

newsStorage = database.NewsShelf(SMTP_SERVER, STORAGE_DIR)
for group in GROUPS:
    newsStorage.addGroup(group, [])
factory = news.NNTPFactory(newsStorage)
reactor.listenTCP(119, factory)
reactor.run()
