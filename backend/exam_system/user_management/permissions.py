from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """只允许管理员访问"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsTeacherUser(permissions.BasePermission):
    """只允许教师访问"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_teacher)


class IsStudentUser(permissions.BasePermission):
    """只允许学生访问"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsMarkerUser(permissions.BasePermission):
    """只允许阅卷员访问"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_marker)


class IsAdminOrTeacherUser(permissions.BasePermission):
    """只允许管理员或教师访问"""
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_teacher)
        )


class IsSelfOrAdmin(permissions.BasePermission):
    """只允许用户自己或管理员访问"""
    
    def has_object_permission(self, request, view, obj):
        # 管理员可以访问任何用户
        if request.user.is_admin:
            return True
            
        # 用户只能访问自己的信息
        return obj.id == request.user.id
