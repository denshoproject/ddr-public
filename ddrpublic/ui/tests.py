"""
Loading Test Data

ddrindex destroy --confirm
ddrindex create
ddrindex vocabs /opt/densho-vocab/api/0.2/
ddrindex narrators /opt/densho-vocab/api/0.2/narrators.json
ddrindex repo /var/www/media/ddr/ddr/repository.json
ddrindex org /var/www/media/ddr/ddr-testing/organization.json
ddrindex org /var/www/media/ddr/ddr-densho/organization.json
ddrindex publish -r --force /var/www/media/ddr/ddr-densho-10
ddrindex publish --force /var/www/media/ddr/ddr-densho-1000/
ddrindex publish -r --force /var/www/media/ddr/ddr-densho-1000/files/ddr-densho-1000-1
"""

from django.test import TestCase
from django.urls import reverse


class RobotsView(TestCase):
    def test_robots(self):
        response = self.client.get(reverse('robots_rule_list'))
        self.assertEqual(response.status_code, 200)


class SitemapView(TestCase):
    def test_sitemap(self):
        response = self.client.get(reverse('ui-sitemap'))
        self.assertEqual(response.status_code, 200)


class APIIndexView(TestCase):

    def test_index(self):
        response = self.client.get(reverse('ui-api-index'))
        self.assertEqual(response.status_code, 200)


