from django.conf import settings
from django.db import models
from django.urls import reverse


class Project(models.Model):
    VISIBILITY_CHOICES = [("private", "Private"), ("public", "Public")]

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="private")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner"]), models.Index(fields=["visibility"])]

    def __str__(self):
        return self.name

    def member_count(self):
        return self.memberships.count()

    def is_owner(self, user):
        return self.owner_id == user.id

    def is_member(self, user):
        return self.memberships.filter(user=user).exists()


class ProjectMember(models.Model):
    ROLE_CHOICES = [("owner", "Owner"), ("member", "Member")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
        ordering = ["-role", "joined_at"]

    def __str__(self):
        return f"{self.user} @ {self.project} ({self.role})"


class ProjectInvitation(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("accepted", "Accepted"), ("declined", "Declined")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invitations")
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations_received"
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations_sent"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "invited_user")


class Block(models.Model):
    """
    A Block is one vertical unit in the Colab-style Center Panel. It can be
    either a TextBlock or a KanbanTable (see the one-to-one models below).
    """
    BLOCK_TYPES = [("text", "Text Block"), ("table", "Kanban Table Block")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=10, choices=BLOCK_TYPES)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_blocks"
    )
    is_collapsed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["project", "order"])]

    def __str__(self):
        return f"{self.get_block_type_display()} #{self.pk} in {self.project}"


class TextBlock(models.Model):
    block = models.OneToOneField(Block, on_delete=models.CASCADE, related_name="text_block")
    content_html = models.TextField(blank=True, default="")

    def __str__(self):
        return f"TextBlock({self.block_id})"


class KanbanTable(models.Model):
    VIEW_CHOICES = [("row", "Row View"), ("column", "Column View")]

    block = models.OneToOneField(Block, on_delete=models.CASCADE, related_name="kanban_table")
    title = models.CharField(max_length=120, default="Sprint Board")
    view_mode = models.CharField(max_length=10, choices=VIEW_CHOICES, default="row")

    def __str__(self):
        return self.title
