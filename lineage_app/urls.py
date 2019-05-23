from django.conf import settings
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

import os

from . import views

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/index.html"), name="index"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    path(
        "acknowledgements/",
        TemplateView.as_view(template_name="pages/acknowledgements.html"),
        name="acknowledgements",
    ),
    path(
        "terms/",
        TemplateView.as_view(template_name="pages/terms.html"),
        name="terms-of-use",
    ),
    path(
        "data-use/",
        TemplateView.as_view(template_name="pages/data-use.html"),
        name="data-use-policy",
    ),
    path("individuals/", views.individuals, name="individuals"),
    path(
        "individuals/delete/<uuid:uuid>",
        views.delete_individual,
        name="delete_individual",
    ),
    path("individuals/edit/<uuid:uuid>", views.edit_individual, name="edit_individual"),
    path("individuals/add/", views.add_individual, name="add_individual"),
    path("individuals/upload/<uuid:uuid>", views.upload_snps, name="upload_snps"),
    path("snps/download/<uuid:uuid>", views.download_snps, name="download_snps"),
    path("snps/delete/<uuid:uuid>", views.delete_snps, name="delete_snps"),
    path(
        "discrepant-snps/download/<uuid:uuid>",
        views.download_discrepant_snps,
        name="download_discrepant_snps",
    ),
    path("shared-dna-genes/", views.shared_dna_genes, name="shared_dna_genes"),
    path(
        "shared-dna-genes/delete/<uuid:uuid>",
        views.delete_shared_dna_genes,
        name="delete_shared_dna_genes",
    ),
    path(
        "shared-dna-genes/details/<uuid:uuid>",
        views.shared_dna_genes_details,
        name="shared_dna_genes_details",
    ),
    path(
        "shared-dna-genes/plot/<uuid:uuid>",
        views.shared_dna_plot,
        name="shared_dna_plot",
    ),
    path(
        "shared-dna-genes/shared-dna-one-chrom/<uuid:uuid>",
        views.shared_dna_one_chrom,
        name="shared_dna_one_chrom",
    ),
    path(
        "shared-dna-genes/shared-dna-two-chrom/<uuid:uuid>",
        views.shared_dna_two_chrom,
        name="shared_dna_two_chrom",
    ),
    path(
        "shared-dna-genes/shared-genes-one-chrom/<uuid:uuid>",
        views.shared_genes_one_chrom,
        name="shared_genes_one_chrom",
    ),
    path(
        "shared-dna-genes/shared-genes-two-chrom/<uuid:uuid>",
        views.shared_genes_two_chrom,
        name="shared_genes_two_chrom",
    ),
    path("discordant-snps/", views.discordant_snps, name="discordant_snps"),
    path(
        "discordant-snps/delete/<uuid:uuid>",
        views.delete_discordant_snps,
        name="delete_discordant_snps",
    ),
    path(
        "discordant-snps/download/<uuid:uuid>",
        views.download_discordant_snps,
        name="download_discordant_snps",
    ),
    path(
        "ajax/load-individual2/",
        views.load_individual2_dropdown,
        name="load_individual2_dropdown",
    ),
    path(
        "ajax/load-individual3/",
        views.load_individual3_dropdown,
        name="load_individual3_dropdown",
    ),
    path("users/", include("lineage_app.users.urls", namespace="users")),
    path("robots.txt", views.robots, name="robots"),
    path("tasks/", include("celery_progress.urls", namespace="celery-progress")),
]

if os.environ.get("DJANGO_SETTINGS_MODULE") == "lineage_app.settings.production":
    # https://docs.sentry.io/enriching-error-data/user-feedback/?platform=django
    from django.shortcuts import render
    from sentry_sdk import last_event_id

    def handler500(request, *args, **argv):
        return render(
            request,
            "500.html",
            {"sentry_event_id": last_event_id(), "sentry_dsn": settings.SENTRY_DSN},
            status=500,
        )


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Forbidden")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
