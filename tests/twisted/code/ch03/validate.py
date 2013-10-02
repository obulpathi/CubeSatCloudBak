from twisted.web import client
import os, tempfile, webbrowser, random

def encodeForm(inputs):
    """
    Takes a dict of inputs and returns a multipart/form-data string
    containing the utf-8 encoded data. Keys must be strings, values
    can be either strings or file-like objects.
    """
    getRandomChar = lambda: chr(random.choice(range(97, 123)))
    randomChars = [getRandomChar() for x in range(20)]
    boundary = "---%s---" % ''.join(randomChars)
    lines = [boundary]
    for key, val in inputs.items():
        header = 'Content-Disposition: form-data; name="%s"' % key
        if hasattr(val, 'name'):
            header += '; filename="%s"' % os.path.split(val.name)[1]
        lines.append(header)
        if hasattr(val, 'read'):
            lines.append(val.read())
        else:
            lines.append(val.encode('utf-8'))
        lines.append('')
        lines.append(boundary)
    return "\r\n".join(lines)

def showPage(pageData):
    # write data to temp .html file, show file in browser
    tmpfd, tmp = tempfile.mkstemp('.html')
    os.close(tmpfd)
    file(tmp, 'w+b').write(pageData)
    webbrowser.open('file://' + tmp)
    reactor.stop()

def handleError(failure):
    print "Error:", failure.getErrorMessage()
    reactor.stop()

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor

    filename = sys.argv[1]
    fileToCheck = file(filename)
    form = encodeForm({'uploaded_file': fileToCheck})
    postRequest = client.getPage(
        'http://validator.w3.org/check',
        method='POST',
        headers={'Content-Type': 'multipart/form-data; charset=utf-8',
                 'Content-Length': str(len(form))},
        postdata=form)
    postRequest.addCallback(showPage).addErrback(handleError)
    reactor.run()
