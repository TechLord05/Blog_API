from rest_framework import serializers
from .models import Post, Comment, Follower
from django.contrib.auth.models import User

class CommentSerializer(serializers.ModelSerializer):
    created_at = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.StringRelatedField(read_only=True) # shows username instead of ID

    class Meta:
        model = Comment
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True) # shows username instead of ID
    comments = CommentSerializer(many=True, read_only=True) # Nested comments using the related name from the models

    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'author', 'created_at', 'comments']



class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ['id', 'user', 'follows']
        read_only_fields = ['user']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
