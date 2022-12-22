from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Post, Group, User


class PostPagesTest(TestCase):
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
        # Создаем словарь с reverse_name и ожидаемым контекстом
        cls.reverse_expected_context = {
            cls.REVERSE_INDEX: list(Post.objects.all()),
            cls.REVERSE_GROUP_LIST: (
                list(Post.objects.filter(group_id=cls.group.id))
            ),
            cls.REVERSE_PROFILE: (
                list(Post.objects.filter(author_id=cls.user.id))
            ),
        }

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.templates_pages_names = {
            PostPagesTest.REVERSE_INDEX: 'posts/index.html',
            PostPagesTest.REVERSE_GROUP_LIST: 'posts/group_list.html',
            PostPagesTest.REVERSE_PROFILE: 'posts/profile.html',
            PostPagesTest.REVERSE_POST_DETAIL: 'posts/post_detail.html',
            PostPagesTest.REVERSE_POST_EDIT: 'posts/create_post.html',
            PostPagesTest.REVERSE_POST_CREATE: 'posts/create_post.html',
        }
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны с постами отображают ожидаемый контекст."""
        reverse_expected_value = PostPagesTest.reverse_expected_context.items()
        for reverse_name, expected_value in reverse_expected_value:
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

    def test_post_edit_page_show_correct_context(self):
        """Форма редактирования поста в шаблоне
        create_post соотвесвует контексту"""
        response = self.authorized_client.get(
            PostPagesTest.REVERSE_POST_EDIT)
        form_fields = {
            'text': (forms.fields.CharField, PostPagesTest.post.text),
            'group': (forms.models.ModelChoiceField, PostPagesTest.post.group)
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                form_value = eval(f"response.context['post'].{value}")
                self.assertIsInstance(form_field, expected[0])
                self.assertEqual(form_value, expected[1])

    def test_post_create_page_show_correct_context(self):
        """Форма create_post соотвесвует контексту"""
        response = self.authorized_client.get(
            PostPagesTest.REVERSE_POST_CREATE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

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
