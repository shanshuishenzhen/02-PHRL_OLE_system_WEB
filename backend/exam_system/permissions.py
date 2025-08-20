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
        # The 'is_marker' property is not on the default user model.
        # This will rely on it being added later if needed.
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_marker', False))


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
        # Admins can access any user object
        if request.user.is_admin:
            return True

        # Users can only access their own info
        if hasattr(obj, 'user'): # for objects that have a user foreign key
            return obj.user.id == request.user.id
        return obj.id == request.user.id