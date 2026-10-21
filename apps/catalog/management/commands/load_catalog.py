from django.core.management.base import BaseCommand, CommandError

from apps.catalog.loader import CatalogError, load


class Command(BaseCommand):
    help = "Validate and load data/catalog/*.yaml (requirement sets, Annex III categories, taxonomies)."

    def handle(self, *args, **opts):
        try:
            rep = load()
        except CatalogError as e:
            raise CommandError(str(e))
        self.stdout.write(
            f"Loaded {rep.requirement_sets} requirement sets, {rep.requirements} requirements "
            f"({rep.draft_rows} draft, {rep.pending_oj_rows} pending OJ check), {rep.categories} categories, "
            f"{rep.taxonomies} taxonomies ({rep.taxonomy_items} items).")
        if rep.retired:
            self.stdout.write(f"Not in YAML any more (kept, statuses reference them): {', '.join(rep.retired)}")
