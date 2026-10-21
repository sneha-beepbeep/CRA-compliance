"""Display helpers: dual local/UTC times, countdowns, neutral status chips."""
from django import template
from django.utils.html import format_html

from apps.art14 import deadlines as engine
from apps.art14.localtime import format_dual, to_local
from apps.core import clock

register = template.Library()

# Design 10.2: text first, distinct shape, never colour alone, no progression.
CHIPS = {
    "not_started": ("○", "not started"),
    "not_assessed": ("○", "not assessed"),
    "in_progress": ("◇", "in progress"),
    "assessed_planned": ("◇", "assessed – treatment planned"),
    "evidence_attached": ("◆", "evidence attached"),
    "treatment_in_place": ("◆", "treatment in place – evidence attached"),
    "evidence_stale": ("◈", "evidence stale"),
    "not_applicable": ("⊘", "not applicable"),
    "accepted": ("⊘", "accepted with rationale"),
}
CLOCK_LABEL = {"early_warning": "Early warning", "notification": "Notification", "final_report": "Final report"}
CLOCK_SHORT = {"early_warning": "EW", "notification": "NT", "final_report": "FR"}


def _tz(context):
    user = context.get("request").user if context.get("request") else None
    return getattr(user, "time_zone", None) or "UTC"


@register.simple_tag(takes_context=True)
def dual(context, dt, weekday=True):
    if not dt:
        return "–"
    return format_dual(dt, _tz(context), with_weekday=weekday)


@register.simple_tag(takes_context=True)
def local_only(context, dt):
    if not dt:
        return "–"
    loc = to_local(dt, _tz(context))
    return f"{loc:%-d %b %Y, %H:%M} {loc.tzname()}"


@register.simple_tag
def countdown(due):
    return engine.format_countdown(due, clock.now()) if due else ""


@register.simple_tag(takes_context=True)
def countdown_label(context, c):
    """Screen-reader name, e.g. 'Early warning due in 5 hours 12 minutes, at 08:05 CEST'."""
    if not c or not c.due_at:
        return ""
    now = clock.now().replace(second=0, microsecond=0)
    mins = int((c.due_at - now).total_seconds() // 60)
    loc = to_local(c.due_at, _tz(context))
    when = f"at {loc:%H:%M} {loc.tzname()}"
    name = CLOCK_LABEL[c.kind]
    if mins >= 0:
        return f"{name} due in {engine.accessible_duration(mins)}, {when}"
    return f"{name} overdue by {engine.accessible_duration(-mins)}, was due {when}"


@register.filter
def clock_name(kind):
    return CLOCK_LABEL.get(str(kind), str(kind))


@register.filter
def clock_short(kind):
    return CLOCK_SHORT.get(str(kind), str(kind))


@register.simple_tag
def chip(status):
    icon, label = CHIPS.get(status, ("○", status))
    extra = format_html(' <span class="chip-note">{}</span>', "date passed") if status == "evidence_stale" else ""
    return format_html('<span class="chip chip-{}"><span aria-hidden="true">{}</span> {}{}</span>',
                       status.replace("_", "-"), icon, label, extra)


@register.simple_tag
def clock_state(c):
    s = c.state.value
    cls = {"overdue": "cs-overdue", "open": "cs-open"}.get(s, "cs-neutral")
    word = {"overdue": "OVERDUE", "open": "OPEN"}.get(s, s)
    icon = "▲ " if s in ("overdue", "open") and c.kind == "early_warning" or s == "overdue" else ""
    return format_html('<span class="clock-state {}">{}{}</span>', cls, icon, word)


@register.filter
def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


@register.filter
def get_item(mapping, key):
    return mapping.get(key) if hasattr(mapping, "get") else None


@register.filter
def status_label(code):
    return CHIPS.get(code, (None, code))[1] if code else ""
