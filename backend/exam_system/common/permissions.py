from rest_framework import permissions


class IsTeacherOrAdmin(permissions.BasePermission):
    """只允许教师或管理员访问"""
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_teacher)
        )


class IsStudent(permissions.BasePermission):
    """只允许学生访问"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)