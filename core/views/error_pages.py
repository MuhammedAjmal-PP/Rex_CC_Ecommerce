from django.shortcuts import render


def custom_404_view(request, exception):
    """
    Custom 404 handler that serves different templates
    for admin panel and user-facing pages.
    """
    if request.path.startswith("/adminpanel/"):
        template = "core/admin/404.html"
    else:
        template = "core/user/404.html"

    return render(request, template, status=404)
