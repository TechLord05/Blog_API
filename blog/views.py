from django.core.cache import cache
from rest_framework import viewsets, permissions
from .models import Post, Comment, Follower
from .serializers import PostSerializer, CommentSerializer, UserRegistrationSerializer, FollowerSerializer
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly
from .tasks import send_welcome_email, notify_followers


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing blog posts with caching and filtering."""
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'author__username']  # Allow filtering by title and author's username


    # Caching the list of posts
    def list(self, request, *args, **kwargs):
        cache_key = 'posts_list'
        cached_response = cache.get(cache_key)
    
        if cached_response:
            print("Cache hit")
            return Response(cached_response)

        print("Cache miss")
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60)  # Cache for 60 seconds
        return response

    # Retrieve individual post with caching
    def retrieve(self, request, *args, **kwargs):
        post_id = kwargs['pk']
        cached_key = f"post_{post_id}"
        cached_post = cache.get(cached_key)

        if cached_post:
            print("Cache hit for single post")
            return Response(cached_post)

        print("Cache miss for single post")
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cached_key, response.data, timeout=60)  # Cache for 60 seconds
        return response

    # ------- Create post and notify followers asynchronously -------
    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the author
        post = serializer.save(author=self.request.user)
        # Async notification
        notify_followers.delay(post.title, post.author.id)
        cache.delete('posts_list')  # Invalidate the cached posts list
        cache.delete(f"post_{post.id}")  # Invalidate the cached individual post


    def perform_update(self, serializer):
        post = serializer.save()
        cache.delete('posts_list')
        cache.delete(f"post_{post.id}")


    def perform_destroy(self, instance):
        post_id = instance.id
        instance.delete()
        cache.delete('posts_list')
        cache.delete(f"post_{post_id}")


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing comments with caching."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.all().order_by('-created_at').select_related('author', 'post')
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def list(self, request, *args, **kwargs):
        post_id = request.query_params.get('post')
        cache_key = f"comments_post_{post_id}" if post_id else "comments_all"

        cached_comments = cache.get(cache_key)
        if cached_comments:
            print(f"⚡ Cache hit for {cache_key}")
            return Response(cached_comments)

        print(f"💾 Cache miss for {cache_key}")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=60 * 10)  # 10 minutes
        return Response(serializer.data)

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        cache_key = f"comments_post_{comment.post.id}"
        cache.delete(cache_key)  # invalidate cache when new comment is added

    def perform_update(self, serializer):
        comment = serializer.save()
        cache_key = f"comments_post_{comment.post.id}"
        cache.delete(cache_key)  # invalidate cache when comment is updated

    def perform_destroy(self, instance):
        post_id = instance.post.id
        instance.delete()
        cache.delete(f"comments_post_{post_id}")  # invalidate cache when comment is deleted


class FollowerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing followers."""
    serializer_class = FollowerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Follower.objects.none()
        return Follower.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the user to the logged-in user
        serializer.save(user=self.request.user)


    @action(detail=False, methods=['post'], url_path='unfollow')
    def unfollow(self, request):
        # Logic to unfollow a user
        follows_id = request.data.get('follows')
        if not follows_id:
            return Response({"error": "follows_id is required"}, status=400)

        try:
            follows = Follower.objects.get(follows=follows_id, user=request.user)
            follows.delete()
            return Response({"success": "Unfollowed successfully"}, status=204)
        except Follower.DoesNotExist:
            return Response({"error": "Follow relationship does not exist"}, status=404)


class UserRegistrationViewSet(viewsets.ModelViewSet):
    """ViewSet for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()

