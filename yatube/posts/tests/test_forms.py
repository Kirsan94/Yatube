from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group, User, Comment


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='LevKharkov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='Test_Slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст не измененного поста',
            author=cls.user
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.guest_client = Client()
        self.text_post_new = 'Тестовый текст нового поста'
        self.text_post_edited = 'Тестовый текст измененного поста'
        self.post_create = reverse('posts:post_create')
        self.post_edit = reverse('posts:post_edit', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.profile = reverse('posts:profile', kwargs={
            'username': f'{self.user.username}'
        })
        self.post_detail = reverse('posts:post_detail', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.add_comment = reverse('posts:add_comment', kwargs={
            'post_id': f'{self.post.id}'
        })
        self.comment = {'text': 'Тестовый комментарий'}

    def test_forms_valid_post_creating(self):
        """При отправке валидной формы пост создаётся"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.text_post_new,
            'group': self.group.pk
        }
        response = self.user_client.post(
            self.post_create,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, self.profile)
        created_post = Post.objects.latest('id')
        post_fields = {
            created_post.text: self.text_post_new,
            created_post.author: self.user,
            created_post.group: self.group
        }
        for field_value, expected_value in post_fields.items():
            with self.subTest(field_value=field_value):
                self.assertEqual(field_value, expected_value)

    def test_forms_valid_post_edit(self):
        """При отправке валидной формы пост редактируется"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.text_post_edited,
            'group': self.group.pk
        }
        response = self.user_client.post(
            self.post_edit,
            data=form_data,
            follow=True
        )
        self.saved_post = Post.objects.get(id=self.post.id)
        post_fields = {
            Post.objects.count(): posts_count,
            self.saved_post.text: self.text_post_edited,
            self.saved_post.author: self.user,
            self.saved_post.group: self.group
        }
        for field_value, expected_value in post_fields.items():
            with self.subTest(field_value=field_value):
                self.assertEqual(field_value, expected_value)

        self.assertRedirects(response, self.post_detail)

    def test_forms_post_text_exist(self):
        """Текст поста не пустой"""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'author': self.user
        }
        response = self.user_client.post(
            self.post_create,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Текст поста не должен быть пустым'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_forms_guest_cant_create_post(self):
        """Неавторизированный пользователь не может создать пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'А я не авторизован',
            'group': self.group.pk
        }
        self.guest_client.post(
            self.post_create,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        last_post = Post.objects.latest('id')
        self.assertNotEqual(last_post.text, 'А я не авторизован')

    def test_forms_guest_cant_create_comment(self):
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

    def test_forms_comment_in_context(self):
        """
        После успешной отправки комментарий
        появляется на странице поста
        """
        test_comment = self.user_client.post(
            self.add_comment,
            data=self.comment,
            follow=True
        )
        created_comment = Comment.objects.latest('pk')
        comment_field = {
            created_comment.text: self.comment['text'],
            created_comment.post: test_comment.context['post'],
        }
        for new, original in comment_field.items():
            with self.subTest(new=new):
                self.assertEqual(new, original)
