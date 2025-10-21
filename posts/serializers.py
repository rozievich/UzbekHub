from rest_framework import serializers
from django.utils import timezone

from .models import Post, PostImages, PostLikes, PostComment, PostViews


# Post Image Serializer
class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImages
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']


# Post Like Serializer
class PostLikeSerializer(serializers.ModelSerializer):
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PostLikes
        fields = ['id', 'owner', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        post = attrs.get('post')

        if PostLikes.objects.filter(owner=user, post=post).exists():
            raise serializers.ValidationError("You have already liked this post.")
        
        return attrs

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['owner'] = {
            "id": instance.owner.id,
            "username": instance.owner.username,
            "full_name": instance.owner.get_full_name(),
            "profile_picture": request.build_absolute_uri(instance.owner.profile_picture.url) if instance.owner.profile_picture else None
        }
        return representation


# Post Comment Serializer
class PostCommentSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = PostComment
        fields = ['id', 'owner', 'post', 'comment', 'reply_to', 'is_edited', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_edited', 'created_at', 'updated_at']

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['owner'] = {
            "id": instance.owner.id,
            "username": instance.owner.username,
            "full_name": instance.owner.get_full_name(),
            "profile_picture": request.build_absolute_uri(instance.owner.profile_picture.url) if instance.owner.profile_picture else None
        }
        return representation

    def update(self, instance, validated_data):
        instance.comment = validated_data.get('comment', instance.comment)
        instance.is_edited = True
        instance.updated_at = timezone.now()
        instance.save()
        return instance


# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, required=False)
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Post
        fields = ['id', 'content', 'owner', 'images', 'is_active', 'is_edited', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'is_active', 'is_edited', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        images_data = request.FILES.getlist('images') if request else []

        post = Post.objects.create(**validated_data)
        for image_data in images_data:
            PostImages.objects.create(post=post, image=image_data)
        return post


    def update(self, instance, validated_data):
        request = self.context.get('request')
        images_data = request.FILES.getlist('images') if request else []

        instance.content = validated_data.get('content', instance.content)
        instance.is_edited = True
        instance.updated_at = timezone.now()
        post = instance.save()
        for image_data in images_data:
            PostImages.objects.update_or_create(post=post, image=image_data)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['like_count'] = instance.like_count
        representation['comment_count'] = instance.comment_count
        representation['view_count'] = instance.view_count
        return representation

