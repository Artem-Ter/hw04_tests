# posts/tests/test_urls.py
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Создаем неавторизованный клиент
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Создаем Автора
        self.author = Client()
        self.author.force_login(PostUrlTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_html_pages_available(self):
        """Проверяет доступ к страницам Posts
        с учетом прав доступа пользователей."""
        # Шаблоны по адресам
        url_names = (
            '/',
            '/group/test-slug/',
            '/profile/auth/',
            '/posts/1/',
            '/create/',
            '/posts/1/edit/',
            '/unexisting_page/',
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                response_authorized = self.authorized_client.get(address)
                response_author = self.author.get(address)
                if address == '/unexisting_page/':
                    self.assertEqual(response.status_code, 404)
                elif address == '/posts/1/edit/':
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response_authorized.status_code, 302)
                    self.assertEqual(response_author.status_code, 200)
                elif address == '/create/':
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response_authorized.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 200)
