# celery
import time
from celery import shared_task
from celery_progress.backend import ProgressRecorder

import json
from django.db import transaction

from app.convert_gtfs import (
    gtfs_data_delete,
    download_gtfs_data,
)

@shared_task(bind=True)
def gtfs_download_task(self, urls, session_id, gDate, selData):

    progress_recorder = ProgressRecorder(self)

    process_count = 0
    process_steps = 10
    max_process_count = process_steps * len(urls)

    selInfo = json.loads(selData)

    with transaction.atomic():
        gtfs_data_delete(session_id)
        for i, url in enumerate(urls):
            try:
                process_count = i * process_steps
                download_gtfs_data(
                    url,
                    session_id,
                    gDate,
                    progress_recorder,
                    process_count,
                    max_process_count,
                    selInfo[i],
                )
            except Exception as e:
                print(f"ダウンロードまたは変換エラー: {e}")
                raise e
