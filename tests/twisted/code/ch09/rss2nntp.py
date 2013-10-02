from twisted.internet import reactor, defer
from twisted.news import database, news, nntp
from twisted.web import client, microdom
from zope.interface import implements
from cStringIO import StringIO
from email.Message import Message
import email.Utils
import socket, time, md5

GROUPS = {
    "rss.slashdot": "http://www.slashdot.org/slashdot.rdf",
    "rss.abefettig": "http://fettig.net/xml/rss2.xml",
    }

class RssFeed(object):
    refreshRate = 60*60 # hourly refresh
    
    def __init__(self, groupName, feedUrl):
        self.title = ""
        self.groupName = groupName
        self.feedUrl = feedUrl
        self.articles = []
        self.articlesById = {}
        self.lastRefreshTime = 0
        self.refreshing = None

    def refreshIfNeeded(self):
        timeSinceRefresh = time.time() - self.lastRefreshTime
        if timeSinceRefresh > self.refreshRate:
            if not self.refreshing:
                self.refreshing = client.getPage(self.feedUrl).addCallback(
                    self._gotFeedData).addErrback(
                    self._getDataFailed)
            d = defer.Deferred()
            self.refreshing.chainDeferred(d)
            return d
        else:
            return defer.succeed(None)
            
    def _gotFeedData(self, data):
        print "Loaded feed data from %s" % self.feedUrl
        self.refreshing = None
        self.lastRefreshTime = time.time()

        # this is a naive and brittle way to parse RSS feeds.
        # It should work for most well-formed feeds, but will choke
        # if the feed has a structure that doesn't meet it's
        # expectations. In the real world, you'd want to use a
        # more robust means of parsing feeds, such as FeedParser
        # (http://feedparser.org) or Yarn (http://yarnproject.org)
        
        xml = microdom.parseString(data)
        self.title = xml.documentElement.getElementsByTagName(
            'title')[0].childNodes[0].data
        items = xml.documentElement.getElementsByTagName('item')
        for item in items:
            rssData = {}
            for field in 'title', 'link', 'description':
                nodes = item.getElementsByTagName(field)
                if nodes: 
                    rssData[field] = nodes[0].childNodes[0].data
                else:
                    rssData[field] = ''
            guid = md5.md5(
                rssData['title'] + rssData['link']).hexdigest()
            articleId = "<%s@%s>" % (guid, socket.getfqdn())
            if not self.articlesById.has_key(articleId):
                article = Message()
                article['From'] = self.title
                article['Newsgroups'] = self.groupName
                article['Message-Id'] = articleId
                article['Subject'] = rssData['title']
                article['Date'] = email.Utils.formatdate()
                body = "%s\r\n\r\n%s" % (
                    rssData['description'], rssData['link'])
                article.set_payload(body)
                self.articles.append(article)
                self.articlesById[articleId] = article

    def _getDataFailed(self, failure):
        print "Failed to load RSS data from %s: %s" % (
            self.feedUrl, failure.getErrorMessage())
        self.refreshing = None
        return failure

    def _refreshComplete(self, _):
        # schedule another refresh
        reactor.callLater(self.refreshRate, self.refresh)

