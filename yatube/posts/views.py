from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Comment, Follow
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page
from django.core.cache import cache

POSTS_Q: int = 10


def paginations(request, posts):
    paginator = Paginator(posts, POSTS_Q)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)

@cache_page(20, key_prefix="index_page")   
def index(request):
    posts = Post.objects.select_related('group').all()
    page_obj = paginations(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginations(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginations(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post.pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)

    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)

@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        post = get_object_or_404(Post, pk=post_id)
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id) 

@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Все посты авторов, на которых подписан'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginations(request, posts)
    context = {
        'title': title,
        'page_obj': page_obj
    }
    return render(request, template, context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.you_can_follow(request.user, author):
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)

@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.get(
        user=request.user,
        author=author
    ).delete()
    return redirect('posts:profile', username)
  

