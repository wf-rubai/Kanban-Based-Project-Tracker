from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Extends Django's built-in auth user with an avatar
    placeholder color/initials (since no custom icons/images are required)
    and a short display role used across the UI.
    """
    email = models.EmailField(unique=True)
    avatar_color = models.CharField(
        max_length=7,
        default="#2F81F7",
        help_text="Hex color used to render this user's placeholder avatar.",
    )
    bio = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def initials(self):
        base = (self.get_full_name() or self.username or "?").strip()
        parts = [p for p in base.split(" ") if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return base[:2].upper()

    def __str__(self):
        return self.username
