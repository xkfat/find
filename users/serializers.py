from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'passwords must match.'})
        
        return attrs
    

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


    
class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True,validators=[validate_email])
    username = serializers.CharField(required=False)
    profile_photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
           'id', 'username', 'email',
            'first_name', 'last_name',
            'profile_photo', 'phone_number', 'language',
            'theme', 'location_permission',
        ]
        read_only_fields = ['id']

    def validate_username(self, value):
        user = self.context['request'].user
        if value and User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("username is already taken.")
        return value

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("email is already taken.")
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True, required=True)
    new_password     = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2    = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn’t match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',  'phone_number', 'profile_photo', 'language', 'theme', 'location_permission', 'role', ]
        read_only_fields = [ 'id', 'username', 'email',
            'first_name', 'last_name',
            'phone_number', 'profile_photo',
            'language', 'theme', 'location_permission',
           ]
    def update(self, instance, validated_data):
            if 'role' in validated_data:
               instance.role = validated_data.get('role', instance.role)
               instance.save()
            return instance
        
