from rest_framework.routers import DefaultRouter
from  .views import PostViewSet, CommentViewSet, FollowerViewSet, UserRegistrationViewSet


router = DefaultRouter()
router.register(r'register', UserRegistrationViewSet, basename='user-registration')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'followers', FollowerViewSet, basename='followers')

urlpatterns = router.urls
