"""

Module :mod:`pyesgf.search.results`
===================================

Search results are retrieved through the :class:`ResultSet` class.  This class
hides paging of large result sets behind a client-side cache.  Subclasses of 
:class:`Result` represent results of different SOLr record type.

"""

from collections import Sequence, defaultdict
import re

from .consts import (DEFAULT_BATCH_SIZE, TYPE_DATASET, TYPE_FILE, 
                     TYPE_AGGREGATION)
from .exceptions import EsgfSearchException

class ResultSet(Sequence):
    """
    :ivar context: The search context object used to generate this resultset
    :property batch_size: The number of results that will be requested
        from esgf-search as one call.  This must be set on creation and
        cannot change.

    """
    def __init__(self, context, batch_size=DEFAULT_BATCH_SIZE, eager=True,
                 result_type=TYPE_DATASET):
        """
        :param context: The search context object used to generate this resultset
        :param batch_size: The number of results that will be requested from
            esgf-search as one call.
        :param eager: Boolean specifying whether to retrieve the first batch on
            instantiation.
            
        """
        self.context = context
        self.__batch_size = batch_size
        self.__batch_cache = [None] * ((len(self) / batch_size) + 1)
        if eager and len(self)>0:
            self.__get_batch(0)

    def __getitem__(self, index):
        batch_i = index / self.batch_size
        offset = index % self.batch_size
        if self.__batch_cache[batch_i] is None:
            self.__batch_cache[batch_i] = self.__get_batch(batch_i)
        batch = self.__batch_cache[batch_i]

        search_type = self.context.search_type
        ResultClass = _result_classes[search_type]

        #!TODO: should probably wrap the json inside self.__batch_cache
        return ResultClass(batch[offset], self.context)
            

    def __len__(self):
        return self.context.hit_count

    @property
    def batch_size(self):
        return self.__batch_size

    def _build_result(self, result):
        """
        Construct a result object from the raw json.

        This method is designed to be overridden in subclasses if desired.
        The default implementation simply returns the json.
        
        """
        return result

    def __get_batch(self, batch_i):
        offset = self.batch_size * batch_i
        limit = self.batch_size

        query_dict = self.context._build_query()
        response = self.context.connection.send_query(query_dict, limit=limit, 
                                                      offset=offset)

        #!TODO: strip out results
        return response['response']['docs']


class BaseResult(object):
    """
    Base class for results.

    Subclasses represent different search types such as File and Dataset.

    :ivar json: The oroginial json representation of the result.
    :ivar context: The SearchContext which generated this result.
    :property urls: a dictionary of the form {service: [(url, mime_type), ...], ...}

    """
    def __init__(self, json, context):
        self.json = json
        self.context = context
        
    @property
    def urls(self):
        url_dict = defaultdict(list)
        for encoded in self.json['url']:
            url, mime_type, service = encoded.split('|')
            url_dict[service].append((url, mime_type))

        return url_dict

    @property
    def opendap_url(self):
        try:
            url, mime = self.urls['OPENDAP'][0]
        except (KeyError, IndexError):
            return None
        
        url = re.sub(r'.html$', '', url)

        return url

    @property
    def download_url(self):
        try:
            url, mime = self.urls['HTTPServer'][0]
        except (KeyError, IndexError):
            return None

        return url

class DatasetResult(BaseResult):
    """
    A result object for ESGF datasets.

    :property dataset_id: The solr dataset_id which is unique throughout the system.

    """

    @property
    def dataset_id(self):
        #!TODO: should we decode this into a tuple?  self.json['id'].split('|')
        return self.json['id']
    
    def file_context(self):
        """
        Return a SearchContext for searching for files within this dataset.
        """
        from .context import SearchContext

        files_context = SearchContext(
            connection=self.context.connection,
            constraints={'dataset_id': self.dataset_id},
            search_type=TYPE_FILE,
            )
        return files_context

    def aggregation_context(self):
        """
        Return a SearchContext for searching for aggregations within this dataset.
        """
        from .context import SearchContext

        agg_context = SearchContext(
            connection=self.context.connection,
            constraints={'dataset_id': self.dataset_id},
            search_type=TYPE_AGGREGATION,
            )
        return agg_context

class FileResult(BaseResult):
    @property
    def file_id(self):
        return self.json['id']

    @property
    def checksum(self):
        return self.json['checksum'][0]

    @property
    def checksum_type(self):
        self.json['checksum_type'][0]

    @property
    def filename(self):
        return self.json['title']

    @property
    def size(self):
        return int(self.json['size'])

    @property
    def url(self):
        return self.urls['HTTPServer'][0][0]

class AggregationResult(BaseResult):
    @property
    def aggregation_id(self):
        return self.json['id']


_result_classes = {
    TYPE_DATASET: DatasetResult,
    TYPE_FILE: FileResult,
    TYPE_AGGREGATION: AggregationResult,
    }
