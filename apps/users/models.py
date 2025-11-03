from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )

    # Content
    bio = models.TextField("User Bio", blank=True, null=True)

    # Roles/flags
    is_verified = models.BooleanField(default=False)  # Only i add this one

    # Badges! (Not really implemented yet but~)
    badges = models.JSONField(default=list, blank=True)

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    def get_profile_picture_url(self):
        """
        Just because some ppl dont set theirs and I always wanna draw something valid
        for their PFP (even if its just a placeholder).
        """

        try:
            if self.profile_picture and self.profile_picture.name:
                return self.profile_picture.url
        except (ValueError, AttributeError):
            pass
        return None

    def __str__(self):
        return self.username
