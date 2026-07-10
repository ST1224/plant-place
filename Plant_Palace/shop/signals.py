"""
signals.py — Auto-create UserProfile when a new User is created.

BUGS FIXED:
  1. Removed save_user_profile receiver — it fired on every user.save() call
     (including inside the profile view), causing infinite save loops and
     IntegrityError when called alongside the create receiver.
  2. Using get_or_create (idempotent) so duplicate signal fires are harmless.
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every NEW User. Safe to call multiple times."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
