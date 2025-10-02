from django.db import models

# Create your models here.
class Comment(models.Model):
    full_name = models.CharField(max_length=20, blank=True, null=True)
    text = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text
    
