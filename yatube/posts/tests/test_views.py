from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User
from ..forms import PostForm


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.REVERSE_INDEX = reverse('posts:index')
        cls.REVERSE_GROUP_LIST = (
            reverse('posts:group_list', kwargs={'slug': cls.group.slug})
        )
        cls.REVERSE_PROFILE = (
            reverse('posts:profile', kwargs={'username': cls.post.author})
        )
        cls.REVERSE_POST_DETAIL = (
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id})
        )
        cls.REVERSE_POST_EDIT = (
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id})
        )
        cls.REVERSE_POST_CREATE = reverse('posts:post_create')

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.REVERSE_INDEX: 'posts/index.html',
            self.REVERSE_GROUP_LIST: 'posts/group_list.html',
            self.REVERSE_PROFILE: 'posts/profile.html',
            self.REVERSE_POST_DETAIL: 'posts/post_detail.html',
            self.REVERSE_POST_EDIT: 'posts/create_post.html',
            self.REVERSE_POST_CREATE: 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны с постами отображают ожидаемый контекст."""
        # Создаем словарь с reverse_name и ожидаемым контекстом
        reverse_expected_context = {
            self.REVERSE_INDEX: list(Post.objects.all()),
            self.REVERSE_GROUP_LIST: (
                list(Post.objects.filter(group_id=self.group.id))
            ),
            self.REVERSE_PROFILE: (
                list(Post.objects.filter(author_id=self.user.id))
            ),
        }
        for reverse_name, expected_value in reverse_expected_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_object = list(response.context['page_obj'])
                self.assertEqual(response_object, expected_value)

    def test_post_detail_page_show_correct_context(self):
        """Пост отфильтрованный по id в шаблоне
        post_detail соответсвует контексту."""
        response = self.authorized_client.get(
            PostPagesTest.REVERSE_POST_DETAIL)
        expected = Post.objects.get(id=PostPagesTest.post.id)
        self.assertEqual(response.context['post'], expected)

    def test_post_edit_and_create_pages_show_correct_context(self):
        """Шаблоны post_edit и post_create
        сформированы с правильным контекстом"""
        url_names = (
            self.REVERSE_POST_EDIT,
            self.REVERSE_POST_CREATE,
        )
        for reverse_name in url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )
                self.assertIsInstance(response.context['form'], PostForm)
                if 'is_edit' in response.context.keys():
                    self.assertTrue(response.context['is_edit'])
                    self.assertEqual(response.context['post'], self.post)

    def test_post_with_group_on_right_pages(self):
        """Проверяем, что пост с указанной группой отображается:
        на главной странице сайта,
        на странице выбранной группы,
        в профайле пользователя."""
        result = Post.objects.get(group=PostPagesTest.post.group)
        check_pages = (
            PostPagesTest.REVERSE_INDEX,
            PostPagesTest.REVERSE_GROUP_LIST,
            PostPagesTest.REVERSE_PROFILE
        )
        for page in check_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                response_obj = response.context['page_obj']
                self.assertIn(result, response_obj)

    def test_post_with_group_not_in_wrong_group_list(self):
        """Проверяем, что пост с указанной группой не попал в группу,
        для которой не был предназначен."""
        group_1 = Group.objects.create(
            title='Тест_группа_1',
            slug='test_slug_1',
            description='Тестовое_описание_1',
        )
        result = Post.objects.get(group=PostPagesTest.post.group)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_1.slug})
        )
        self.assertNotIn(result, response.context['page_obj'])
