from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .authentication import generate_tokens, decode_token
from .models import User
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, ChangePasswordSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    tokens = generate_tokens(user)
    return Response({"user": UserSerializer(user).data, **tokens}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(request, username=serializer.validated_data["email"],
                        password=serializer.validated_data["password"])
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    tokens = generate_tokens(user)
    return Response({"user": UserSerializer(user).data, **tokens})


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    token = request.data.get("refresh")
    if not token:
        return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
    payload = decode_token(token, expected_type="refresh")
    try:
        user = User.objects.get(id=payload["user_id"], is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    tokens = generate_tokens(user)
    return Response(tokens)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "GET":
        return Response(UserSerializer(request.user).data)
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not request.user.check_password(serializer.validated_data["old_password"]):
        return Response({"detail": "Old password incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save()
    return Response({"detail": "Password updated."})
