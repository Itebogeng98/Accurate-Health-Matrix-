from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import CustomUser, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'role']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True,
        required=False,
    )
    role = RoleSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_id',
            'phone_number',
            'is_approved',
            'join_date',
            'password',
            'confirm_password',
        ]
        read_only_fields = ['id', 'role', 'is_approved', 'join_date']

    def validate(self, attrs):
        confirmation = attrs.pop('confirm_password', None)
        if confirmation != attrs['password']:
            raise serializers.ValidationError({'confirm_password': ['Passwords do not match.']})
        user = CustomUser(**{key: value for key, value in attrs.items() if key != 'password'})
        try:
            validate_password(attrs['password'], user=user)
        except ValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_approved',
        ]
