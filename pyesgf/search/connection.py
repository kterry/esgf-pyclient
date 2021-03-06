"""

Module :mod:`pyesgf.search.connection`
======================================

Defines the class representing connections to the ESGF Search API.


"""

import urllib2, urllib, urlparse
import json

import logging
log = logging.getLogger(__name__)

from .context import SearchContext
from .consts import RESPONSE_FORMAT
from .exceptions import EsgfSearchException
from pyesgf.multidict import MultiDict

class SearchConnection(object):
    """
    :ivar url: The URL to the Search API service.  Usually <prefix>/esgf-search
    :ivar distrib: Boolean stating whether searches through this connection are
        distributed.  I.e. whether the Search service distributes the query to
        other search peers.
    :ivar shards: List of shards to send the query to.  An empty list implies
        distrib==False.  None implies the default of all shards.
        
    """
    #TODO: we don't need both distrib and shards.

    # Default limit for queries.  None means use service default.
    default_limit = None

    def __init__(self, url, distrib=True, shards=None, 
                 context_class=None):
	"""
        :param context_class: Override the default SearchContext class.

        """
        self.url = url
        self.distrib = distrib
        self.shards = shards
	
        if context_class:
            self.__context_class = context_class
        else:
            self.__context_class = SearchContext
        
        #!TODO: shards should probably be a property.
        
    def send_query(self, query_dict, limit=None, offset=None):
        """
        Generally not to be called directly by the user but via SearchContext
	instances.
        
        :param query_dict: dictionary of query string parameers to send.
        :return: ElementTree instance (TODO: think about this)
        
        """
        
        full_query = MultiDict({
            'format': RESPONSE_FORMAT,
            'limit': limit,
            'distrib': 'true' if self.distrib else 'false',
            'offset': offset,
            'shards': ','.join(self.shards) if self.shards else None,
            })
        full_query.extend(query_dict)

        # Remove all None valued items
        full_query = MultiDict(item for item in full_query.items() if item[1] is not None)


        query_url = '%s?%s' % (self.url, urllib.urlencode(full_query))
        log.debug('Query request is %s' % query_url)

        response = urllib2.urlopen(query_url)
        ret = json.load(response)

        return ret
    

    def get_shard_list(self):
	"""
        :return: the list of available shards

        """
        if not self.distrib:
            raise EsgfSearchException('Shard list not available for '
                                      'non-distributed queries')
        response = self.send_query({'facets': [], 'fields': []})
        shards = response['responseHeader']['params']['shards'].split(',')
        
        return shards
    
    def new_context(self, **constraints):
	#!MAYBE: context_class=None, 
	return self.__context_class(self, constraints)


def query_keyword_type(keyword):
    """
    Returns the keyword type of a search query keyword.

    Possible values are 'system', 'freetext', 'facet', 'temporal' and
    'geospatial'.  If the keyword is unknown it is assumed to be a
    facet keyword

    """
    #!TODO: support "last update" constraints (to/from)

    if keyword == 'query':
        return 'freetext'
    elif keyword in ['start', 'end']:
        return 'temporal'
    elif keyword in ['lat', 'lon', 'bbox', 'location', 'radius', 'polygon']:
        return 'geospatial'
    elif keyword in ['limit', 'from', 'to', 'fields', 'facets', 'format',
                     'type', 'distrib', 'replica', 'id', 'shards']:
        return 'system'
    else:
        return 'facet'
