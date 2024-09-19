from rest_framework.routers import DefaultRouter
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from tracker.views import *

router = DefaultRouter()
router.register(r'period', PeriodViewSet, basename='period')

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('token', TokenObtainPairView.as_view(), name='token')
]

urlpatterns += router.urls