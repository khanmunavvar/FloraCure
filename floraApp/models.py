from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Diagnosis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plant_name = models.CharField(max_length=100)
    symptoms = models.TextField()
    disease = models.CharField(max_length=100)
    cure = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    plant_image = models.ImageField(upload_to='diagnosis_images/', null=True, blank=True)
    is_cured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.disease}"
