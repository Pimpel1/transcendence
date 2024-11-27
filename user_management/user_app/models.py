from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a new user."""
        if not email:
            raise ValueError('Users must have an email address.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model."""
    email = models.EmailField(max_length=255, unique=True, default='None')
    username = models.CharField(max_length=255,
                                unique=True,
                                null=False,
                                blank=False
                                )
    displayname = models.CharField(max_length=255,
                                   default='Anonymous', unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'displayname']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Profile model extending the user model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/',
                               null=True,
                               blank=True,
                               default='avatars/default.png')
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    wannabe_friends = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='wannabe_requests',
        blank=True
        )
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    language = models.CharField(max_length=2, default='en')

    def __str__(self):
        return self.user.email
