from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth.models import User
from tracker.serializers import *


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email=serializer.validated_data['email']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)