from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from core.utils import json_ok, json_error, parse_json_body
from stories.models import Story, STATUS_CHOICES
from summarizer.models import ProjectSummaryCache

from .forms import ProjectForm, KanbanTableForm
from .models import Block, KanbanTable, Project, ProjectMember, TextBlock

User = get_user_model()


# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------
def _member_projects(user):
    return Project.objects.filter(memberships__user=user).distinct()


def require_membership(view_func):
    """Ensure the requesting user belongs to the project referenced by project_id/pk kwarg."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        project_id = kwargs.get("project_id") or kwargs.get("pk")
        project = get_object_or_404(Project, pk=project_id)
        if not project.is_member(request.user):
            return json_error("You are not a member of this project.", status=403)
        return view_func(request, *args, project=project, **kwargs)
    return wrapper


def require_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        project_id = kwargs.get("project_id") or kwargs.get("pk")
        project = get_object_or_404(Project, pk=project_id)
        if not project.is_owner(request.user):
            return json_error("Only the project owner can do this.", status=403)
        return view_func(request, *args, project=project, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
@login_required
def project_manager(request):
    owned = Project.objects.filter(owner=request.user)
    joined = _member_projects(request.user).exclude(owner=request.user)

    selected_id = request.GET.get("project")
    selected = None
    if selected_id:
        selected = _member_projects(request.user).filter(pk=selected_id).first()
    if selected is None:
        selected = owned.first() or joined.first()

    context = {
        "owned_projects": owned,
        "joined_projects": joined,
        "selected_project": selected,
    }
    context["status_choices"] = STATUS_CHOICES
    if selected:
        context["blocks"] = selected.blocks.select_related("text_block", "kanban_table").prefetch_related(
            "kanban_table__stories__status_history", "kanban_table__stories__badges"
        )
        context["members"] = selected.memberships.select_related("user")
    return render(request, "projects/project_manager.html", context)


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------
@login_required
def new_project_form(request):
    form = ProjectForm()
    html = render_to_string("projects/partials/create_project_form.html", {"form": form}, request=request)
    return json_ok({"html": html})


@login_required
def create_project(request):
    if request.method != "POST":
        return json_error("Invalid method", status=405)
    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, f'Project "{project.name}" created.')
        return json_ok({"redirect": f"/projects/?project={project.id}"})
    html = render_to_string("projects/partials/create_project_form.html", {"form": form}, request=request)
    return json_error("Please fix the errors below.", html=html)


@login_required
@require_owner
def delete_project(request, project):
    if request.method != "POST":
        return json_error("Invalid method", status=405)
    name = project.name
    project.delete()
    messages.success(request, f'Project "{name}" was deleted.')
    return json_ok({"redirect": "/projects/"})


# ---------------------------------------------------------------------------
# Blocks (Center Panel)
# ---------------------------------------------------------------------------
def _center_panel_html(request, project):
    blocks = project.blocks.select_related("text_block", "kanban_table").prefetch_related(
        "kanban_table__stories__status_history", "kanban_table__stories__badges"
    )
    return render_to_string(
        "projects/partials/center_panel.html",
        {"selected_project": project, "blocks": blocks, "status_choices": STATUS_CHOICES},
        request=request,
    )


@login_required
@require_membership
def create_block(request, project, project_id=None):
    if request.method != "POST":
        return json_error("Invalid method", status=405)
    block_type = request.POST.get("block_type")
    if block_type not in ("text", "table"):
        return json_error("Unknown block type.")

    with transaction.atomic():
        max_order = project.blocks.count()
        block = Block.objects.create(
            project=project, block_type=block_type, order=max_order, created_by=request.user
        )
        if block_type == "text":
            TextBlock.objects.create(block=block, content_html="")
        else:
            KanbanTable.objects.create(block=block, title="New Sprint Board")

    return json_ok({"html": _center_panel_html(request, project)})


@login_required
@require_membership
def move_block(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project)
    direction = request.POST.get("direction")
    siblings = list(project.blocks.order_by("order", "id"))
    idx = siblings.index(block)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(siblings):
        other = siblings[swap_idx]
        block.order, other.order = other.order, block.order
        block.save(update_fields=["order"])
        other.save(update_fields=["order"])
    return json_ok({"html": _center_panel_html(request, project)})


@login_required
@require_membership
def delete_block(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project)
    block.delete()
    return json_ok({"html": _center_panel_html(request, project)})


@login_required
@require_membership
def duplicate_block(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project)
    with transaction.atomic():
        new_block = Block.objects.create(
            project=project,
            block_type=block.block_type,
            order=project.blocks.count(),
            created_by=request.user,
        )
        if block.block_type == "text":
            TextBlock.objects.create(block=new_block, content_html=block.text_block.content_html)
        else:
            KanbanTable.objects.create(
                block=new_block, title=f"{block.kanban_table.title} (copy)", view_mode=block.kanban_table.view_mode
            )
    return json_ok({"html": _center_panel_html(request, project)})


@login_required
@require_membership
def toggle_collapse(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project)
    block.is_collapsed = not block.is_collapsed
    block.save(update_fields=["is_collapsed"])
    return json_ok({"html": _center_panel_html(request, project)})


@login_required
@require_membership
def save_text_block(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project, block_type="text")
    payload = parse_json_body(request)
    content = payload.get("content_html", "")
    block.text_block.content_html = content
    block.text_block.save(update_fields=["content_html"])
    return json_ok({"saved_at": block.updated_at.isoformat()})


@login_required
@require_membership
def set_table_view(request, project, block_id, project_id=None):
    block = get_object_or_404(Block, pk=block_id, project=project, block_type="table")
    payload = parse_json_body(request)
    mode = payload.get("view_mode")
    if mode not in ("row", "column"):
        return json_error("Invalid view mode.")
    block.kanban_table.view_mode = mode
    block.kanban_table.save(update_fields=["view_mode"])
    return json_ok({"html": _center_panel_html(request, project)})


# ---------------------------------------------------------------------------
# Member window (Right Panel default state)
# ---------------------------------------------------------------------------
@login_required
@require_membership
def member_window(request, project, project_id=None):
    members = project.memberships.select_related("user")
    html = render_to_string(
        "projects/partials/member_window.html",
        {"selected_project": project, "members": members},
        request=request,
    )
    return json_ok({"html": html})


@login_required
@require_owner
def search_users(request, project, project_id=None):
    q = request.GET.get("q", "").strip()
    results = []
    if q:
        existing_ids = project.memberships.values_list("user_id", flat=True)
        results = User.objects.filter(username__icontains=q).exclude(pk__in=existing_ids)[:8]
    html = render_to_string(
        "projects/partials/member_search_results.html", {"results": results, "selected_project": project},
        request=request,
    )
    return json_ok({"html": html})


@login_required
@require_owner
def add_member(request, project, project_id=None):
    if request.method != "POST":
        return json_error("Invalid method", status=405)
    payload = parse_json_body(request)
    user_id = payload.get("user_id")
    target = get_object_or_404(User, pk=user_id)
    ProjectMember.objects.get_or_create(project=project, user=target, defaults={"role": "member"})
    members = project.memberships.select_related("user")
    html = render_to_string(
        "projects/partials/member_window.html", {"selected_project": project, "members": members}, request=request
    )
    return json_ok({"html": html})


@login_required
@require_owner
def remove_member(request, project, project_id=None):
    if request.method != "POST":
        return json_error("Invalid method", status=405)
    payload = parse_json_body(request)
    user_id = payload.get("user_id")
    if str(user_id) == str(project.owner_id):
        return json_error("The owner cannot be removed from the project.")
    ProjectMember.objects.filter(project=project, user_id=user_id).delete()
    members = project.memberships.select_related("user")
    html = render_to_string(
        "projects/partials/member_window.html", {"selected_project": project, "members": members}, request=request
    )
    return json_ok({"html": html})
