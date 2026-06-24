# community/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Topic, Thread, Post, PostVote, UserActivity
from .forms import ThreadForm, PostForm

def community_page(request):
    """Main community page showing all topics"""
    topics = Topic.objects.filter(is_active=True).annotate(
        thread_count=Count('threads', filter=Q(threads__is_active=True)),
        post_count=Count('threads__posts', filter=Q(threads__posts__is_active=True)),
        latest_post_time=Max('threads__posts__created_at')
    ).order_by('name')
    
    # Get recent activity
    recent_threads = Thread.objects.filter(is_active=True).select_related(
        'author', 'topic'
    ).order_by('-created_at')[:5]
    
    recent_posts = Post.objects.filter(is_active=True).select_related(
        'author', 'thread', 'thread__topic'
    ).order_by('-created_at')[:5]
    
    # Get forum statistics
    total_threads = Thread.objects.filter(is_active=True).count()
    total_posts = Post.objects.filter(is_active=True).count()
    total_members = UserActivity.objects.count()
    
    context = {
        'topics': topics,
        'recent_threads': recent_threads,
        'recent_posts': recent_posts,
        'stats': {
            'total_threads': total_threads,
            'total_posts': total_posts,
            'total_members': total_members,
        }
    }
    return render(request, 'community/community.html', context)

def topic_detail(request, pk):
    """Show threads for a specific topic"""
    topic = get_object_or_404(Topic, pk=pk, is_active=True)
    
    # Get threads with search functionality
    search_query = request.GET.get('search', '')
    threads = Thread.objects.filter(topic=topic, is_active=True).select_related('author')
    
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    # Order threads (pinned first, then by latest activity)
    threads = threads.annotate(
        post_count=Count('posts', filter=Q(posts__is_active=True)),
        latest_post_time=Max('posts__created_at')
    ).order_by('-is_pinned', '-updated_at')
    
    # Pagination
    paginator = Paginator(threads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'topic': topic,
        'threads': page_obj,
        'search_query': search_query,
        'page_obj': page_obj,
    }
    return render(request, 'community/topic_detail.html', context)

def thread_detail(request, pk):
    """Show posts in a specific thread"""
    thread = get_object_or_404(Thread, pk=pk, is_active=True)
    
    # Increment view count
    thread.increment_views()
    
    # Get posts
    posts = Post.objects.filter(thread=thread, is_active=True).select_related(
        'author', 'author__profile'
    ).prefetch_related('votes')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Post form for replies
    post_form = PostForm() if request.user.is_authenticated else None
    
    context = {
        'thread': thread,
        'posts': page_obj,
        'post_form': post_form,
        'page_obj': page_obj,
    }
    return render(request, 'community/thread_detail.html', context)

@login_required
def create_thread(request, topic_pk):
    """Create a new thread in a topic"""
    topic = get_object_or_404(Topic, pk=topic_pk, is_active=True)
    
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.topic = topic
            thread.author = request.user
            thread.save()
            
            # Update user activity
            activity, created = UserActivity.objects.get_or_create(user=request.user)
            activity.update_thread_count()
            
            messages.success(request, 'Thread created successfully!')
            return redirect('community:thread_detail', pk=thread.pk)
    else:
        form = ThreadForm()
    
    context = {
        'form': form,
        'topic': topic,
    }
    return render(request, 'community/create_thread.html', context)

@login_required
@require_POST
def create_post(request, thread_pk):
    """Create a new post in a thread"""
    thread = get_object_or_404(Thread, pk=thread_pk, is_active=True)
    
    if thread.is_locked:
        messages.error(request, 'This thread is locked.')
        return redirect('community:thread_detail', pk=thread.pk)
    
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.thread = thread
        post.author = request.user
        post.save()
        
        # Update thread's updated_at timestamp
        thread.updated_at = timezone.now()
        thread.save(update_fields=['updated_at'])
        
        # Update user activity
        activity, created = UserActivity.objects.get_or_create(user=request.user)
        activity.update_post_count()
        
        messages.success(request, 'Reply posted successfully!')
        return redirect('community:thread_detail', pk=thread.pk)
    
    messages.error(request, 'Error posting reply. Please try again.')
    return redirect('community:thread_detail', pk=thread.pk)

