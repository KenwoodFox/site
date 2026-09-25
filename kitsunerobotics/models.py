import os

from django.conf import settings
from django.db import models


class SiteSetting(models.Model):
    """
    Site setting can store dedicated simple things. Easier than editing
    a bunch of ENV variables on the host side!
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.key}: {self.value}"


class BlogImage(models.Model):
    """File dropped or pasted into the markdown editor."""

    image = models.FileField(upload_to="blog/uploads/", max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    filename = models.CharField(max_length=255, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename or self.image.name

    def save(self, *args, **kwargs):
        if not self.filename and self.image:
            self.filename = os.path.basename(self.image.name)
        super().save(*args, **kwargs)
        if self.image and (self.size is None or not self.checksum):
            from kitsunerobotics.uploads import file_sha256

            try:
                self.size = self.image.size
            except Exception:
                self.size = self.size or 0
            if not self.checksum:
                try:
                    self.checksum = file_sha256(self.image)
                except Exception:
                    self.checksum = self.checksum or ""
            type(self).objects.filter(pk=self.pk).update(
                size=self.size, checksum=self.checksum
            )

    @property
    def is_image(self):
        from kitsunerobotics.uploads import image_extensions

        name = self.filename or self.image.name
        return os.path.splitext(name)[1].lower() in image_extensions()

    @property
    def markdown_link(self):
        name = self.filename or os.path.basename(self.image.name)
        if self.is_image:
            return f"![{name}]({self.image.url})"
        return f"[{name}]({self.image.url})"
