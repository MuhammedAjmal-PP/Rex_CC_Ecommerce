from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def admin_dashboard(request):
    return render(request, "core/admin/dashboard.html")
