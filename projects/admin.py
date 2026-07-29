from django.contrib import admin
from .models import Project, ProjectMember, ProjectInvitation, Block, TextBlock, KanbanTable

admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(ProjectInvitation)
admin.site.register(Block)
admin.site.register(TextBlock)
admin.site.register(KanbanTable)
