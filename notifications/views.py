from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import CommentModelSerializer
from .models import Comment
# Create your views here.


class CommentModelAPIView(APIView):
    queryset = Comment.objects.all()
    serializer_class = CommentModelSerializer
    permission_classes = (AllowAny, )

    def get(self, request, *args, **kwargs):
        comments = self.queryset.all()
        serializer = self.serializer_class(comments, many=True)
        return Response(serializer.data, status=200)
    
    @swagger_auto_schema(request_body=CommentModelSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    