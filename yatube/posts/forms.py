from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
            'image': ('Изображение'),
        }
        text_help = {
            'text': ('Текст поста'),
            'group': ('Группа, к которой относистя пост'),
            'image': ('Изображение поста'),
        }

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['text'].error_messages = {
            'required': 'Текст поста не должен быть пустым'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
                'text': ('Текст комментария'),
        }
        text_help = {
                'text': ('Текст комментария'),
        }

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].error_messages = {
            'required': 'Текст комментария не должен быть пустым'
        }
