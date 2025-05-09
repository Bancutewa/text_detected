from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class DetectionResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    original_text = models.TextField()
    translated_text = models.TextField(null=True, blank=True)
    confidence_score = models.FloatField()
    image = models.ImageField(upload_to='detection_results/', null=True, blank=True)
    image_path = models.CharField(max_length=255, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    translation_direction = models.CharField(max_length=10, choices=[
        ('vi_to_en', 'Vietnamese to English'),
        ('en_to_vi', 'English to Vietnamese'),
    ], null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def get_image_url(self):
        if self.image:
            return self.image.url
        return None

class CombinedTranslation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    original_paragraph = models.TextField()
    translated_paragraph = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    translation_direction = models.CharField(max_length=10, choices=[
        ('vi_to_en', 'Vietnamese to English'),
        ('en_to_vi', 'English to Vietnamese'),
    ])

    class Meta:
        ordering = ['-created_at']
