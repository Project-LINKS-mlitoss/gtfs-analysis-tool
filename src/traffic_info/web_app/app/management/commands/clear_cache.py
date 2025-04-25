from django.core.management.base import BaseCommand
from datetime import datetime
import os

from app.models import (
    AppAggregatorRoutes,
    AppAggregatorStops,
    AppAggregatorStopsBuffer300,
    AppRoutes,
    AppMergedRoutes,
    AppStopTimes,
    AppStops,
    AppTrips,
)


class Command(BaseCommand):
    help = "delete test data"

    def handle(self, *args, **options):
        print("delete test data", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        AppAggregatorRoutes.objects.exclude(
            file_name__in=("current", "NO_DATA")
        ).delete()
        AppAggregatorStops.objects.exclude(
            file_name__in=("current", "NO_DATA")
        ).delete()
        AppAggregatorStopsBuffer300.objects.exclude(
            file_name__in=("current", "NO_DATA")
        ).delete()
        AppRoutes.objects.exclude(file_name__in=("current", "NO_DATA")).delete()
        AppMergedRoutes.objects.exclude(file_name__in=("current", "NO_DATA")).delete()
        AppStopTimes.objects.exclude(file_name__in=("current", "NO_DATA")).delete()
        AppStops.objects.exclude(file_name__in=("current", "NO_DATA")).delete()
        AppTrips.objects.exclude(file_name__in=("current", "NO_DATA")).delete()

        os.system("rm -rf /.media/*")
        print("delete test data done", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
