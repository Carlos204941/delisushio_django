from django.db import models
from django_resized import ResizedImageField
from django.core.validators import MinValueValidator


class Category(models.TextChoices):
    VEGETARIAN = 'VEG', 'Vegetarian'
    RAW_FISH = 'RAW', 'Raw Fish'
    COOKED_FISH = 'COOKED', 'Cooked Fish'
    POKE_BOWL = 'POKE', 'Poke Bowl'
    HARUMAKI = 'HARU', 'Harumaki'


class SpiceLevel(models.IntegerChoices):
    NONE = 0, 'No Spice'
    MILD = 1, 'Mild'
    MEDIUM = 2, 'Medium'
    HOT = 3, 'Hot'


class Product(models.Model):
    id_product = models.AutoField(primary_key=True)
    category = models.CharField(max_length=10, choices=Category.choices)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    # Automatic resizing using django-resized
    image = ResizedImageField(
        size=[800, 800], crop='middle', quality=85,
        upload_to='products/', blank=True, null=True
    )

    is_available = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    spice_level = models.IntegerField(choices=SpiceLevel.choices, default=SpiceLevel.NONE)

    # Store allergens as a JSON list or comma separated string
    allergens = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
