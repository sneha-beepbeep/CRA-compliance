"""S-14 users and roles; profile (time zone)."""
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.art14.forms import ZONE_CHOICES
from apps.authz.capabilities import Capability, has_capability, requires

from . import services
from .models import RoleGrant, UserAccount


@requires(Capability.REGISTRY_EDIT)
def users(request):
    ctx = request.tenant_ctx
    people = UserAccount.objects.filter(tenant_id=ctx.tenant_id).order_by("display_name")
    active = set(RoleGrant.objects.filter(role="incident_responder", revoked_at__isnull=True)
                 .values_list("user_id", flat=True))
    customers = UserAccount.objects.exclude(tenant_id=ctx.tenant_id).select_related("tenant").order_by("email")
    return render(request, "tenancy/users.html", {
        "people": [(u, u.pk in active) for u in people], "customers": customers,
        "can_manage": has_capability(ctx, Capability.ROLES_MANAGE),
        "managers": people.filter(is_access_manager=True)})


@requires(Capability.ROLES_MANAGE)
@require_POST
def set_responder(request, pk):
    user = UserAccount.objects.filter(pk=pk, tenant_id=request.tenant_ctx.tenant_id).first()
    if user is None:
        raise Http404
    if request.POST.get("grant") == "1":
        services.grant_responder(request, user)
        messages.info(request, f"{user.display_name} is now an incident responder.")
    else:
        services.revoke_responder(request, user)
        messages.info(request, f"{user.display_name} no longer has the incident responder role.")
    return redirect("/setup/users/")


class ProfileForm(forms.Form):
    time_zone = forms.ChoiceField(label="Display time zone", choices=ZONE_CHOICES)


@requires(Capability.AUTHENTICATED)
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, initial={"time_zone": request.user.time_zone})
    if request.method == "POST" and form.is_valid():
        if request.tenant_ctx.workspace != "vendor":
            raise Http404  # customer profile editing arrives with the customer workspace (phase 1b)
        services.set_time_zone(request, form.cleaned_data["time_zone"])
        messages.info(request, "Time zone saved.")
        return redirect("/profile/")
    return render(request, "tenancy/profile.html", {"form": form})
