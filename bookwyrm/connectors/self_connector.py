''' using a bookwyrm instance as a source of book data '''
from functools import reduce
import operator

from django.contrib.postgres.search import SearchRank, SearchVector
from django.db.models import Count, F, Q

from bookwyrm import models
from .abstract_connector import AbstractConnector, SearchResult


class Connector(AbstractConnector):
    ''' instantiate a connector  '''
    def search(self, query, min_confidence=0.1):
        ''' search your local database '''
        # first, try searching unqiue identifiers
        results = search_identifiers(query)
        if not results:
            # then try searching title/author
            results = search_title_author(query, min_confidence)
        search_results = []
        for result in results:
            search_results.append(self.format_search_result(result))
            if len(search_results) >= 10:
                break
        search_results.sort(key=lambda r: r.confidence, reverse=True)
        return search_results


    def format_search_result(self, search_result):
        return SearchResult(
            title=search_result.title,
            key=search_result.remote_id,
            author=search_result.author_text,
            year=search_result.published_date.year if \
                    search_result.published_date else None,
            connector=self,
            confidence=search_result.rank if \
                    hasattr(search_result, 'rank') else 1,
        )


    def is_work_data(self, data):
        pass

    def get_edition_from_work_data(self, data):
        pass

    def get_work_from_edition_data(self, data):
        pass

    def get_authors_from_data(self, data):
        return None

    def parse_search_data(self, data):
        ''' it's already in the right format, don't even worry about it '''
        return data

    def expand_book_data(self, book):
        pass


def search_identifiers(query):
    ''' tries remote_id, isbn; defined as dedupe fields on the model '''
    filters = [{f.name: query} for f in models.Edition._meta.get_fields() \
        if hasattr(f, 'deduplication_field') and f.deduplication_field]
    results = models.Edition.objects.filter(
        reduce(operator.or_, (Q(**f) for f in filters))
    ).distinct()

    # when there are multiple editions of the same work, pick the default.
    # it would be odd for this to happen.
    return results.filter(parent_work__default_edition__id=F('id')) \
            or results


def search_title_author(query, min_confidence):
    ''' searches for title and author '''
    vector = SearchVector('title', weight='A') +\
        SearchVector('subtitle', weight='B') +\
        SearchVector('authors__name', weight='C') +\
        SearchVector('series', weight='D')

    results = models.Edition.objects.annotate(
        search=vector
    ).annotate(
        rank=SearchRank(vector, query)
    ).filter(
        rank__gt=min_confidence
    ).order_by('-rank')

    # when there are multiple editions of the same work, pick the closest
    editions_of_work = results.values(
        'parent_work'
    ).annotate(
        Count('parent_work')
    ).values_list('parent_work')

    for work_id in set(editions_of_work):
        editions = results.filter(parent_work=work_id)
        default = editions.filter(parent_work__default_edition=F('id'))
        default_rank = default.first().rank if default.exists() else 0
        # if mutliple books have the top rank, pick the default edition
        if default_rank == editions.first().rank:
            yield default.first()
        else:
            yield editions.first()