@login_required
@require_POST
def vote_post(request, post_pk):
    """Vote on a post (AJAX endpoint)"""
    post = get_object_or_404(Post, pk=post_pk, is_active=True)
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    vote_value = 1 if vote_type == 'up' else -1
    
    # Check if user already voted
    existing_vote = PostVote.objects.filter(post=post, user=request.user).first()
    
    if existing_vote:
        if existing_vote.vote == vote_value:
            # Remove vote if clicking same button
            existing_vote.delete()
            user_vote = None
        else:
            # Change vote
            existing_vote.vote = vote_value
            existing_vote.save()
            user_vote = vote_value
    else:
        # Create new vote
        PostVote.objects.create(post=post, user=request.user, vote=vote_value)
        user_vote = vote_value
    
    # Calculate new vote counts
    upvotes = PostVote.objects.filter(post=post, vote=1).count()
    downvotes = PostVote.objects.filter(post=post, vote=-1).count()
    score = upvotes - downvotes
    
    return JsonResponse({
        'upvotes': upvotes,
        'downvotes': downvotes,
        'score': score,
        'user_vote': user_vote
    })

def search_threads(request):
    """Search threads across all topics"""
    query = request.GET.get('q', '')
    topic_filter = request.GET.get('topic', '')
    
    threads = Thread.objects.filter(is_active=True).select_related('author', 'topic')
    
    if query:
        threads = threads.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
    
    if topic_filter:
        threads = threads.filter(topic__pk=topic_filter)
    
    threads = threads.annotate(
        post_count=Count('posts', filter=Q(posts__is_active=True))
    ).order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(threads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get topics for filter dropdown
    topics = Topic.objects.filter(is_active=True).order_by('name')
    
    context = {
        'threads': page_obj,
        'query': query,
        'topic_filter': topic_filter,
        'topics': topics,
        'page_obj': page_obj,
    }
    return render(request, 'community/search_results.html', context)

@login_required
def user_profile(request, username):
    """Show user's forum activity"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, username=username)
    activity, created = UserActivity.objects.get_or_create(user=user)
    
    # Get user's recent threads and posts
    recent_threads = Thread.objects.filter(
        author=user, is_active=True
    ).select_related('topic').order_by('-created_at')[:10]
    
    recent_posts = Post.objects.filter(
        author=user, is_active=True
    ).select_related('thread', 'thread__topic').order_by('-created_at')[:10]
    
    context = {
        'profile_user': user,
        'activity': activity,
        'recent_threads': recent_threads,
        'recent_posts': recent_posts,
    }
    return render(request, 'community/user_profile.html', context)

@login_required
def edit_thread(request, thread_pk):
    """Edit a thread"""
    thread = get_object_or_404(Thread, pk=thread_pk)
    
    if request.user != thread.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this thread.')
        return redirect('community:thread_detail', pk=thread.pk)
        
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thread updated successfully!')
            return redirect('community:thread_detail', pk=thread.pk)
    else:
        form = ThreadForm(instance=thread)
        
    context = {
        'form': form,
        'thread': thread,
        'is_edit': True
    }
    return render(request, 'community/create_thread.html', context)

@login_required
@require_POST
def delete_thread(request, thread_pk):
    """Delete a thread"""
    thread = get_object_or_404(Thread, pk=thread_pk)
    
    if request.user != thread.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this thread.')
        return redirect('community:thread_detail', pk=thread.pk)
        
    topic_pk = thread.topic.pk
    thread.delete()
    messages.success(request, 'Thread deleted successfully!')
    return redirect('community:topic_detail', pk=topic_pk)

@login_required
def edit_post(request, post_pk):
    """Edit a post"""
    post = get_object_or_404(Post, pk=post_pk)
    
    if request.user != post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('community:thread_detail', pk=post.thread.pk)
        
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('community:thread_detail', pk=post.thread.pk)
    else:
        form = PostForm(instance=post)
        
    context = {
        'form': form,
        'post': post,
        'is_edit': True
    }
    # In a full app you might use a dedicated edit template or a modal,
    # but rendering the thread page again with the form prefilled might be easier
    # Let's render a simple standalone template or reuse something.
    # To keep it simple without creating a new template, we'll pass it to thread_detail but mark it as edit.
    # Actually, we should probably create an 'edit_post.html' or redirect to it.
    return render(request, 'community/edit_post.html', context)

@login_required
@require_POST
def delete_post(request, post_pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=post_pk)
    
    if request.user != post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('community:thread_detail', pk=post.thread.pk)
        
    thread_pk = post.thread.pk
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('community:thread_detail', pk=thread_pk)