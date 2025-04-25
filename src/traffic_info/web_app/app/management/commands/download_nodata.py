import os
import requests
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.management import call_command

from app.convert_gtfs import convert_gtfs, gtfs_data_delete, download_gtfs_data


class Command(BaseCommand):
    help = "Scheduled execution: Download GTFS data, create network, and import into PostGIS for NO_DATA"

    def handle(self, *args, **options):
        file_name = "NO_DATA"
        gDate = "2024-04-01".replace("-", "").replace("/", "").replace(":", "")

        repo_url = f"https://api.gtfs-data.jp/v2/files?target_date=2024-04-01&pref=16"
        response = requests.get(repo_url)
        response.raise_for_status()
        data = response.json()
        body_list = data.get("body", [])
        for item in body_list:
            if item["feed_id"] == "chitetsubus":
                file_url = item["file_url"]

                with transaction.atomic():
                    gtfs_data_delete(file_name)
                    try:
                        download_gtfs_data(
                            file_url,
                            file_name,
                            gDate,
                        )
                    except Exception as e:
                        print(f"ダウンロードまたは変換エラー: {e}")
