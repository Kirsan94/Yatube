from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='LevKharkov')
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='Test',
            description='Group for test'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_user = User.objects.create_user(username='NotLevKharkov')
        self.another_user_client = Client()
        self.another_user_client.force_login(self.another_user)

    def test_urls_exists_for_guest(self):
        """Проверяем наличие страниц для гостя"""
        urls = [
            '/',
            '/about/author/',
            '/about/tech/',
            '/auth/login/',
            '/auth/signup/',
            f'/posts/{self.post.id}/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_for_user(self):
        """Проверяем наличие страниц для авторизованного пользователя"""
        urls = [
            '/',
            '/follow/',
            '/create/',
            '/about/tech/',
            '/about/author/',
            f'/posts/{self.post.id}/',
            f'/group/{self.group.slug}/',
            f'/posts/{self.post.id}/edit/',
            f'/profile/{self.user.username}/',
            '/auth/logout/',

        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_missing_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('missing_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Проверяем корректность использованных шаблонов"""
        urls_templates = {
            '/': 'posts/index.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            '/missing_page/': 'core/404.html',
            '/follow/': 'posts/follow.html',
            '/auth/logout/': 'users/logged_out.html',
        }
        for url, template in urls_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_guest_create_redirect(self):
        """Проверяем корректность редиректа при создании поста гостем"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_urls_guest_edit_redirect(self):
        """Проверяем корректность редиректа при изменении поста гостем"""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/edit/'))

    def test_urls_another_user_edit_redirect(self):
        """Проверяем корректность редиректа при изменении поста не автором"""
        response = self.another_user_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/')
        )
