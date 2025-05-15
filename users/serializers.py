from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')
    email = serializers.EmailField(required=True, validators=[validate_email])
    phone_number = serializers.CharField(required=True, max_length=15)
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password', 'password2']
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
    """
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with that phone number already exists.")
        return value
    """
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value
    
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
    username = serializers.CharField(required=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=True, max_length=15)
    theme = serializers.ChoiceField(
        choices=User.THEME_CHOICES,
        default=User.THEME_LIGHT
    )
    language = serializers.ChoiceField(
        choices=User.LANGUAGE_CHOICES,
        default=User.LANGUAGE_ENGLISH
    )
    location_permission = serializers.BooleanField()

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
        if User.objects.exclude(pk=user.pk).filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists():
            raise serializers.ValidationError("email is already taken.")
        return value
    
    """ 
     def validate_phone_number(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number is already taken.")
        return value
    """
class ChangePasswordSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True, required=True)
    new_password     = serializers.CharField(write_only=True, required=True, validators=[validate_password], label ='New password')
    new_password2    = serializers.CharField(write_only=True, required=True, label ='Confirm new password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn’t match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

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
        
