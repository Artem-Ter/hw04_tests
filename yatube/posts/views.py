from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User
from .utils import split_pages
from .forms import PostForm


VIEW_ELEMENTS = 10


# Главная страница
def index(request):
    '''Передаёт в шаблон posts/index.html
    десять объектов модели Post на каждой странице.'''
    template = 'posts/index.html'
    post_list = Post.objects.all()
    context = {
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
    }
    return render(request, template, context)


# Страница с групповыми постами
def group_posts(request, slug):
    '''Передаёт в шаблон posts/group_list.html
    десять объектов модели Post на каждой странице,
    отфильтрованных по полю group,
    и содержимое для тега <title>.'''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
    }
    return render(request, template, context)


def profile(request, username):
    """Передает автора с указнным username в шаблон posts/profile
    и его посты по 10 штук на страницу"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    context = {
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
        'author': author,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Передает пост с указанной post_id в шабон posts/post_detail"""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Передает форму из PostForm в шаблон posts/create_post.html
    если форма заполнена верно,
    переводит пользователя на страницу с его профилем"""
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, template, {'form': form})

    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Передает пост с указанным post_id в
    шаблон posts/create_post.html для редактирования.
    Если user не является авторам поста,
    переводит его на странцу с деталями этого поста"""
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    template = 'posts/create_post.html'

    if request.method == 'GET':
        if request.user != post.author:
            return redirect('posts:post_detail', post_id=post.id)
        form = PostForm(instance=post)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post.id)

    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post,
    }

    return render(request, template, context)
