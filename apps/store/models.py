from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()


class StoreItem(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("sold_out", "Sold Out"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True)  # Rendered HTML version
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    featured_image = models.ImageField(upload_to="store/", blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    stock_quantity = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    in_stock = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Set published_at when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:item_detail", kwargs={"slug": self.slug})

    @property
    def is_available(self):
        """Check if item is available for purchase"""
        if self.status != "published":
            return False
        if not self.in_stock:
            return False
        if self.stock_quantity > 0 and self.stock_quantity == 0:
            return False
        return True


class StoreImage(models.Model):
    """Additional images for store items"""

    item = models.ForeignKey(StoreItem, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="store/")
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.item.title} - Image {self.order}"
