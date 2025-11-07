import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from blog.models import Post, Comment, Follower

# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username='testuser', password='testpass')

@pytest.fixture
def auth_client(api_client, test_user):
    response = api_client.post('/api/login/', {'username': 'testuser', 'password': 'testpass'})
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client

# ----------------------------
# Post tests
# ----------------------------
@pytest.mark.django_db
def test_create_post(auth_client):
    payload = {"title": "Test Post", "body": "This is a test post."}
    response = auth_client.post('/api/posts/', payload)
    assert response.status_code == 201
    assert response.data['title'] == "Test Post"

@pytest.mark.django_db
def test_list_posts(auth_client, test_user):
    Post.objects.create(title="Existing Post", body="Content", author=test_user)
    Post.objects.create(title="Another Post", body="More Content", author=test_user)
    response = auth_client.get('/api/posts/')
    assert response.status_code == 200
    assert len(response.data) >= 2

@pytest.mark.django_db
def test_update_post(auth_client, test_user):
    post = Post.objects.create(title="Old", body="Old", author=test_user)
    payload = {"title": "Updated", "body": "Updated"}
    response = auth_client.put(f'/api/posts/{post.id}/', payload)
    assert response.status_code == 200
    assert response.data['title'] == "Updated"

@pytest.mark.django_db
def test_delete_post(auth_client, test_user):
    post = Post.objects.create(title="To delete", body="Content", author=test_user)
    response = auth_client.delete(f'/api/posts/{post.id}/')
    assert response.status_code == 204

# ----------------------------
# Comment tests
# ----------------------------
@pytest.mark.django_db
def test_create_comment(auth_client, test_user):
    post = Post.objects.create(title="Post for Comment", body="Content", author=test_user)
    payload  = {"body": "Nice post!", "post": str(post.id)}
    response = auth_client.post('/api/comments/', payload)
    assert response.status_code == 201
    assert response.data['body'] == "Nice post!"

@pytest.mark.django_db
def test_update_comment(auth_client, test_user):
    post = Post.objects.create(title="Post", body="Content", author=test_user)
    comment = Comment.objects.create(post=post, author=test_user, body="Old Comment")
    payload = {"body": "Updated Comment", "post": str(comment.post.id)}
    response = auth_client.put(f'/api/comments/{comment.id}/', payload)
    assert response.status_code == 200
    assert response.data['body'] == "Updated Comment"

@pytest.mark.django_db
def test_delete_comment(auth_client, test_user):
    post = Post.objects.create(title="Post", body="Content", author=test_user)
    comment = Comment.objects.create(post=post, author=test_user, body="Comment to delete")
    response = auth_client.delete(f'/api/comments/{comment.id}/')
    assert response.status_code == 204

# ----------------------------
# User registration & login
# ----------------------------
@pytest.mark.django_db
def test_user_registration(api_client):
    payload = {"username": "newuser", "email": "newuser@example.com", "password": "newpass"}
    response = api_client.post("/api/register/", payload)
    assert response.status_code == 201
    assert response.data['username'] == "newuser"
    assert 'password' not in response.data  # password should not be returned

@pytest.mark.django_db
def test_login(api_client, test_user):
    payload = {"username": "testuser", "password": "testpass"}
    response = api_client.post("/api/login/", payload)
    assert response.status_code == 200
    assert 'access' in response.data

# ----------------------------
# Follower tests
# ----------------------------
@pytest.mark.django_db
def test_follow_user(auth_client, test_user):
    new_user = User.objects.create_user(username='otheruser', password='otherpass')
    payload = {"follows": new_user.id}
    response = auth_client.post('/api/followers/', payload)
    assert response.status_code == 201
    assert response.data['follows'] == new_user.id

@pytest.mark.django_db
def test_unfollow_user(auth_client, test_user):
    other_user = User.objects.create_user(username="otheruser2", password="pass2")
    auth_client.post('/api/followers/', {"follows": other_user.id})
    response = auth_client.post('/api/followers/unfollow/', {"follows": other_user.id})
    assert response.status_code == 204

# ----------------------------
# Unauthorized access
# ----------------------------
@pytest.mark.django_db
def test_post_create_unauthenticated(api_client):
    payload = {"title": "x", "body": "y"}
    response = api_client.post('/api/posts/', payload)
    assert response.status_code == 401

@pytest.mark.django_db
def test_comment_create_unauthenticated(api_client, test_user):
    post = Post.objects.create(title="Post", body="Content", author=test_user)
    payload = {"body": "x", "post": str(post.id)}
    response = api_client.post('/api/comments/', payload)
    assert response.status_code == 401
