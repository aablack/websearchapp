import json
import httplib
import urllib
import urllib2

class SearchError(Exception):
    """Raised when the results of a search are unexpected or
    incorrectly formatted

    """
    pass


class SearchEngine(object):

    def search(self, search_term, count, skip=0):
        """ Need to override this method to perform the search and
        return a list of dict objects containing url, title
        and description entries.

        Example:
        [{"url": "http://www.myexample.com",
        "title": "Example search item",
        "description": "This is my example search result ..."},
        ]

        Keyword arguments:
        search_term -- search term. Spaces will be handled
        appropriately by this method
        count -- how many results to fetch
        skip -- skip over this number of initial results. This
        allows paginated fetches of the results.

        """
        raise NotImplementedError("search() needs to be implemented")


class BingSearchEngine(SearchEngine):
    BASE_URI = "https://api.datamarket.azure.com:443"

    def __init__(self, account_key):
        """Keyword arguments:
        account_key -- account key as provided by the Windows
        Azure Marketplace.

        """
        if not account_key:
            raise ValueError("account_key is required to use the Bing Api")

        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm="", uri=self.BASE_URI, user="", passwd=account_key)
        self._opener = urllib2.build_opener(auth_handler)

    def _construct_search_url(self, search_term, count, skip):
        search_url = urllib.basejoin(self.BASE_URI, "Data.ashx/Bing/Search/v1/Web")
        search_url += "?Query=%%27%s%%27" % (urllib.quote(search_term))
        search_url += "&$top=%d" % (count)
        if skip:
            search_url += "&$skip=%d" % (skip)
        search_url += "&$format=JSON"
        return search_url

    def _process_results(self, results):
        """Process JSON formatted Bing search results and convert
        to a list of dict objects containing url, title
        and description entries.

        Keyword arguments:
        results -- string of raw JSON formatted response

        """
        try:
            search_results = list()
            for result in json.loads(results)['d']["results"]:
                search_results.append({
                    "url": result["Url"],
                    "title": result["Title"],
                    "description": result["Description"]})

            return search_results

        except KeyError as e:
            raise SearchError("Unexpected formatting in search results")


    def search(self, search_term, count, skip=0):
        """ Search web using Bing API for the specified search term
        and return a list of dict objects. Each dictionary contains
        a url, title and description entry.

        Keyword arguments:
        search_term -- search term. Spaces will be handled
        appropriately by this method
        count -- how many results to fetch
        skip -- skip over this number of initial results. This
        allows paginated fetches of the results.

        """

        response = self._opener.open(self._construct_search_url(search_term, count, skip))
        returncode = response.getcode()
        if returncode == httplib.OK:
            return self._process_results(response.read())
        else:
            raise urllib2.HTTPError("HTTP GET failed, status code = %d" % (returncode))


def rank_search_results(search_results, providers):
    """Given a list of RankProvider objects calculate the page
    rank for each URL in the search results.
    The search_result dict passed in will have a rank key added
    pointing to a new dict. The dict will contain the name of the
    RankProvider class and the page rank figure.

    Example:
    search_results = {
        "url": "http://www.google.com",
        "title": ...,
        "description": ...
        "rank" : {"GooglePageRank", 5}}

    Keyword arguments:
    search_results -- as obtained from the search() function in a
    SearchEngine object.
    providers -- list of RankProvider objects to use

    """
    for result in search_results:
        rank = dict()
        for provider in providers:
            rank[provider.__class__.__name__] = provider.get_rank(result["url"])

        result["rank"] = rank


def sort_search_results(search_results, provider_name, reverse=False):
    """ Sort a list of search results from least popular to most
    popular. Results should been ranked first using rank_search_results.

    Keyword arguments:
    search_results -- dictionary of search results
    provider_name -- name of the rank provider class
    reverse -- sort in reverse-rank order

    """
    # for these providers a higher number = more popular
    if provider_name in ("GooglePageRank"):
        return sorted(search_results,
                key=lambda x: x["rank"][provider_name] or 0, reverse=not reverse)

    # for these providers a lower number = more popular
    elif provider_name in ("AlexaTrafficRank"):
        return sorted(search_results,
                key=lambda x: x["rank"][provider_name] or float("inf"), reverse=reverse)

