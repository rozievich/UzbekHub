from django.urls import path

from .views import CommentModelAPIView

urlpatterns = [
    path('comment', CommentModelAPIView.as_view(), name="comment_data")
]
