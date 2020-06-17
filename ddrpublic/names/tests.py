from django.test import TestCase
from django.urls import reverse


class APINamesViews(TestCase):

    def test_api_names_search(self):
        response = self.client.get(reverse('names-api-search'))
        self.assertEqual(response.status_code, 200)

    def test_api_names_name(self):
        nid = 'far-ancestry:1-topaz_hirabayashi_1890_george'
        response = self.client.get(reverse('names-api-name', args=[nid]))
        self.assertEqual(response.status_code, 200)


class NamesViews(TestCase):

    def test_names_search(self):
        response = self.client.get(reverse('names-search'))
        self.assertEqual(response.status_code, 200)

    def test_names_detail(self):
        nid = 'far-ancestry:1-topaz_hirabayashi_1890_george'
        response = self.client.get(reverse('names-detail', args=[nid]))
        self.assertEqual(response.status_code, 200)
