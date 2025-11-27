import jwt
import datetime
from uuid import uuid4

from django.conf import settings


def get_jwt(user):
    print('jwt created')

    payload = {
        'sub': str(user.id),
        'aud': settings.ALLOWED_HOSTS,
        'iss': settings.APP_ID,
        'exp': datetime.datetime.utcnow() + settings.ACCESS_TOKEN_EXPIRED_TIME,
        'iat': datetime.datetime.utcnow(),
    }

    secret_key = settings.SECRET_KEY
    algorithm = 'HS256'
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def decode_jwt(token, audience):
    secret_key = settings.SECRET_KEY
    algorithm = 'HS256'
    return jwt.decode(token, secret_key, algorithms=[algorithm], audience=audience, issuer=settings.APP_ID)


def get_refresh_jwt(user):
    print('refresh created')
    payload = {
        'sub': str(user.id),
        'aud': settings.ALLOWED_HOSTS,
        'iss': settings.APP_ID,
        'exp': datetime.datetime.utcnow() + settings.REFRESH_TOKEN_EXPIRED_TIME,
        'iat': datetime.datetime.utcnow(),
        'jti': str(uuid4()),
    }

    secret_key = settings.SECRET_KEY
    algorithm = 'HS256'
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token

