import struct
import sys
import urllib
import urllib2
import httplib
import re
import xml.etree.ElementTree

class RankProvider(object):
    """Abstract class for obtaining the page rank (popularity)
    from a provider such as Google or Alexa.

    """
    def __init__(self, host, proxy=None, timeout=30):
        """Keyword arguments:
        host -- toolbar host address
        proxy -- address of proxy server. Default: None
        timeout -- how long to wait for a response from the server.
        Default: 30 (seconds)

        """
        self._opener = urllib2.build_opener()
        if proxy:
            self._opener.add_handler(urllib2.ProxyHandler({"http": proxy}))

        self._host = host
        self._timeout = timeout

    def get_rank(self, url):
        """Get the page rank for the specified URL

        Keyword arguments:
        url -- get page rank for url

        """
        raise NotImplementedError("You must override get_rank()")


class AlexaTrafficRank(RankProvider):
    """ Get the Alexa Traffic Rank for a URL

    """
    def __init__(self, host="xml.alexa.com", proxy=None, timeout=30):
        """Keyword arguments:
        host -- toolbar host address: Default: joolbarqueries.google.com
        proxy -- address of proxy server (if required). Default: None
        timeout -- how long to wait for a response from the server.
        Default: 30 (seconds)

        """
        super(AlexaTrafficRank, self).__init__(host, proxy, timeout)

    def get_rank(self, url):
        """Get the page rank for the specified URL

        Keyword arguments:
        url -- get page rank for url

        """
        query = "http://%s/data?%s" % (self._host, urllib.urlencode((
            ("cli", 10),
            ("dat", "nsa"),
            ("ver", "quirk-searchstatus"),
            ("uid", "20120730094100"),
            ("userip", "192.168.0.1"),
            ("url", url))))

        response = self._opener.open(query, timeout=self._timeout)
        if response.getcode() == httplib.OK:
            data = response.read()

            element = xml.etree.ElementTree.fromstring(data)
            for e in element.iterfind("SD"):
                popularity = e.find("POPULARITY")
                if popularity is not None:
                    return int(popularity.get("TEXT"))


class GooglePageRank(RankProvider):
    """ Get the google page rank figure using the toolbar API.
    Credits to the author of the WWW::Google::PageRank CPAN package
    as I ported that code to Python.

    """
    def __init__(self, host="toolbarqueries.google.com", proxy=None, timeout=30):
        """Keyword arguments:
        host -- toolbar host address: Default: toolbarqueries.google.com
        proxy -- address of proxy server (if required). Default: None
        timeout -- how long to wait for a response from the server.
        Default: 30 (seconds)

        """
        super(GooglePageRank, self).__init__(host, proxy, timeout)
        self._opener.addheaders = [("User-agent", "Mozilla/4.0 (compatible; \
GoogleToolbar 2.0.111-big; Windows XP 5.1)")]

    def get_rank(self, url):
        # calculate the hash which is required as part of the get
        # request sent to the toolbarqueries url.
        ch = '6' + str(self._compute_ch_new("info:%s" % (url)))

        query = "http://%s/tbr?%s" % (self._host, urllib.urlencode((
            ("client", "navclient-auto"),
            ("ch", ch),
            ("ie", "UTF-8"),
            ("oe", "UTF-8"),
            ("features", "Rank"),
            ("q", "info:%s" % (url)))))

        response = self._opener.open(query, timeout=self._timeout)
        if response.getcode() == httplib.OK:
            data = response.read()
            match = re.match("Rank_\d+:\d+:(\d+)", data)
            if match:
                rank = match.group(1)
                return int(rank)

    @classmethod
    def _compute_ch_new(cls, url):
        ch = cls._compute_ch(url)
        ch = ((ch % 0x0d) & 7) | ((ch / 7) << 2);

        return cls._compute_ch(struct.pack("<20L", *(cls._wsub(ch, i * 9) for i in range(20))))

    @classmethod
    def _compute_ch(cls, url):
        url = struct.unpack("%dB" % (len(url)), url)
        a = 0x9e3779b9
        b = 0x9e3779b9
        c = 0xe6359a60
        k = 0

        length = len(url)

        while length >= 12:
            a = cls._wadd(a, url[k+0] | (url[k+1] << 8) | (url[k+2] << 16) | (url[k+3] << 24));
            b = cls._wadd(b, url[k+4] | (url[k+5] << 8) | (url[k+6] << 16) | (url[k+7] << 24));
            c = cls._wadd(c, url[k+8] | (url[k+9] << 8) | (url[k+10] << 16) | (url[k+11] << 24));

            a, b, c = cls._mix(a, b, c)

            k += 12
            length -= 12

        c = cls._wadd(c, len(url));

        if length > 10: c = cls._wadd(c, url[k+10] << 24)
        if length > 9: c = cls._wadd(c, url[k+9] << 16)
        if length > 8: c = cls._wadd(c, url[k+8] << 8)
        if length > 7: b = cls._wadd(b, url[k+7] << 24)
        if length > 6: b = cls._wadd(b, url[k+6] << 16)
        if length > 5: b = cls._wadd(b, url[k+5] << 8)
        if length > 4: b = cls._wadd(b, url[k+4])
        if length > 3: a = cls._wadd(a, url[k+3] << 24)
        if length > 2: a = cls._wadd(a, url[k+2] << 16)
        if length > 1: a = cls._wadd(a, url[k+1] << 8)
        if length > 0: a = cls._wadd(a, url[k])

        a, b, c = cls._mix(a, b, c);

        # integer is always positive
        return c

    @classmethod
    def _mix(cls, a, b, c):
        a = cls._wsub(a, b); a = cls._wsub(a, c); a ^= c >> 13;
        b = cls._wsub(b, c); b = cls._wsub(b, a); b ^= (a << 8) % 4294967296;
        c = cls._wsub(c, a); c = cls._wsub(c, b); c ^= b >>13;
        a = cls._wsub(a, b); a = cls._wsub(a, c); a ^= c >> 12;
        b = cls._wsub(b, c); b = cls._wsub(b, a); b ^= (a << 16) % 4294967296;
        c = cls._wsub(c, a); c = cls._wsub(c, b); c ^= b >> 5;
        a = cls._wsub(a, b); a = cls._wsub(a, c); a ^= c >> 3;
        b = cls._wsub(b, c); b = cls._wsub(b, a); b ^= (a << 10) % 4294967296;
        c = cls._wsub(c, a); c = cls._wsub(c, b); c ^= b >> 15;

        return a, b, c

    @staticmethod
    def _wadd(a, b):
        return (a + b) % 4294967296

    @staticmethod
    def _wsub(a, b):
        return (a - b) % 4294967296


if __name__ == "__main__":
    url = "http://www.archlinux.org"
    providers = (AlexaTrafficRank(), GooglePageRank(),)

    print("Traffic stats for: %s" % (url))
    for p in providers:
        print("%s:%d" % (p.__class__.__name__, p.get_rank(url)))