class RssFeedStorage(object):
    "keeps articles in memory, loses them when the process exits"
    implements(database.INewsStorage)

    def __init__(self, feeds):
        "feeds is a dict of {groupName:url}"
        self.feeds = {}
        for groupName, url in feeds.items():
            self.feeds[groupName] = RssFeed(groupName, url)

    def refreshAllFeeds(self):
        refreshes = [feed.refreshIfNeeded() for feed in self.feeds.values()]
        return defer.DeferredList(refreshes)

    def _refreshAllFeedsAndCall(self, func, *args, **kwargs):
        "refresh all feeds and then return the results of calling func"
        return self.refreshAllFeeds().addCallback(
            lambda _: func(*args, **kwargs))

    def _refreshFeedAndCall(self, groupName, func, *args, **kwargs):
        "refresh one feed and then return the results of calling func"
        if self.feeds.has_key(groupName):
            feed = self.feeds[groupName]
            return feed.refreshIfNeeded().addCallback(
                lambda _: func(*args, **kwargs))
        else:
            return defer.fail(KeyError(groupName))

    def listRequest(self):
        """
        List information about the newsgroups on this server.
        Returns a Deferred which will call back with a list of tuples
        in the form
        (groupname, messageCount, firstMessage, postingAllowed)
        """
        return self._refreshAllFeedsAndCall(self._listRequest)

    def _listRequest(self):
        groupInfo = []
        for feed in self.feeds.values():
            # set to 'y' to indicate that posting is allowed
            postingAllowed = 'n' 
            groupInfo.append(
                (feed.groupName, len(feed.articles), 0, postingAllowed))
        return groupInfo

    def listGroupRequest(self, groupname):
        "return the list of message indexes for the group"
        return self._refreshFeedAndCall(groupname, self._listGroupRequest,
                                        groupname)

    def _listGroupRequest(self, groupname):
        feed = self.feeds[groupname]
        return range(len(feed.articles))
    
    def subscriptionRequest(self):
        "return the list of groups the server recommends to new users"
        return defer.succeed(self.feeds.keys())

    def overviewRequest(self):
        """
        return a list of headers that will be used for giving
        an overview of a message. twisted.news.database.OVERVIEW_FMT
        is such a list.
        """
        return defer.succeed(database.OVERVIEW_FMT)

    def groupRequest(self, groupName):
        """
        Return a tuple of information about the group:
        (groupName, articleCount, startIndex, endIndex, flags)
        """
        return self._refreshFeedAndCall(groupName,
                                        self._groupRequest,
                                        groupName)
    
    def _groupRequest(self, groupName):
        feed = self.feeds[groupName]
        groupInfo = (groupName,
                     len(feed.articles),
                     len(feed.articles),
                     0,
                     {})
        return defer.succeed(groupInfo)

    def xoverRequest(self, groupName, low, high):
        """
        Return a list of tuples, once for each article between low and high.
        Each tuple contains the article's values of the headers that
        were returned by self.overviewRequest.
        """
        return self._refreshFeedAndCall(groupName,
                                        self._processXOver,
                                        groupName, low, high,
                                        database.OVERVIEW_FMT)

    def xhdrRequest(self, groupName, low, high, header):
        """
        Like xoverRequest, except that instead of returning all the
        header values it should return only the value of a single header.
        """
        return self._refreshFeedAndCall(groupName,
                                        self._processXOver,
                                        groupName, low, high,
                                        [header])
        

    def _processXOver(self, groupName, low, high, headerNames):
        feed = self.feeds[groupName]
        if low is None: low = 0
        if high is None: high = len(feed.articles)-1
        results = []
        for i in range(low, high+1):
            article = feed.articles[i]
            articleData = article.as_string(unixfrom=False)
            headerValues = [i]
            for header in headerNames:
                # check for special headers
                if header == 'Byte-Count':
                    headerValues.append(len(articleData))
                elif header == 'Line-Count':
                    headerValues.append(len(articleData.split('\n')))
                else:
                    headerValues.append(article.get(header, ''))
            results.append(headerValues)
        return defer.succeed(results)

    def articleExistsRequest(self, groupName, id):
        feed = self.feeds[groupName]
        return defer.succeed(feed.articlesById.has_key(id))

    def articleRequest(self, groupName, index, messageId=None):
        """
        return the contents of the article specified by either
        index or message ID
        """
        feed = self.feeds[groupName]
        if messageId:
            message = feeds.articlesById(messageId)
            # look up the index
            index = feed.articles.index(message)
        else:
            message = feed.articles[index]
            # look up the message ID
            for mId, m in feed.articlesById.items():
                if m == message:
                    messageId = mId
                    break
        messageData = message.as_string(unixfrom=False)
        return defer.succeed((index, id, (StringIO(messageData))))
   
    def headRequest(self, groupName, index):
        "return the headers of them message at index"
        group = self.groups[groupName]
        article = group.articles[index]
        return defer.succeed(article.getHeaders())

    def bodyRequest(self, groupName, index):
        "return the body of the message at index"
        group = self.groups[groupName]
        article = group.articles[index]
        return defer.succeed(article.body)

    def postRequest(self, message):
        "post the message."
        return defer.fail(Exception("RSS feeds are read-only."))

class DebuggingNNTPProtocol(nntp.NNTPServer):
    debug = True

    def lineReceived(self, line):
        if self.debug:
            print "CLIENT:", line
        nntp.NNTPServer.lineReceived(self, line)

    def sendLine(self, line):
        nntp.NNTPServer.sendLine(self, line)
        if self.debug:
            print "SERVER:", line

class DebuggingNNTPFactory(news.NNTPFactory):
    protocol = DebuggingNNTPProtocol

if __name__ == "__main__":
    factory = DebuggingNNTPFactory(RssFeedStorage(GROUPS))
    reactor.listenTCP(119, factory)
    reactor.run()
