from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='LevKharkov')
        cls.index = reverse('posts:index')
        cls.post = Post.objects.create(
            text='Тестовый текст поста для кеша',
            author=cls.user
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_index_post_list_cache(self):
        """
        Список записей главной страницы
        хранится в кеше и обновлялся раз в 20 секунд
        """
        cache.clear()
        response_one = self.client.get(self.index)
        cache.set('index_page', response_one.content, 20)
        self.assertEqual(response_one.content, cache.get('index_page'))
        self.post.delete()
        response_two = self.client.get(self.index)
        self.assertEqual(response_two.content, cache.get('index_page'))
        cache.clear()
        response_last = self.client.get(self.index)
        self.assertNotEqual(response_last.content, cache.get('index_page'))
