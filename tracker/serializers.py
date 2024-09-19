from rest_framework import serializers
from django.contrib.auth.models import User
from tracker.models import Period

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class PeriodSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Period
        fields = '__all__'

    def validate(self, data):

        instance = getattr(self, 'instance', None)

        first_day = data.get('first_day', getattr(instance, 'first_day', None))
        ovulation_day = data.get('ovulation_day', None)

        if ovulation_day and first_day and ovulation_day <= first_day:
            raise serializers.ValidationError
        
        return data
    