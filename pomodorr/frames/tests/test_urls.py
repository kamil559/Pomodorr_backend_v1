from django.urls import reverse


class TestDateFrameUrls:
    def test_list_url(self):
        url = reverse('api:date_frame-list')
        assert url is not None
