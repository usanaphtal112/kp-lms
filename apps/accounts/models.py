from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    IT_ADMIN = "IT_ADMIN", "IT Administrator"
    LECTURER = "LECTURER", "Lecturer"
    LAB_COORDINATOR = "LAB_COORDINATOR", "Skills Lab Coordinator"
    ADMINISTRATION = "ADMINISTRATION", "Administration"
    STUDENT = "STUDENT", "Student"


class User(AbstractUser):
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
    )
    phone_number = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["username"]),
        ]

    def is_student(self):
        return self.role == UserRole.STUDENT

    def is_lecturer(self):
        return self.role == UserRole.LECTURER

    def is_it_admin(self):
        return self.role == UserRole.IT_ADMIN
    
class StudentType(models.TextChoices):
    REGULAR = "REGULAR", "Regular"
    UPGRADING = "UPGRADING", "Upgrading"
    CREDIT_TRANSFER = "CREDIT_TRANSFER", "Credit Transfer"
    CONTINUING = "CONTINUING", "Continuing"


# class StudentProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="student_profile",
#     )
#     registration_number = models.CharField(max_length=50, unique=True)
#     student_type = models.CharField(
#         max_length=30,
#         choices=StudentType.choices,
#         default=StudentType.REGULAR,
#     )
#     program = models.ForeignKey(
#         "academics.Program",
#         on_delete=models.PROTECT,
#         related_name="students",
#     )
#     cohort = models.ForeignKey(
#         "academics.Cohort",
#         on_delete=models.PROTECT,
#         related_name="students",
#     )
#     is_active_student = models.BooleanField(default=True)

#     def __str__(self):
#         return self.registration_number


# class StaffProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="staff_profile",
#     )
#     staff_number = models.CharField(max_length=50, unique=True, blank=True)
#     department = models.ForeignKey(
#         "academics.Department",
#         on_delete=models.PROTECT,
#         related_name="staff_members",
#         null=True,
#         blank=True,
#     )
#     job_title = models.CharField(max_length=120, blank=True)

#     def __str__(self):
#         return self.user.get_full_name() or self.user.username