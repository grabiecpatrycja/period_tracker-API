from django.db.models import Subquery, OuterRef, Avg, F, ExpressionWrapper, IntegerField, DateField, When, Case, Value
from django.db.models.functions import Round, TruncDate
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from tracker.serializers import *
from datetime import timedelta


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email=serializer.validated_data['email']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PeriodViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer

    def get_queryset(self):

        previous_period = Subquery(
            Period.objects.filter(user=OuterRef('user'), first_day__lt=OuterRef('first_day'))
                .order_by('-first_day')
                .values('first_day')[:1]
            )
        
        cycles = (Period.objects.filter(user=self.request.user)
                .order_by('first_day')
                .annotate(length=ExpressionWrapper(
                    (F('first_day') - previous_period)/timedelta(days=1),
                    output_field=IntegerField()
                ))
                .annotate(ovul_len=Case(
                    When(ovulation_day__isnull=True, then=Value(None)),
                    default=ExpressionWrapper(                            
                        ((F('ovulation_day')-F('first_day'))/timedelta(days=1))+1,
                        output_field=IntegerField())
                ))
            )

        return cycles

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["GET"], serializer_class=PeriodSerializer)
    def last(self, request):
        last_period = Period.objects.filter(user=request.user).order_by('-first_day').first()
        
        if last_period:
            serializer = PeriodSerializer(last_period)

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(status=status.HTTP_404_NOT_FOUND)
    
class StatisticView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user_periods = Period.objects.filter(user=request.user)

        if not user_periods.exists() or user_periods.count() < 2:
            return Response(
                {'message': 'Add more data to perform calculations.'},
                status=status.HTTP_400_BAD_REQUEST)

        previous_period = Subquery(
            Period.objects.filter(user=OuterRef('user'), first_day__lt=OuterRef('first_day'))
            .order_by('-first_day')
            .values('first_day')[:1])
        
        averages = (Period.objects.filter(user=self.request.user)
                .order_by('first_day')
                .annotate(length=ExpressionWrapper(
                    (F('first_day') - previous_period)/timedelta(days=1),
                    output_field=IntegerField()
                ))
                .annotate(ovul_length=Case(
                        When(ovulation_day__isnull=True, then=Value(14)),
                        default=ExpressionWrapper(
                            ((F('ovulation_day')-F('first_day'))/timedelta(days=1))+1,
                            output_field=IntegerField())
                ))
                .aggregate(avg_length=Round(Avg(F'length')), avg_ovulation=Round(Avg(F'ovul_length')))
            )
        
        predictions = (Period.objects.filter(user=self.request.user)
                       .order_by('-first_day')
                       .annotate(day=ExpressionWrapper(
                           (TruncDate(timezone.now())-F('first_day'))/timedelta(days=1)+1,
                           output_field=IntegerField()
                       ))
                       .annotate(next_period=ExpressionWrapper(
                            F('first_day') + timedelta(days=averages['avg_length']),
                            output_field=DateField()
                        ))
                        .annotate(days_to_next=ExpressionWrapper(
                            (F('next_period')-TruncDate(timezone.now()))/timedelta(days=1),
                            output_field=IntegerField()
                        ))
                        .annotate(next_ovulation=Case(
                            When(ovulation_day__isnull = False, then=None),
                            default=ExpressionWrapper(
                                F('first_day') + timedelta(days=averages['avg_ovulation']),
                                output_field=DateField())
                        ))
                        .annotate(days_to_ovul_raw=ExpressionWrapper(
                                (F('next_ovulation')-TruncDate(timezone.now()))/timedelta(days=1),
                                output_field=IntegerField()
                                ),
                                days_to_ovul=Case(
                                    When(days_to_ovul_raw__lt=0, then=Value(None)),
                                    default=F('days_to_ovul_raw'),
                                    output_field=IntegerField()
                        ))
                       .values('day', 'next_period', 'days_to_next', 'next_ovulation', 'days_to_ovul')
                       .first()
        )
        
        result = {
            'averages': averages,
            'predictions': predictions
        }

        return Response(result)
    