"""S-14 products, versions, deployments (setup) and version selection."""
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.authz.capabilities import Capability, requires
from apps.catalog.models import AnnexIIICategory

from . import services
from .models import Deployment, Product, ProductVersion


class CategorySelect(forms.Select):
    """Unsupported categories are listed but disabled (design 5, step 3)."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        opt = super().create_option(name, value, label, selected, index, subindex, attrs)
        cat = getattr(value, "instance", None)
        if cat is not None and not cat.supported:
            opt["attrs"]["disabled"] = True
        return opt


class ProductForm(forms.Form):
    name = forms.CharField(label="Product name", max_length=200)
    intended_purpose = forms.CharField(label="Intended purpose", widget=forms.Textarea)
    category = forms.ModelChoiceField(label="Annex III category", queryset=AnnexIIICategory.objects.all(),
                                      widget=CategorySelect)
    delivery_model = forms.ChoiceField(label="Delivery model", choices=[("", "–")] + Product.DeliveryModel.choices,
                                       required=False)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["category"].label_from_instance = (
            lambda c: c.citation if c.supported else f"{c.citation} – not yet supported")

    def clean_category(self):
        c = self.cleaned_data["category"]
        if not c.supported:
            raise forms.ValidationError(f"{c.citation} – not yet supported")
        return c


class VersionForm(forms.Form):
    product = forms.ModelChoiceField(label="Product", queryset=Product.objects.none())
    label = forms.CharField(label="Version label", max_length=64)
    release_date = forms.DateField(label="Release date", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["product"].queryset = Product.objects.all()


class DeploymentForm(forms.Form):
    customer_name = forms.CharField(label="Customer name", max_length=200,
                                    help_text="Creates the customer if it doesn't exist yet.")
    label = forms.CharField(label="Deployment label", max_length=200)
    version = forms.ModelChoiceField(label="Version deployed", queryset=ProductVersion.objects.none())

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["version"].queryset = ProductVersion.objects.select_related("product")


def _ctx(request, **forms_):
    return {"products": Product.objects.prefetch_related("versions").select_related("category"),
            "deployments": Deployment.objects.select_related("customer_tenant", "version", "product"),
            "product_form": forms_.get("product_form") or ProductForm(),
            "version_form": forms_.get("version_form") or VersionForm(),
            "deployment_form": forms_.get("deployment_form") or DeploymentForm(),
            "checklist": services.setup_checklist(request), "hosted_warning": services.HOSTED_ONLY_WARNING}


@requires(Capability.REGISTRY_EDIT)
def setup(request):
    return render(request, "registry/setup.html", _ctx(request))


@requires(Capability.REGISTRY_EDIT)
@require_POST
def add_product(request):
    form = ProductForm(request.POST)
    if form.is_valid():
        p = services.create_product(request, **form.cleaned_data)
        if p.delivery_model == Product.DeliveryModel.HOSTED_ONLY:
            messages.warning(request, services.HOSTED_ONLY_WARNING)
        messages.info(request, f"{p.name} added.")
        return redirect("/setup/")
    return render(request, "registry/setup.html", _ctx(request, product_form=form), status=400)


@requires(Capability.REGISTRY_EDIT)
@require_POST
def add_version(request):
    form = VersionForm(request.POST)
    if form.is_valid():
        if ProductVersion.objects.filter(product=form.cleaned_data["product"], label=form.cleaned_data["label"]).exists():
            form.add_error("label", "This version already exists.")
        else:
            v = services.create_version(request, **form.cleaned_data)
            request.session["version_id"] = str(v.pk)
            messages.info(request, f"Version {v.label} added. Requirement sets attached from the catalog data.")
            return redirect("/setup/")
    return render(request, "registry/setup.html", _ctx(request, version_form=form), status=400)


@requires(Capability.REGISTRY_EDIT)
@require_POST
def add_deployment(request):
    form = DeploymentForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        d = services.create_deployment(request, product=cd["version"].product, version=cd["version"],
                                       label=cd["label"], customer_name=cd["customer_name"])
        messages.info(request, f"Deployment {d.label} added.")
        return redirect("/setup/")
    return render(request, "registry/setup.html", _ctx(request, deployment_form=form), status=400)


@requires(Capability.VENDOR_OVERVIEW)
@require_POST
def select_version(request):
    v = ProductVersion.objects.filter(pk=request.POST.get("version", "")).first()
    if v is None:
        raise Http404
    request.session["version_id"] = str(v.pk)
    nxt = request.POST.get("next", "/")
    return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else "/")
