import logging
import traceback

from django.conf import settings
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError

import search.searchutils as searchutils
import search.rank_provider as rank_provider

logger = logging.getLogger("debug.view")

# rank the results using the following providers. You will need to add
# the results to the search template and also add the provider name
# to the searchutils.sort_search_results() function.
rank_providers = [
        rank_provider.GooglePageRank(),
        rank_provider.AlexaTrafficRank(),
        ]

def search(request):
    """ Show the initial search form, or perform a search.
    Also handles posts via AJAX

    """
    if request.method == "GET":
        return render_to_response('search/index.html', {
            "search_text": ''},
            context_instance=RequestContext(request))

    elif request.method == "POST":
        try:
            search_text = request.POST.get("search_text", '')
            order = request.POST.get("order")
            engine = searchutils.BingSearchEngine(settings.BING_ACCOUNT_KEY)
            search_results = engine.search(search_text, count=10)

            # rank the search results and add a "rank" attribute to
            # the dict
            searchutils.rank_search_results(search_results, rank_providers)

            if order:
                logger.debug("Sorting using: %s" % (order))
                search_results = searchutils.sort_search_results(search_results, order)

            # generate the search HTML code from the search template
            t = loader.get_template("search/search.html")
            search_html = t.render(Context({"search_results": search_results},))
        except Exception, e:
            logger.error(traceback.format_exc())
            return HttpResponseServerError(e)

        if request.is_ajax():
            logger.debug("AJAX post")
            return HttpResponse(search_html)
        else:
            logger.debug("HTML post")
            return render_to_response("search/index.html", {
                'results': search_html},
                context_instance=RequestContext(request))


