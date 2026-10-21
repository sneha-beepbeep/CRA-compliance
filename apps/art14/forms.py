from django import forms

from apps.core import clock

from . import localtime
from .models import Art14Event

ZONE_CHOICES = [(z, z) for z in localtime.common_zones()] + [("UTC", "UTC")]



class LocalTimeMixin(forms.Form):
    """Date + time + IANA zone (+ explicit offset for repeated DST hours) -> UTC."""

    time_prefix = "awareness"
    time_label = "Awareness time"

    def add_time_fields(self, initial_tz):
        p = self.time_prefix
        self.fields[f"{p}_date"] = forms.DateField(label="Date", help_text="YYYY-MM-DD",
                                                   widget=forms.DateInput(attrs={"type": "date"}))
        self.fields[f"{p}_time"] = forms.TimeField(label="Time", help_text="24-hour, HH:MM",
                                                   widget=forms.TimeInput(attrs={"type": "time"}))
        self.fields[f"{p}_tz"] = forms.ChoiceField(label="Time zone", choices=ZONE_CHOICES, initial=initial_tz)
        self.fields[f"{p}_offset"] = forms.CharField(required=False, widget=forms.HiddenInput)
        self.ambiguous_options = None

    def clean_local_time(self, cleaned):
        p = self.time_prefix
        d, t, tz = cleaned.get(f"{p}_date"), cleaned.get(f"{p}_time"), cleaned.get(f"{p}_tz")
        if not (d and t and tz):
            return None
        try:
            return localtime.to_utc(d, t, tz, now=clock.now(), offset_choice=cleaned.get(f"{p}_offset") or None,
                                    label=self.time_label)
        except localtime.AmbiguousLocalTimeError as e:
            # No silent default (design 8.3): show the two offsets as an explicit choice.
            self.ambiguous_options = e.options
            hhmm = t.strftime("%H:%M")
            self.fields[f"{p}_offset"] = forms.ChoiceField(
                label="Which one?", widget=forms.RadioSelect,
                choices=[(o.offset_label, f"{hhmm} {o.abbreviation} (UTC{o.offset_label})") for o in e.options])
            self.add_error(f"{p}_time", e.message)
        except localtime.LocalTimeError as e:
            self.add_error(f"{p}_time", e.message)
        return None


class EventForm(LocalTimeMixin):
    event_type = forms.ChoiceField(label="Event type", choices=Art14Event.EventType.choices,
                                   widget=forms.RadioSelect)
    product = forms.ModelChoiceField(label="Product", queryset=None)
    assignee = forms.ModelChoiceField(label="Responder", queryset=None)

    def __init__(self, *args, products, responders, user_tz, **kw):
        super().__init__(*args, **kw)
        self.add_time_fields(user_tz)
        self.fields["product"].queryset = products
        self.fields["assignee"].queryset = responders
        self.fields["assignee"].label_from_instance = lambda u: f"{u.display_name} – incident responder"

    def clean(self):
        cleaned = super().clean()
        cleaned["awareness_at"] = self.clean_local_time(cleaned)
        return cleaned


class StartClockForm(EventForm):
    """S-8a: four fields only, no free text at all (OQ-D4)."""

    is_drill = forms.BooleanField(label="This is a drill", required=False)


class LogEventForm(EventForm):
    version = forms.ModelChoiceField(label="Version", queryset=None, required=False)
    deployments = forms.ModelMultipleChoiceField(label="Affected deployments", queryset=None, required=False,
                                                 widget=forms.CheckboxSelectMultiple,
                                                 help_text="You can add these later.")
    title = forms.CharField(label="Title", max_length=300)
    description = forms.CharField(label="Description", widget=forms.Textarea, required=False)
    affected_component = forms.CharField(label="Affected component", max_length=300, required=False)
    vector = forms.CharField(label="Vector", max_length=300, required=False)

    def __init__(self, *args, versions, deployments, **kw):
        super().__init__(*args, **kw)
        self.fields["version"].queryset = versions
        self.fields["deployments"].queryset = deployments


class DetailsForm(forms.Form):
    title = forms.CharField(label="Title", max_length=300, required=False)
    description = forms.CharField(label="Description", widget=forms.Textarea, required=False)
    affected_component = forms.CharField(label="Affected component", max_length=300, required=False)
    vector = forms.CharField(label="Vector", max_length=300, required=False)
    version = forms.ModelChoiceField(label="Version", queryset=None, required=False)
    deployments = forms.ModelMultipleChoiceField(label="Affected deployments", queryset=None, required=False,
                                                 widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, versions, deployments, **kw):
        super().__init__(*args, **kw)
        self.fields["version"].queryset = versions
        self.fields["deployments"].queryset = deployments


class TimeForm(LocalTimeMixin):
    time_prefix = "when"
    time_label = "This time"
    which = forms.ChoiceField(choices=[("early_warning", "Early warning filed"), ("notification", "Notification filed"),
                                       ("final_report", "Final report filed"),
                                       ("fix", "Fix or mitigation available")], widget=forms.HiddenInput)
    reason = forms.CharField(label="Reason for correction", widget=forms.Textarea, required=False,
                             help_text="Required when correcting a recorded time (at least 20 characters).")
    row_version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, user_tz, **kw):
        super().__init__(*args, **kw)
        self.add_time_fields(user_tz)

    def clean(self):
        cleaned = super().clean()
        cleaned["when_at"] = self.clean_local_time(cleaned)
        return cleaned


class AwarenessEditForm(LocalTimeMixin):
    reason = forms.CharField(label="Reason", widget=forms.Textarea, min_length=20,
                             help_text="Required, at least 20 characters. Recorded in the audit trail.")
    row_version = forms.IntegerField(widget=forms.HiddenInput)
    confirm = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, user_tz, **kw):
        super().__init__(*args, **kw)
        self.add_time_fields(user_tz)

    def clean(self):
        cleaned = super().clean()
        cleaned["awareness_at"] = self.clean_local_time(cleaned)
        return cleaned


class CloseForm(forms.Form):
    outcome = forms.ChoiceField(label="Close as", widget=forms.RadioSelect, choices=[
        (Art14Event.Status.CLOSED_REPORTING_COMPLETE, "Closed – reporting complete"),
        (Art14Event.Status.CLOSED_NOT_REPORTABLE, "Closed – determined not reportable")])
    rationale = forms.CharField(label="Rationale", widget=forms.Textarea, required=False,
                                help_text="Required for “determined not reportable” (at least 20 characters).")
    row_version = forms.IntegerField(widget=forms.HiddenInput)


class ReopenForm(forms.Form):
    reason = forms.CharField(label="Reason for reopening", widget=forms.Textarea, min_length=20)
    row_version = forms.IntegerField(widget=forms.HiddenInput)


class ReassignForm(forms.Form):
    assignee = forms.ModelChoiceField(label="Assign to", queryset=None)

    def __init__(self, *args, responders, **kw):
        super().__init__(*args, **kw)
        self.fields["assignee"].queryset = responders


class DrillOutcomeForm(forms.Form):
    answer = forms.ChoiceField(label="Would the 24h early warning have been met?", widget=forms.RadioSelect,
                               choices=[("yes", "Yes"), ("no", "No")])
    notes = forms.CharField(label="Notes", widget=forms.Textarea, required=False)
