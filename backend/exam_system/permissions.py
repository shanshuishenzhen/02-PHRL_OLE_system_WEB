# 导出权限类
from exam_system.user_management.permissions import (
    IsAdminUser, IsTeacherUser, IsStudentUser, IsMarkerUser,
    IsAdminOrTeacherUser, IsSelfOrAdmin
)

# 导出common中的权限类
from exam_system.common.permissions import IsTeacherOrAdmin, IsStudent