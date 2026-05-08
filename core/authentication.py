import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User


def generate_tokens(user):
    now = datetime.now(tz=timezone.utc)
    access_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "exp": now + timedelta(hours=settings.JWT_ACCESS_EXPIRY_HOURS),
        "iat": now,
        "type": "access",
    }
    refresh_payload = {
        "user_id": user.id,
        "exp": now + timedelta(days=settings.JWT_REFRESH_EXPIRY_DAYS),
        "iat": now,
        "type": "refresh",
    }
    access  = jwt.encode(access_payload,  settings.JWT_SECRET, algorithm="HS256")
    refresh = jwt.encode(refresh_payload, settings.JWT_SECRET, algorithm="HS256")
    return {"access": access, "refresh": refresh}


def decode_token(token, expected_type="access"):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise AuthenticationFailed("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        try:
            user = User.objects.get(id=payload["user_id"], is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")
        return (user, token)
