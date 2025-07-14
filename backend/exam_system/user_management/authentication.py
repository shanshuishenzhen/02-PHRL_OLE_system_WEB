import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """JWT认证类"""
    
    def authenticate(self, request):
        # 从请求头中获取JWT令牌
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
            
        try:
            # 提取令牌
            auth_parts = auth_header.split()
            if auth_parts[0].lower() != 'bearer':
                return None
            if len(auth_parts) == 1:
                raise ParseError('无效的令牌头')
            elif len(auth_parts) > 2:
                raise ParseError('无效的令牌格式')
                
            token = auth_parts[1]
            
            # 解码令牌
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 检查令牌是否过期
            token_exp = datetime.fromtimestamp(payload['exp'])
            if token_exp < datetime.now():
                raise AuthenticationFailed('令牌已过期')
                
            # 获取用户
            user_id = payload['user_id']
            user = User.objects.filter(id=user_id).first()
            if user is None:
                raise AuthenticationFailed('用户不存在')
            if not user.is_active:
                raise AuthenticationFailed('用户已被禁用')
                
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('令牌已过期')
        except jwt.DecodeError:
            raise AuthenticationFailed('令牌无效')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('无效的令牌')
    
    @staticmethod
    def generate_token(user):
        """生成JWT令牌"""
        access_token_expiry = datetime.now() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)
        refresh_token_expiry = datetime.now() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        
        access_payload = {
            'token_type': 'access',
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': int(access_token_expiry.timestamp()),
            'iat': int(datetime.now().timestamp())
        }
        
        refresh_payload = {
            'token_type': 'refresh',
            'user_id': user.id,
            'exp': int(refresh_token_expiry.timestamp()),
            'iat': int(datetime.now().timestamp())
        }
        
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return {
            'access': access_token,
            'refresh': refresh_token,
            'access_expires': int(access_token_expiry.timestamp()),
            'refresh_expires': int(refresh_token_expiry.timestamp())
        }
    
    @staticmethod
    def refresh_token(refresh_token):
        """刷新令牌"""
        try:
            # 解码刷新令牌
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 检查令牌类型
            if payload.get('token_type') != 'refresh':
                raise AuthenticationFailed('无效的刷新令牌')
                
            # 获取用户
            user_id = payload['user_id']
            user = User.objects.filter(id=user_id).first()
            if user is None:
                raise AuthenticationFailed('用户不存在')
            if not user.is_active:
                raise AuthenticationFailed('用户已被禁用')
                
            # 生成新的访问令牌
            access_token_expiry = datetime.now() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)
            
            access_payload = {
                'token_type': 'access',
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': int(access_token_expiry.timestamp()),
                'iat': int(datetime.now().timestamp())
            }
            
            access_token = jwt.encode(
                access_payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            return {
                'access': access_token,
                'access_expires': int(access_token_expiry.timestamp())
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('刷新令牌已过期')
        except jwt.DecodeError:
            raise AuthenticationFailed('刷新令牌无效')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('无效的刷新令牌')
