import os
import glob
from datetime import datetime
import requests
import osmnx as ox

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from app.convert_gtfs import convert_gtfs, gtfs_data_delete


class Command(BaseCommand):
    help = "Scheduled execution: Download GTFS data, create network, and import into PostGIS"

    def handle(self, *args, **options):
        today = datetime.now().strftime("%Y-%m-%d")

        log_path = "/.logs"
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_file_path = os.path.join(log_path, today + ".log")

        session_id_name = "current"
        download_folder = "/otp"
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        for file_path in glob.glob(os.path.join(download_folder, "*.zip")):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

        prefs = list(range(1, 48))
        prefs = [16]

        with open(log_file_path, "w") as lf:
            with transaction.atomic():
                lf.write(f"Convert Current GTFS Start")
                lf.write(f"\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")

                try:
                    lf.write(f"\n\ndb date deleting")
                    lf.write(f"\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
                    gtfs_data_delete(session_id_name)

                    for pref_no in prefs:
                        print(f"Pref No: {pref_no} Get Data")
                        lf.write(f"\n\nPref No: {pref_no} Get Data")
                        lf.write(f"\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
                        repo_url = f"https://api.gtfs-data.jp/v2/files?target_date={today}&pref={pref_no}"

                        response = requests.get(repo_url)
                        if response.status_code != 200:
                            lf.write(
                                f"\nFailed to get GTFS data from {response.status_code} {repo_url}"
                            )
                            lf.write(response.text)
                            continue

                        data = response.json()
                        body = data["body"]
                        for _, item in enumerate(body, 1):
                            print(f"File Download feed_id: {item['feed_id']}")
                            lf.write(f"\n\nFile Download feed_id: {item['feed_id']}")

                            zip_response = requests.get(item["file_url"])
                            if zip_response.status_code == 200:
                                file_name = (
                                    f"{item['feed_id']}-{item['file_uid']}-GTFS.zip"
                                )
                                file_path = os.path.join(download_folder, file_name)
                                with open(file_path, "wb") as f:
                                    f.write(zip_response.content)
                                    try:
                                        lf.write(f"\n    make network")
                                        lf.write(
                                            f"\n    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
                                        )
                                        convert_gtfs(lf, session_id_name, file_path)
                                        lf.write(f"\n    complete network")
                                        lf.write(
                                            f"\n    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
                                        )
                                    except Exception as e:
                                        lf.write(
                                            f"\nFailed to convert GTFS to PostGIS: {e}"
                                        )

                    lf.write(f"\nCOMMIT")
                    lf.write(f"\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")

                except Exception as ex:
                    lf.write(f"\nROLLBACK")
                    raise ex


            lf.write(f"\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
