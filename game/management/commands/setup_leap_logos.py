"""ربط شعارات عجلة LEAP من مجلد static بالقاعدة."""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from game.leap_assets import LEAP_PRIZE_LOGOS
from game.models import LeapWheel, LeapWheelPrize


class Command(BaseCommand):
    help = 'Assign default LEAP wheel logos from static/images/leap-wheel/'

    def handle(self, *args, **options):
        wheel = LeapWheel.get_instance()
        static_root = Path(settings.BASE_DIR) / 'static'
        updated = 0

        if wheel.center_logo:
            wheel.center_logo.delete(save=True)

        for prize in LeapWheelPrize.objects.filter(leap_wheel=wheel):
            rel = LEAP_PRIZE_LOGOS.get(prize.name)
            if not rel:
                continue
            logo_path = static_root / rel
            if not logo_path.is_file():
                self.stdout.write(self.style.WARNING(f'Missing {prize.name}: {logo_path}'))
                continue
            with logo_path.open('rb') as fh:
                prize.logo.save(logo_path.name, File(fh), save=True)
            updated += 1
            self.stdout.write(f'Prize OK: {logo_path.name}')

        self.stdout.write(self.style.SUCCESS(f'Done — {updated} logo(s) assigned.'))
