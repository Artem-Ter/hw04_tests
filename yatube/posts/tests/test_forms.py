# posts/tests/test_forms.py
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostCreateFormTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем авторизованный клент.
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверяет, что при отправке валидной формы
        со страницы создания поста reverse('posts:post_create')
        создаётся новая запись в базе данных"""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test_text'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text='test_text'
            ).exists()
        )

    def test_post_edit(self):
        """Проверяет, что при отправке валидной формы со страницы
        редактирования поста reverse('posts:post_edit', args=('post_id',)),
        происходит изменение поста с post_id в базе данных."""
        self.post = Post.objects.create(
            author=self.user,
            text='test_text_1'
        )
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'edited_text'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        # Проверяем, что число постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что запись с измененным текстом существует
        self.assertTrue(Post.objects.filter(text='edited_text').exists())
