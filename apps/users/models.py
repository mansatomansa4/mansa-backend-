from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

ROLE_CHOICES = [
    ("user", "User"),
    ("admin", "Admin"),
    ("super_admin", "Super Admin"),
    ("mentee", "Mentee"),
    ("mentor", "Mentor"),
    ("mentor_mentee", "Mentor & Mentee"),
]

APPROVAL_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("denied", "Denied"),
]


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    # Extended profile / governance fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default="pending"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_approved = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_users"
    )
    # Mentorship-specific fields
    is_mentor = models.BooleanField(default=False, help_text="User is registered as a mentor")
    is_mentee = models.BooleanField(default=False, help_text="User is registered as a mentee")
    mentor_approved_at = models.DateTimeField(blank=True, null=True, help_text="When mentor application was approved")
    must_change_password = models.BooleanField(
        default=False,
        help_text="True when user was created with default password and must change it"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    DEFAULT_PASSWORD = "Mansa2026!"

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self):
        return self.email

    def can_be_mentor(self):
        """Check if user can act as a mentor (approved mentor status)"""
        return self.is_mentor and self.mentor_approved_at is not None

    def can_be_mentee(self):
        """Check if user can act as a mentee"""
        return self.is_mentee or self.is_active
