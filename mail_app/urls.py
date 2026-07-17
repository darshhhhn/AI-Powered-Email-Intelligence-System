from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from . import views
from .forms import UsernameAuthenticationForm

app_name = "mail_app"

urlpatterns = [
    path(
        "",
        auth_views.LoginView.as_view(
            template_name="mail_app/login.html",
            redirect_authenticated_user=False,
            success_url=reverse_lazy("mail_app:dashboard"),
            authentication_form=UsernameAuthenticationForm,
        ),
        name="login",
    ),

    path("settings/", views.settings_view, name="settings"),
    path("sync-mails/", views.sync_mails_view, name="sync_mails"),
    path("inbox/", views.dashboard_view, name="dashboard"),
    path("analyze/", views.analyze_view, name="analyze"),
    path("search-suggestions/", views.search_suggestions_view, name="search_suggestions"),
    path("search/", views.search_view, name="search"),
    path("summarize-search/", views.summarize_search_view, name="summarize_search"),
    path("generate-pdf/", views.generate_pdf_view, name="generate_pdf"),

    path(
        "logout/",
        auth_views.LogoutView.as_view(
            next_page=reverse_lazy("mail_app:login")
        ),
        name="logout",
    ),
]