class APIObjectViews(TestCase):

    def test_api_object_repo(self):
        oid = 'ddr'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_repo_children(self):
        oid = 'ddr'
        response = self.client.get(reverse('ui-api-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_org(self):
        oid = 'ddr-densho'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_org_children(self):
        oid = 'ddr-densho'
        response = self.client.get(reverse('ui-api-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_collection(self):
        oid = 'ddr-densho-1000'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_collection_children(self):
        oid = 'ddr-densho-1000'
        response = self.client.get(reverse('ui-api-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_entity(self):
        oid = 'ddr-densho-1000-1'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_entity_files(self):
        oid = 'ddr-densho-1000-1'
        response = self.client.get(reverse('ui-api-object-nodes', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_file(self):
        oid = 'ddr-densho-1000-1-transcript-3bf547426b'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_entity_children(self):
        oid = 'ddr-densho-1000-1'
        response = self.client.get(reverse('ui-api-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_segment(self):
        oid = 'ddr-densho-1000-1-1'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_segment_children(self):
        oid = 'ddr-densho-1000-1-1'
        response = self.client.get(reverse('ui-api-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_segment_files(self):
        oid = 'ddr-densho-1000-1-1'
        response = self.client.get(reverse('ui-api-object-nodes', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_api_object_file(self):
        oid = 'ddr-densho-1000-1-1-mezzanine-0762419626'
        response = self.client.get(reverse('ui-api-object', args=[oid]))
        self.assertEqual(response.status_code, 200)


class APIFacetViews(TestCase):

    def test_api_facets(self):
        response = self.client.get(reverse('ui-api-facets'))
        self.assertEqual(response.status_code, 200)

    def test_api_facet(self):
        fid = 'topics'
        response = self.client.get(reverse('ui-api-facet', args=[fid]))
        self.assertEqual(response.status_code, 200)
        fid = 'facility'
        response = self.client.get(reverse('ui-api-facet', args=[fid]))
        self.assertEqual(response.status_code, 200)

    def test_api_facetterms(self):
        fid = 'topics'
        response = self.client.get(reverse('ui-api-facetterms', args=[fid]))
        self.assertEqual(response.status_code, 200)
        fid = 'facility'
        response = self.client.get(reverse('ui-api-facetterms', args=[fid]))
        self.assertEqual(response.status_code, 200)

    def test_api_term(self):
        fid = 'topics'; tid = '120'
        response = self.client.get(reverse('ui-api-term', args=[fid, tid]))
        self.assertEqual(response.status_code, 200)
        fid = 'facility'; tid = '46'
        response = self.client.get(reverse('ui-api-term', args=[fid, tid]))
        self.assertEqual(response.status_code, 200)

    def test_api_term_objects(self):
        fid = 'topics'; tid = '120'
        response = self.client.get(reverse('ui-api-term-objects', args=[fid, tid]))
        self.assertEqual(response.status_code, 200)
        fid = 'facility'; tid = '46'
        response = self.client.get(reverse('ui-api-term-objects', args=[fid, tid]))
        self.assertEqual(response.status_code, 200)


class APINarratorViews(TestCase):

    def test_api_narrators(self):
        response = self.client.get(reverse('ui-api-narrators'))
        self.assertEqual(response.status_code, 200)

    def test_api_narrator(self):
        nid = '165'
        response = self.client.get(reverse('ui-api-narrator', args=[nid]))
        self.assertEqual(response.status_code, 200)

    def test_api_narrator_interviews(self):
        nid = '165'
        response = self.client.get(reverse('ui-api-narrator-interviews', args=[nid]))
        self.assertEqual(response.status_code, 200)


class APISearchViews(TestCase):

    def test_api_search_index(self):
        response = self.client.get(reverse('ui-api-search'))
        self.assertEqual(response.status_code, 200)

    def test_api_search_results(self):
        response = self.client.get(
            reverse('ui-api-search'), {'fulltext': 'minidoka'}
        )
        self.assertEqual(response.status_code, 200)


class APISwaggerViews(TestCase):

    def test_swagger(self):
        response = self.client.get(reverse('schema-swagger-ui'))
        self.assertEqual(response.status_code, 200)

    #def test_swagger_json(self):
    #    response = self.client.get(reverse('schema-json'))
    #    self.assertEqual(response.status_code, 200)

    def test_swagger_redoc(self):
        response = self.client.get(reverse('schema-redoc'))
        self.assertEqual(response.status_code, 200)


#    url(r'^api/0.2/ui-state/$', ui_state, name='ui-api-state'),


# ------------------------------------------------------------------------

class IndexView(TestCase):
    
    def test_index(self):
        response = self.client.get(reverse('ui-index'))
        self.assertEqual(response.status_code, 200)
    
    def test_browse(self):
        names = [
            'ui-about',
            'ui-contact',
            'ui-terms',
            'ui-using',
            'ui-ethicalediting',
        ]
        for name in names:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
    
    def test_collections(self):
        response = self.client.get(reverse('ui-collections-list'))
        self.assertEqual(response.status_code, 200)


#    url(r'^(?P<oid>[\w\d-]+)/search/$', search.collection, name='ui-search-collection'),
#    url(r'^(?P<oid>[\w\d-]+)/objects/$', objects.children, name='ui-object-children'),
#    url(r'^(?P<oid>[\w\d-]+)/files/$', objects.nodes, name='ui-object-nodes'),
#    url(r'^(?P<oid>[\w\d-]+)/', objects.detail, name='ui-object-detail'),
class ObjectViews(TestCase):

    def test_collection_detail(self):
        oid = 'ddr-densho-10'
        response = self.client.get(reverse('ui-object-detail', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_collection_children(self):
        oid = 'ddr-densho-10'
        response = self.client.get(reverse('ui-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_entity_detail(self):
        oid = 'ddr-densho-10-2'
        response = self.client.get(reverse('ui-object-detail', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_entity_audio_simple(self):
        # mp3, simple entity
        oid = 'ddr-densho-400-1'
        response = self.client.get(reverse('ui-object-detail', args=[oid]))
        self.assertEqual(response.status_code, 200)
        assert b'av:audio'                          in response.content
        assert b'wavesurfer.playPause()'            in response.content
        assert b'Download segment transcript'   not in response.content
        assert b'Download full transcript'          in response.content
        assert b'Download fullsize'                 in response.content

    def test_entity_audio_segment(self):
        # mp3, VH interview segment
        oid = 'ddr-csujad-30-19-1'
        response = self.client.get(reverse('ui-interview', args=[oid]))
        self.assertEqual(response.status_code, 200)
        assert b'vh:'                               in response.content
        assert b'wavesurfer.playPause()'            in response.content
        assert b'Download segment transcript'       in response.content
        assert b'Download full transcript'          in response.content
        assert b'Download fullsize'                 in response.content

    def test_entity_video_mpg_inhouse(self):
        # mpg, standard VH prepared in-house
        oid = 'ddr-densho-1000-1-1'
        response = self.client.get(reverse('ui-interview', args=[oid]))
        self.assertEqual(response.status_code, 200)
        assert b'vh:'                               in response.content
        assert b'ui/entities/segment-video.html'    in response.content
        assert b'video-js'                          in response.content
        assert b'Download segment transcript'       in response.content
        assert b'Download full transcript'          in response.content
        assert b'Download MP4'                      in response.content
        assert b'Download full-size'                in response.content

    def test_entity_video_mp4_ia_streaming(self):
        # original video mp4; IA-created streaming video
        oid = 'ddr-densho-1020-13'
        response = self.client.get(reverse('ui-object-detail', args=[oid]))
        self.assertEqual(response.status_code, 200)
        assert b'av:video'                          in response.content
        assert b'ui/entities/detail-video.html'     in response.content
        assert b'video-js'                          in response.content
        assert b'Download segment transcript'   not in response.content
        assert b'Download full transcript'      not in response.content
        assert b'Download MP4'                      in response.content
        assert b'Download full-size'            not in response.content

    def test_entity_video_mp4_external_no_download(self):
        # external video, stream-only/no download from IA
        oid = 'ddr-densho-122-4-1'
        response = self.client.get(reverse('ui-interview', args=[oid]))
        self.assertEqual(response.status_code, 200)
        assert b'vh:'                               in response.content
        assert b'ui/entities/segment-video.html'    in response.content
        assert b'video-js'                          in response.content
        assert b'Download segment transcript'       in response.content
        assert b'Download full transcript'          in response.content
        assert b'Download MP4'                  not in response.content
        assert b'Download full-size'            not in response.content

    def test_entity_children(self):
        oid = 'ddr-densho-10-2'
        response = self.client.get(reverse('ui-object-children', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_file_detail(self):
        oid = 'ddr-densho-10-2-mezzanine-768fb04ca7'
        response = self.client.get(reverse('ui-object-detail', args=[oid]))
        self.assertEqual(response.status_code, 200)

    def test_interview(self):
        oid = 'ddr-densho-1000-1-1'
        response = self.client.get(reverse('ui-interview', args=[oid]))
        self.assertEqual(response.status_code, 200)

#    def test_cite(self):
#        oid = 'ddr-densho-10-2'
#        response = self.client.get(reverse('ui-cite', args=[oid]))
#        self.assertEqual(response.status_code, 200)



class FacetViews(TestCase):
    
    def test_browse_index(self):
        response = self.client.get(reverse('ui-browse-index'))
        self.assertEqual(response.status_code, 200)
    
    def test_browse_facet(self):
        fid = 'topics'
        r = self.client.get(reverse('ui-browse-facet', args=[fid]))
        self.assertEqual(r.status_code, 200)
        fid = 'facility'
        r = self.client.get(reverse('ui-browse-facet', args=[fid]))
        self.assertEqual(r.status_code, 200)
    
    def test_browse_term(self):
        kwargs = {'facet_id': 'topics', 'term_id': '68'}
        r = self.client.get(reverse('ui-browse-term', kwargs=kwargs))
        self.assertEqual(r.status_code, 200)
        kwargs = {'facet_id': 'facility', 'term_id': '46'}
        r = self.client.get(reverse('ui-browse-term', kwargs=kwargs))
        self.assertEqual(r.status_code, 200)


class NarratorViews(TestCase):
    
    def test_narrators_list(self):
        response = self.client.get(reverse('ui-narrators-list'))
        self.assertEqual(response.status_code, 200)

    def test_narrators_detail(self):
        nid = '165'
        response = self.client.get(reverse('ui-narrators-detail', args=[nid]))
        self.assertEqual(response.status_code, 200)

    def test_search_narrator(self):
        nid = '165'
        response = self.client.get(reverse('ui-search-narrator', args=[nid]))
        self.assertEqual(response.status_code, 200)


#    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', search.term_query, name='ui-search-term-query'),
#    url(r'^search/results/$', searching.search_ui, name='ui-search-results'),
#    url(r'^search/$', searching.search_ui, name='ui-search-index'),
class SearchViews(TestCase):
    
    def test_search_index(self):
        response = self.client.get(reverse('ui-search-index'))
        self.assertEqual(response.status_code, 200)

    def test_search_fulltext(self):
        response = self.client.get(
            reverse('ui-search-index'), {'fulltext': 'minidoka'}
        )
        self.assertEqual(response.status_code, 200)
        
        len_page_object_list = len(response.context['page'].object_list)
        #print(f'len(page.object_list): {len_page_object_list}')
        assert response.context['page'].object_list
        #print(f"paginator.num_pages: {response.context['paginator'].num_pages}")
        assert response.context['paginator'].num_pages

        fieldname_aggs = [
            (fieldname,aggs)
            for fieldname,aggs in response.context['results'].aggregations.items()
        ]
        #print(fieldname_aggs)
        assert response.context['results'].aggregations.get('topics')
        for item in response.context['results'].aggregations['topics']:
            assert item.key
            assert item.doc_count

    def test_search_persons(self):
        """Searches the Persons/Organizations links on entity-detail pages"""
        response = self.client.get(
            reverse('ui-search-index'), {'fulltext': 'persons:Yasui, Sachi'}
        )
        self.assertEqual(response.status_code, 200)
        
        len_page_object_list = len(response.context['page'].object_list)
        assert response.context['page'].object_list
        assert response.context['paginator'].num_pages

        fieldname_aggs = [
            (fieldname,aggs)
            for fieldname,aggs in response.context['results'].aggregations.items()
        ]
        assert response.context['results'].aggregations.get('topics')
        for item in response.context['results'].aggregations['topics']:
            assert item.key
            assert item.doc_count

    def test_search_creators(self):
        """Searches the Persons/Organizations links on entity-detail pages"""
        response = self.client.get(
            reverse('ui-search-index'), {'fulltext': 'creators:Yanagihara, Akio'}
        )
        self.assertEqual(response.status_code, 200)
        
        len_page_object_list = len(response.context['page'].object_list)
        assert response.context['page'].object_list
        assert response.context['paginator'].num_pages

        fieldname_aggs = [
            (fieldname,aggs)
            for fieldname,aggs in response.context['results'].aggregations.items()
        ]
        assert response.context['results'].aggregations.get('topics')
        for item in response.context['results'].aggregations['topics']:
            assert item.key
            assert item.doc_count

#    # match legacy urls
#    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/(?P<sha1>[\w\d]+)/', objects.legacy, name='ui-legacy'),
#    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/', objects.legacy, name='ui-legacy'),
#    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/', objects.legacy, name='ui-legacy'),
#    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/', objects.legacy, name='ui-legacy'),

    
