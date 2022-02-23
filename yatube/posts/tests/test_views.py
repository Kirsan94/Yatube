import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from http import HTTPStatus

from ..models import Post, Group, User, Comment, Follow
from ..forms import PostForm
from ..views import POSTS_COUNT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='LevKharkov')
        cls.another_user = User.objects.create_user(username='NotLevKharkov')
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='Test',
            description='Group for test'
        )
        cls.another_group = Group.objects.create(
            title='AnotherTestGroup',
            slug='AnotherTest',
            description='Another group for test'
        )
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)
        self.index = reverse('posts:index')
        self.post_create = reverse('posts:post_create')
        self.post_edit = reverse('posts:post_edit', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.post_detail = reverse('posts:post_detail', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.add_comment = reverse('posts:add_comment', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.profile = reverse('posts:profile', kwargs={
            'username': f'{self.user.username}'
        })
        self.group_list = reverse('posts:group_list', kwargs={
            'slug': f'{self.group.slug}'
        })
        self.another_group_list = reverse('posts:group_list', kwargs={
            'slug': f'{self.another_group.slug}'
        })
        self.follow_index = reverse('posts:follow_index')
        self.profile_follow = reverse('posts:profile_follow', kwargs={
            'username': f'{self.user.username}'
        })
        self.profile_unfollow = reverse('posts:profile_unfollow', kwargs={
            'username': f'{self.user.username}'
        })
        self.comment = {'text': 'Тестовый комментарий'}

    def test_views_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.index: 'posts/index.html',
            self.post_create: 'posts/create_post.html',
            self.post_edit: 'posts/create_post.html',
            self.post_detail: 'posts/post_detail.html',
            self.profile: 'posts/profile.html',
            self.group_list: 'posts/group_list.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_views_index_context(self):
        """Проверяем контекст index"""
        response = self.authorized_client.get(self.index)
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.post, response.context['page_obj'][0])

    def test_views_post_create_context(self):
        """Проверяем контекст post_create"""
        response = self.authorized_client.get(self.post_create)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertNotIn('is_edit', response.context)

    def test_views_post_edit_context(self):
        """Проверяем контекст post_edit"""
        response = self.authorized_client.get(self.post_edit)
        self.assertEqual(response.context['post_id'], self.post.id)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_edit', response.context)
        self.assertTrue(response.context['is_edit'])

    def test_views_post_detail_context(self):
        """Проверяем контекст post_detail"""
        response = self.authorized_client.get(self.post_detail)
        post_title = f'Пост: {self.post.text}'
        self.assertEqual(post_title, response.context['title'])
        self.assertEqual(self.post, response.context['post'])
        self.assertEqual(self.post.pk, response.context['posts_count'])

    def test_views_profile_context(self):
        """Проверяем контекст profile"""
        response = self.authorized_client.get(self.profile)
        self.assertEqual(self.user, response.context['author'])
        self.assertEqual(self.post, response.context['page_obj'][0])

    def test_views_group_list_context(self):
        """Проверяем контекст group_list."""
        response = self.authorized_client.get(self.group_list)
        page_object = response.context['page_obj'][0]
        group_object = page_object.group
        self.assertEqual(page_object, self.post)
        self.assertEqual(group_object, self.group)

    def test_views_group_post_creation(self):
        """Пост не отражается не в своей группе"""
        response = self.authorized_client.get(self.another_group_list)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_views_image_in_context(self):
        """
        Пост сохраняется, а при выводе поста
        с картинкой изображение передаётся в словаре context
        """
        posts_count = Post.objects.count()
        pages = [self.index, self.profile, self.group_list]
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    response.context['page_obj'][0].image,
                    'posts/small.gif'
                )
        response = self.client.get(self.post_detail)
        self.assertEqual(response.context['post'].image, 'posts/small.gif')
        Post.objects.create(
            text='Тестовый текст поста с картинкой',
            author=self.user,
            group=self.group,
            image=self.uploaded
        )
        self.assertEqual(posts_count + 1, Post.objects.count())

    def test_views_guest_cant_create_comment(self):
        """
        Комментировать посты может
        только авторизованный пользователь
        """
        comments_count = Comment.objects.count()
        create_comment = self.guest_client.post(
            self.add_comment,
            data=self.comment,
            follow=True
        )
        self.assertEqual(create_comment.status_code, HTTPStatus.OK)
        self.assertEqual(comments_count, Comment.objects.count())

    def test_views_comment_in_context(self):
        """
        После успешной отправки комментарий
        появляется на странице поста
        """
        create_comment = self.authorized_client.post(
            self.add_comment,
            data=self.comment,
            follow=True
        )
        comment = create_comment.context['comments']
        self.assertEqual(len(comment), 1)

    def test_views_user_can_follow_and_unfollow(self):
        """
        Авторизованный пользователь может
        подписываться на других пользователей и удалять их из подписок
        """
        response = self.another_authorized_client.get(self.profile_follow)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Follow.objects.filter(
                user=self.another_user,
                author=self.user
            ).exists()
        )
        response = self.another_authorized_client.get(self.profile_unfollow)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(
            Follow.objects.filter(
                user=self.another_user,
                author=self.user
            ).exists()
        )

    def test_views_new_post_seen_if_followed(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан
        """
        response = self.another_authorized_client.get(self.follow_index)
        self.assertEqual(len(response.context['page_obj']), 0)
        self.another_authorized_client.get(self.profile_follow)
        response = self.another_authorized_client.get(self.follow_index)
        self.assertEqual(len(response.context['page_obj']), 1)


class PostViewsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='LevKharkov')
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='Test',
            description='Group for test'
        )
        bulk_size = 15
        posts = [
            Post(
                text=f'Тестовый текст {post_num}',
                author=cls.user,
                group=cls.group
            )
            for post_num in range(bulk_size)
        ]
        Post.objects.bulk_create(posts, bulk_size)

    def setUp(self):
        self.paginator_length = POSTS_COUNT
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.index = reverse('posts:index')
        self.profile = reverse('posts:profile', kwargs={
            'username': f'{self.user.username}'
        })
        self.group_list = reverse('posts:group_list', kwargs={
            'slug': f'{self.group.slug}'
        })

    def test_views_paginator(self):
        """Проверяем работает ли пагинатор там, где он должен быть"""
        pages = [self.index, self.profile, self.group_list]
        posts_count = Post.objects.count()
        second_page_posts_count = posts_count - self.paginator_length
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                response2 = self.client.get(page + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.paginator_length
                )
                self.assertEqual(
                    len(response2.context['page_obj']),
                    second_page_posts_count
                )
