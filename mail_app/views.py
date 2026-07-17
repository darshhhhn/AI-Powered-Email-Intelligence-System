"""
Views for Mail Viewer.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.db.models import Q

from .forms import MailConfigForm
from .imap_client import (
    IMAPAuthError,
    IMAPConnectionError,
    fetch_recent_emails_for_storage,
)
from .models import MailConfig, StoredEmail
from .gemini_client import (
    summarize_thread,
    analyze_email_conversations,
)
from .pdf_generator import generate_email_report


@login_required
def settings_view(request):
    config = MailConfig.objects.filter(user=request.user).first()
    instance = config or MailConfig(user=request.user)

    if request.method == "POST":
        form = MailConfigForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, "Mail settings saved.")
            return redirect("mail_app:sync_mails")

    else:
        form = MailConfigForm(instance=instance)

    return render(
        request,
        "mail_app/settings.html",
        {"form": form},
    )


@login_required
def sync_mails_view(request):
    config = MailConfig.objects.filter(user=request.user).first()

    if not config:
        messages.warning(request, "Please configure mail settings first.")
        return redirect("mail_app:settings")

    try:
        inbox_rows = fetch_recent_emails_for_storage(
            config.email,
            config.app_password,
            host=settings.IMAP_HOST,
            port=settings.IMAP_PORT,
        )

        for row in inbox_rows:
            StoredEmail.objects.get_or_create(
                user=request.user,
                subject=row["subject"],
                email_date=row["email_date"],
                defaults={
                    "sender": row["sender"],
                    "message": row["message"],
                },
            )

        messages.success(request, "Inbox refreshed successfully.")

    except IMAPAuthError:
        messages.error(request, "IMAP login failed.")
        return redirect("mail_app:settings")

    except IMAPConnectionError as exc:
        messages.error(request, f"Could not load inbox: {exc}")

    return redirect("mail_app:dashboard")


@login_required
def dashboard_view(request):
    emails = StoredEmail.objects.filter(
        user=request.user
    ).order_by("-email_date")

    return render(
        request,
        "mail_app/dashboard.html",
        {
            "emails": emails,
            "total_fetched": emails.count(),
        },
    )


@login_required
def analyze_view(request):
    emails = StoredEmail.objects.filter(
        user=request.user
    ).order_by("-email_date")[:20]

    if not emails:
        messages.warning(request, "No emails available.")
        return redirect("mail_app:dashboard")

    result = analyze_email_conversations(emails)

    return render(
        request,
        "mail_app/analysis.html",
        {
            "analysis_type": "clusters",
            "analysis": result,
        },
    )


@login_required
def search_suggestions_view(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    matches = StoredEmail.objects.filter(
        user=request.user
    ).filter(
        Q(subject__icontains=query) |
        Q(sender__icontains=query) |
        Q(message__icontains=query)
    ).values("id", "subject").distinct()[:10]

    return JsonResponse(list(matches), safe=False)


@login_required
def search_view(request):
    email_id = request.GET.get("email_id")

    if not email_id:
        messages.warning(request, "Please select a suggestion.")
        return redirect("mail_app:dashboard")

    selected = StoredEmail.objects.get(
        id=email_id,
        user=request.user
    )

    exact_query = selected.subject

    emails = StoredEmail.objects.filter(
        user=request.user
    ).filter(
        Q(subject__icontains=exact_query) |
        Q(sender=selected.sender)
    ).order_by("email_date")

    request.session["thread_email_ids"] = list(
        emails.values_list("id", flat=True)
    )

    return render(
        request,
        "mail_app/search_results.html",
        {
            "emails": emails,
            "query": selected.subject,
        },
    )


@login_required
def summarize_search_view(request):
    ids = request.session.get("thread_email_ids", [])

    if not ids:
        messages.warning(request, "No thread selected.")
        return redirect("mail_app:dashboard")

    emails = StoredEmail.objects.filter(
        id__in=ids,
        user=request.user
    ).order_by("email_date")

    summary = summarize_thread(emails)

    request.session["latest_summary"] = summary

    return render(
        request,
        "mail_app/analysis.html",
        {
            "analysis_type": "thread",
            "analysis": summary,
        },
    )


@login_required
def generate_pdf_view(request):
    ids = request.session.get("thread_email_ids", [])
    summary = request.session.get("latest_summary")

    if not ids or not summary:
        messages.warning(request, "Please summarize a thread first.")
        return redirect("mail_app:dashboard")

    emails = StoredEmail.objects.filter(
        id__in=ids,
        user=request.user
    ).order_by("email_date")

    pdf_buffer = generate_email_report(summary, emails)

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename="email_thread_report.pdf"
    )