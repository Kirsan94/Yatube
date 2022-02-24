from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, текст которого должен превратиться в слаг',
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        str_test_dict = {
            str(self.group): self.group.title,
            str(self.post): self.post.text[:15]
        }
        for str_value, expected_str in str_test_dict.items():
            with self.subTest(str_value=str_value):
                self.assertEqual(str_value, expected_str)

    def test_post_verbose_help_is_right(self):
        """Проверяем verbose_name и help_text поста"""
        text_verbose = self.post._meta.get_field('text').verbose_name
        text_help = self.post._meta.get_field('text').help_text
        date_verbose = self.post._meta.get_field('pub_date').verbose_name
        author_verbose = self.post._meta.get_field('author').verbose_name
        group_verbose = self.post._meta.get_field('group').verbose_name
        group_help = self.post._meta.get_field('group').help_text
        image_verbose = self.post._meta.get_field('image').verbose_name
        image_help = self.post._meta.get_field('image').help_text
        post_test = {
            text_verbose: 'Текст поста',
            text_help: 'Введите текст поста',
            date_verbose: 'Дата публикации',
            author_verbose: 'Автор',
            group_verbose: 'Группа',
            group_help: 'Группа, к которой будет относиться пост',
            image_verbose: 'Изображение',
            image_help: 'Изображение в шапке поста'
        }
        for field, expected_value in post_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
