from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from tracker.views import *


urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('token', TokenObtainPairView.as_view(), name='token')
]
