# -*- coding: utf-8 -*-

import unittest
import os

from algoliasearch import algoliasearch
from .helpers import safe_index_name, get_api_client


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index_name = safe_index_name(u'àlgol?à-python')
        cls.client = get_api_client()
        cls.index = cls.client.init_index(cls.index_name)

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_index(cls.index_name)

    def setUp(self):
        self.client.delete_index(self.index_name)

    def test_wrong_app_id(self):
        client = algoliasearch.Client("fakeappID", "blabla")
        try:
            client.listIndexes()
            self.assertTrue(False)
        except algoliasearch.AlgoliaException as e:
            pass

    def test_retry(self):
        try:
            client = algoliasearch.Client(
                os.environ['ALGOLIA_APPLICATION_ID'],
                os.environ['ALGOLIA_API_KEY'], [
                    "fakeapp-1.algolianet.com",
                    "fakeapp-2.algolianet.com",
                    os.environ['ALGOLIA_APPLICATION_ID'] + "-dsn.algolia.net"
                ])
            client.listIndexes()
        except algoliasearch.AlgoliaException as e:
            print(e)
            self.assertTrue(False)

    def test_network(self):
        batch = []
        for i in range(1, 1000):
            batch.append({'action': 'addObject', 'body': {
                'test1': 330 * 'a',
                'test2': 330 * 'a',
                'test3': 330 * 'a'
            }})
        self.index.batch(batch)

    def test_new_secured_keys(self):
        key1 = "MDZkNWNjNDY4M2MzMDA0NmUyNmNkZjY5OTMzYjVlNmVlMTk1NTEwMGNmNTVjZmJhMmIwOTIzYjdjMTk2NTFiMnRhZ0ZpbHRlcnM9JTI4cHVibGljJTJDdXNlcjElMjk="
        gen1_1 = self.client.generate_secured_api_key("182634d8894831d5dbce3b3185c50881", "(public,user1)")
        self.assertEquals(key1, gen1_1)

        gen1_2 = self.client.generate_secured_api_key("182634d8894831d5dbce3b3185c50881", {'tagFilters': "(public,user1)"})
        self.assertEquals(key1, gen1_2)

        key2_1 = "ZDU0N2YzZjA3NGZkZGM2OTUxNzY3NzhkZDI3YWFkMjhhNzU5OTBiOGIyYTgyYzFmMjFjZTY4NTA0ODNiN2I1ZnVzZXJUb2tlbj00MiZ0YWdGaWx0ZXJzPSUyOHB1YmxpYyUyQ3VzZXIxJTI5"
        key2_2 = "OGYwN2NlNTdlOGM2ZmM4MjA5NGM0ZmYwNTk3MDBkNzMzZjQ0MDI3MWZjNTNjM2Y3YTAzMWM4NTBkMzRiNTM5YnRhZ0ZpbHRlcnM9JTI4cHVibGljJTJDdXNlcjElMjkmdXNlclRva2VuPTQy"
        gen2_1 = self.client.generate_secured_api_key("182634d8894831d5dbce3b3185c50881", {'tagFilters': "(public,user1)", 'userToken': '42'})
        self.assertTrue(key2_1 == gen2_1 or key2_2 == gen2_1)

        gen2_2 = self.client.generate_secured_api_key("182634d8894831d5dbce3b3185c50881", {'tagFilters': "(public,user1)"}, '42')
        self.assertTrue(key2_1 == gen2_2 or key2_2 == gen2_2)

    def test_disjunctive_faceting(self):
        self.index.set_settings(
            {'attributesForFacetting': ['city', 'stars', 'facilities']})
        task = self.index.add_objects([{
            'name': 'Hotel A',
            'stars': '*',
            'facilities': ['wifi', 'bath', 'spa'],
            'city': 'Paris'
        }, {
            'name': 'Hotel B',
            'stars': '*',
            'facilities': ['wifi'],
            'city': 'Paris'
        }, {
            'name': 'Hotel C',
            'stars': '**',
            'facilities': ['bath'],
            'city': 'San Francisco'
        }, {
            'name': 'Hotel D',
            'stars': '****',
            'facilities': ['spa'],
            'city': 'Paris'
        }, {
            'name': 'Hotel E',
            'stars': '****',
            'facilities': ['spa'],
            'city': 'New York'
        }, ])
        self.index.wait_task(task['taskID'])

        answer = self.index.search_disjunctive_faceting(
            'h', ['stars', 'facilities'], {'facets': 'city'})
        self.assertEquals(answer['nbHits'], 5)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)

        answer = self.index.search_disjunctive_faceting('h', [
            'stars', 'facilities'
        ], {'facets': 'city'}, {'stars': ['*']})
        self.assertEquals(answer['nbHits'], 2)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['**'], 1)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 2)

        answer = self.index.search_disjunctive_faceting('h', [
            'stars', 'facilities'
        ], {'facets': 'city'}, {'stars': ['*'],
                                'city': ['Paris']})
        self.assertEquals(answer['nbHits'], 2)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 1)

        answer = self.index.search_disjunctive_faceting('h', [
            'stars', 'facilities'
        ], {'facets': 'city'}, {'stars': ['*', '****'],
                                'city': ['Paris']})
        self.assertEquals(answer['nbHits'], 3)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 1)
