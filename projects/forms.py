from django import forms
from .models import Project, TextBlock, KanbanTable


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "visibility"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mobile App Redesign"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "What is this project about?"}),
            "visibility": forms.Select(attrs={"class": "form-control"}),
        }


class TextBlockForm(forms.ModelForm):
    class Meta:
        model = TextBlock
        fields = ["content_html"]


class KanbanTableForm(forms.ModelForm):
    class Meta:
        model = KanbanTable
        fields = ["title"]
        widgets = {"title": forms.TextInput(attrs={"class": "form-control"})}
