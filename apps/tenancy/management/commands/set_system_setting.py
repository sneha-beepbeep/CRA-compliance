from django.core.management.base import BaseCommand, CommandError

from apps.tenancy.settings_admin import SETTINGS, SettingError, current, set_setting


class Command(BaseCommand):
    help = ("Change a global system setting (audited in every vendor tenant's trail). "
            "Example: set_system_setting real_events_enabled true --operator 'A. Admin' "
            "--reason 'Pentest passed, criticals fixed, CPO approval 2026-12-07'")

    def add_arguments(self, parser):
        parser.add_argument("key", nargs="?", choices=sorted(SETTINGS))
        parser.add_argument("value", nargs="?")
        parser.add_argument("--operator", default="")
        parser.add_argument("--reason", default="")
        parser.add_argument("--list", action="store_true", help="Show every setting and its current value.")

    def handle(self, *args, key=None, value=None, operator="", reason="", list=False, **opts):
        if list or key is None:
            for k in sorted(SETTINGS):
                self.stdout.write(f"{k} = {current(k)!r}    # {SETTINGS[k].help}")
            return
        if value is None:
            raise CommandError("Give a value.")
        try:
            old, new, n = set_setting(key, value, operator=operator, reason=reason)
        except SettingError as e:
            raise CommandError(str(e))
        self.stdout.write(f"{key}: {old!r} -> {new!r}. Audited in {n} vendor audit trail(s).")
