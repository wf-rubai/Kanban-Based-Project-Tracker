from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_manager, name="project_manager"),
    path("new/form/", views.new_project_form, name="new_project_form"),
    path("create/", views.create_project, name="create_project"),
    path("<int:pk>/delete/", views.delete_project, name="delete_project"),

    path("<int:project_id>/blocks/create/", views.create_block, name="create_block"),
    path("<int:project_id>/blocks/<int:block_id>/move/", views.move_block, name="move_block"),
    path("<int:project_id>/blocks/<int:block_id>/delete/", views.delete_block, name="delete_block"),
    path("<int:project_id>/blocks/<int:block_id>/duplicate/", views.duplicate_block, name="duplicate_block"),
    path("<int:project_id>/blocks/<int:block_id>/collapse/", views.toggle_collapse, name="toggle_collapse"),
    path("<int:project_id>/blocks/<int:block_id>/text/save/", views.save_text_block, name="save_text_block"),
    path("<int:project_id>/blocks/<int:block_id>/table/view/", views.set_table_view, name="set_table_view"),

    path("<int:project_id>/members/", views.member_window, name="member_window"),
    path("<int:project_id>/members/search/", views.search_users, name="search_users"),
    path("<int:project_id>/members/add/", views.add_member, name="add_member"),
    path("<int:project_id>/members/remove/", views.remove_member, name="remove_member"),
]
