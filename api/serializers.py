from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class AccessContextQuerySerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    product = serializers.SlugField(max_length=64)
