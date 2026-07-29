from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Project, ProjectMember


@receiver(post_save, sender=Project)
def create_owner_membership(sender, instance, created, **kwargs):
    """Whenever a Project is created, automatically add the owner as a member with role=owner."""
    if created:
        ProjectMember.objects.get_or_create(
            project=instance, user=instance.owner, defaults={"role": "owner"}
        )
