from django.contrib.auth.models import User
from django.db import models


class MailConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mail_config")
    email = models.CharField(max_length=255)
    app_password = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.email}"


class StoredEmail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stored_emails")
    sender = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    email_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-email_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.subject}"
