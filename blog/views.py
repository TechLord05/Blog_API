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
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'author__username']  # Allow filtering by title and author's username


    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the author
        post = serializer.save(author=self.request.user)

        # Async notification
        notify_followers.delay(post.title, post.author.id)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        # Set the author to the logged-in user
        serializer.save(author=self.request.user)


class FollowerViewSet(viewsets.ModelViewSet):
    serializer_class = FollowerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return followers related to the logged-in user
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
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Trigger the Celery task to send welcome email
        send_welcome_email.delay(user.username, user.email)

