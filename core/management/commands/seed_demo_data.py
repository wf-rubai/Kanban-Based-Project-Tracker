"""
Management command that populates the database with realistic sample data:
2 users, 1 project (with a text block + kanban table block), 5 stories
spread across different statuses, a couple of comments, and a generated
AI summary. Safe to re-run (uses get_or_create where appropriate).

Usage:
    python manage.py seed_demo_data
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from comments.models import Comment
from projects.models import Block, KanbanTable, Project, ProjectMember, TextBlock
from stories.models import Story
from stories.services import record_status_change, recalculate_priorities

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo users, a project, blocks, stories, and comments."

    def handle(self, *args, **options):
        alice, _ = User.objects.get_or_create(
            username="alice",
            defaults={"email": "alice@example.com", "first_name": "Alice", "avatar_color": "#2F81F7"},
        )
        alice.set_password("password123")
        alice.save()

        bob, _ = User.objects.get_or_create(
            username="bob",
            defaults={"email": "bob@example.com", "first_name": "Bob", "avatar_color": "#3FB950"},
        )
        bob.set_password("password123")
        bob.save()

        project, created = Project.objects.get_or_create(
            name="Mobile App Redesign",
            owner=alice,
            defaults={"description": "Redesigning the onboarding and dashboard flows.", "visibility": "private"},
        )
        ProjectMember.objects.get_or_create(project=project, user=bob, defaults={"role": "member"})

        if created or not project.blocks.exists():
            text_block = Block.objects.create(project=project, block_type="text", order=0, created_by=alice)
            TextBlock.objects.create(
                block=text_block,
                content_html="<h2>Project Notes</h2><p>This is the first sprint of the redesign. "
                              "Goals: simplify onboarding, ship a new dashboard.</p>"
                              "<ul><li>Design review Friday</li><li>Dev handoff Monday</li></ul>",
            )

            table_block = Block.objects.create(project=project, block_type="table", order=1, created_by=alice)
            table = KanbanTable.objects.create(block=table_block, title="Sprint 1 Board", view_mode="row")

            demo_stories = [
                ("Design onboarding screens", "Figma mockups for 5 screens", "very_high", "done"),
                ("Implement auth API", "JWT-based login/register", "high", "in_progress"),
                ("Dashboard chart widget", "Recharts-based summary chart", "medium", "testing"),
                ("Push notification setup", "FCM integration", "low", "backlog"),
                ("Accessibility audit", "WCAG AA pass on new screens", "very_low", "backlog"),
            ]
            for name, note, importance, status in demo_stories:
                story = Story.objects.create(
                    kanban_table=table,
                    name=name,
                    short_note=note,
                    description=f"Detailed description for '{name}'.",
                    importance=importance,
                    created_by=alice,
                )
                story.status_history.get_or_create(status="backlog", defaults={"entered_at": timezone.now()})
                if status != "backlog":
                    record_status_change(story, status, actor=alice)

            recalculate_priorities(table)

            first_story = table.stories.first()
            if first_story:
                Comment.objects.create(story=first_story, author=bob, body="Looks great, ready for dev handoff.")
                Comment.objects.create(story=first_story, author=alice, body="Thanks! Moving to Done.")

        self.stdout.write(self.style.SUCCESS(
            "Seed complete. Login as alice/password123 (owner) or bob/password123 (member)."
        ))
