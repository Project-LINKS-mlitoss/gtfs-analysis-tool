from decimal import Decimal
from datetime import date, datetime
import json
import numpy as np
from collections import defaultdict
import os
from itertools import groupby
from operator import itemgetter
import ast
from collections import Counter
import shutil

import gtfs_parser
from gtfs_parser.gtfs import GTFS

from django.core.management import call_command
from django.db.models import Q, Sum, OuterRef, Subquery
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.conf import settings
import requests

import pdfkit
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotAllowed
import base64
from django.utils.safestring import mark_safe

from app.models import (
    AppStopTimes,
    AppStops,
    AppAggregatorStops,
    AppAggregatorRoutes,
    AppRoutes,
    AppTrips,
    AppAggregatorStopsBuffer300,
    AppMergedRoutes,
    AppCalendar,
    AppCalendarDates,
)
from app.convert_gtfs import (
    gtfs_data_delete,
    convert_gtfs_to_postgis,
)
import app.gtfs_isochrone as gtfs_isochrone

from django.db import connection
import pandas as pd
from django.http import StreamingHttpResponse
import csv
import tempfile
import zipfile

from celery import shared_task
from celery_progress.backend import ProgressRecorder
import time
from app.tasks import gtfs_download_task

import re
from django.db.models import IntegerField, F
from django.db.models.functions import Cast
from django.core.exceptions import ValidationError


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        elif isinstance(obj, pd.Series):
            return obj.to_dict()

        else:
            return super(MyEncoder, self).default(obj)


def stop_times(request, session_id, stop_id):
    routes = list(
        AppStopTimes.objects.filter(stop_id=stop_id, file_name=session_id).values(
            "trip_id", "stop_headsign", "arrival_time"
        )
    )
    return HttpResponse(
        json.dumps(routes, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def trip_detail(request, file_name, trip_id):
    trips = AppStopTimes.objects.filter(trip_id=trip_id, file_name=file_name).values(
        "arrival_time", "departure_time", "stop_id"
    )
    trip_routes = []
    for trip in trips:
        trip_routes.append(
            {
                "arrival_time": trip["arrival_time"],
                "departure_time": trip["departure_time"],
                "stop_name": AppStops.objects.filter(
                    stop_id=trip["stop_id"], file_name=file_name
                ).values("stop_name")[0]["stop_name"],
            }
        )

    return HttpResponse(
        json.dumps(trip_routes, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_route_ids(request, file_name, route_name):
    route_ids = list(
        AppRoutes.objects.filter(route_name=route_name, file_name=file_name).values(
            "route_id"
        )
    )
    return HttpResponse(
        json.dumps(route_ids, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_route_sl_name(request, file_name, route_id):
    route_title = ""
    route_ids = AppRoutes.objects.filter(route_id=route_id, file_name=file_name)
    for route in route_ids:
        s_name = route.route_short_name
        l_name = route.route_long_name
        if route.route_short_name == None:
            s_name = ""
        if route.route_long_name == None:
            l_name = ""
        if s_name == "nan" or s_name == "NaN":
            s_name = ""
        if l_name == "nan" or l_name == "NaN":
            l_name = ""
        route_title = s_name + " " + l_name
    return HttpResponse(
        json.dumps(route_title, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_route_to_stop_ids(request, file_name, route_id):
    one_trip = (
        AppTrips.objects.filter(route_id=route_id, file_name=file_name)
        .values_list("trip_id", flat=True)
        .first()
    )
    first_stop_time = AppStopTimes.objects.filter(
        trip_id=one_trip, file_name=file_name
    ).values("stop_id", "stop_sequence")
    stop_ids = []
    for stop_time in first_stop_time:
        stop = AppStops.objects.filter(
            stop_id=stop_time["stop_id"], file_name=file_name
        ).first()
        stop_ids.append(
            {
                "stop_id": stop.stop_id,
                "stop_name": stop.stop_name,
                "stop_sequence": stop_time["stop_sequence"],
            }
        )
    return HttpResponse(
        json.dumps(stop_ids, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def stops_on_route(request, file_name, route_id, direction_id):
    route_ids = AppRoutes.objects.filter(route_id=route_id, file_name=file_name).values(
        "route_id"
    )

    direction = []
    if direction_id == "0":
        direction = ["0"]
    if direction_id == "1":
        direction = ["1"]
    if len(direction) == 0:
        direction = ["0", "1", "nan"]

    first_trip_id = AppTrips.objects.filter(
        route_id=route_id, file_name=file_name, direction_id__in=direction
    ).values("trip_id")
    if first_trip_id.count() == 0:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    first_stop_time = AppStopTimes.objects.filter(
        trip_id=first_trip_id[0]["trip_id"], stop_sequence=1, file_name=file_name
    ).values("stop_id")
    if first_stop_time.count() == 0:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )

    stops = []
    for route in route_ids:
        route_id = route["route_id"]
        stops += AppStops.objects.filter(
            (
                Q(route_ids__startswith="{" + route_id + ",")
                | Q(route_ids__startswith="{" + route_id + "}")
                | Q(route_ids__startswith="[" + route_id + ",")
                | Q(route_ids__startswith="[" + route_id + "]")
                | Q(route_ids__contains="," + route_id + ",")
                | Q(route_ids__contains="'" + route_id + "'")
                | Q(route_ids__endswith="," + route_id + "}")
            ),
            file_name=file_name,
        )
    stops_list = []
    service_ids = []
    for stop in stops:
        ct = AppAggregatorStops.objects.filter(
            similar_stop_id=stop.stop_id, file_name=file_name
        ).values("service_id")
        for c in ct:
            service_ids.append(c["service_id"])

    for service_id in list(set(service_ids)):
        for i in range(len(stops) - 1):
            p_stop = stops[i]
            n_stop = stops[i + 1]
            rr = AppAggregatorRoutes.objects.filter(
                prev_stop_id=p_stop.stop_id,
                next_stop_id=n_stop.stop_id,
                file_name=file_name,
            ).aggregate(total_frequency=Sum("frequency"))
            total_frequency = rr["total_frequency"] if rr["total_frequency"] else 0
            sl = {
                "service_id": service_id,
                "stop_id": p_stop.stop_id,
                "stop_name": p_stop.stop_name,
                "count": total_frequency,
            }
            stops_list.append(sl)

    if stops_list[0]["stop_id"] != first_stop_time[0]["stop_id"]:
        stops_list.reverse()

    grouped_stops = {
        service_id: list(group)
        for service_id, group in groupby(stops_list, key=itemgetter("service_id"))
    }

    return HttpResponse(
        json.dumps(grouped_stops, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def gtfs_download(request):
    if request.method == "POST":
        data = json.loads(request.body)
        session_id = data["session_id"]
        pref = data["pref"]
        request.session["pref"] = pref
        gDate = data["gDate"].replace("-", "").replace("/", "").replace(":", "")
        selData = mark_safe(json.dumps(data["selData"], ensure_ascii=False))
        request.session["selData"] = selData

        task = gtfs_download_task.delay(data["urls"], session_id, gDate, selData)
        result = task.result
        return JsonResponse({"task_id": task.id})
    return HttpResponseNotAllowed(["POST"])


def isochrone(request, session_id):
    try:
        lat = float(request.GET["lat"])
        lon = float(request.GET["lon"])
        date_str = request.GET["start"]
        start_datetime = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError, KeyError):
        return HttpResponseBadRequest(
            "invalid query string. Valid example: GET /isochrone"
            "?duration=2700&lat=47.910244&lon=1.907501&start=2020-07-02T08:00:00",
            "application/json",
        )

    features = gtfs_isochrone.compute_isochrone(session_id, lat, lon, start_datetime)
    gjson = {"type": "FeatureCollection", "features": features}
    return HttpResponse(
        json.dumps(gjson, cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def gtfs_upload(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file was uploaded"}, status=400)

    uploaded_file = request.FILES["file"]
    if not uploaded_file.name.endswith(".zip"):
        return JsonResponse(
            {"error": "Uploaded file must be a ZIP archive"}, status=400
        )

    temp_zip_path = os.path.join("/", ".media", f"{session_id}-GTFS.zip")
    with open(temp_zip_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    try:
        with transaction.atomic():
            gtfs_data_delete(session_id)
            convert_gtfs_to_postgis(temp_zip_path, session_id, "")

            return JsonResponse(
                {
                    "message": "GTFS files uploaded and extracted successfully",
                    "session_id": session_id,
                }
            )
    except Exception as e:
        return JsonResponse(
            {"error": f"Error while processing GTFS files: {str(e)}"}, status=500
        )


def jisseki_csv_upload(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file was uploaded"}, status=400)

    uploaded_file = request.FILES["file"]
    if not uploaded_file.name.endswith(".csv"):
        return JsonResponse(
            {"error": "Uploaded file must be a CSV archive"}, status=400
        )

    temp_csv_path = os.path.join("/", ".media", f"{session_id}-JISSEKI.csv")
    with open(temp_csv_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    msg = ""
    agency_ids = set()
    try:
        with open(
            temp_csv_path, "r", encoding="utf-8-sig"
        ) as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)

            if not header:
                msg = "行ヘッダが無いCSVファイルが指定されています。"
            else:
                required_headers = {
                    "agency_id",
                    "route_id",
                    "trip_id",
                    "stop_id",
                    "stop_sequence",
                    "date",
                    "count_geton",
                    "count_getoff",
                }

                processed_header = {h.strip('"').lower() for h in header}
                if required_headers.issubset(processed_header):
                    msg = "OK"
                else:
                    missing_headers = required_headers - processed_header
                    msg = f"乗降実績データの処理に必要な列({', '.join(missing_headers)})が不足しています。"
            if msg == "OK":
                agency_id_index = [h.lower() for h in header].index("agency_id")
                expected_column_count = len(processed_header)
                ngcount = 0
                for row_number, row in enumerate(reader, start=2):
                    if row:
                        if len(row) != expected_column_count:
                            ngcount += 1
                        else:
                            agency_id = row[agency_id_index]
                            agency_ids.add(agency_id)

                if ngcount > 0:
                    msg = f"所定の列数が無い行が{ngcount}行ありました。ファイルの内容を確認してください。"

    except UnicodeDecodeError:
        msg = "CSVのエンコードがUTF-8であるか確認してください。"
    except csv.Error as e:
        msg = "CSVの読み取り時にエラーが発生しました。ファイルの内容を確認してください。\r\n" + str(
            e
        )
    except FileNotFoundError:
        msg = "CSVファイルを読み込めませんでした。"

    if msg == "OK":
        for agency_id in agency_ids:
            count = AppAggregatorRoutes.objects.filter(
                agency_id=agency_id, file_name=session_id
            ).count()
            if count == 0:
                msg = "読み込み済のGTFSデータのagency_idと合致しないCSVが指定されています。"
                break

        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            data = f.read()

        with open(temp_csv_path, "w", encoding="utf-8") as f:
            f.write(data)

    if msg != "OK":
        print(delete_csv_file(temp_csv_path))

    return JsonResponse(
        {
            "message": msg,
            "session_id": session_id,
        }
    )


def download_exportfile(request):
    if request.method == "POST":

        count = 0
        layerscount = 0
        csvscount = 0
        isochronecount = 0
        aggregatorcsvcount = 0

        layers = json.loads(request.body).get("layers", [])
        csvs = json.loads(request.body).get("csvs", [])
        isochrone = json.loads(request.body).get("isochrone", [])

        session_id = json.loads(request.body).get("session_id")
        pref = json.loads(request.body).get("pref")
        year = json.loads(request.body).get("year")

        layerscount = len(layers)
        csvscount = len(csvs)

        count = layerscount + csvscount
        print("layerscount is " + str(layerscount))
        with tempfile.TemporaryDirectory() as temp_dir:

            for layer in layers:
                layer_name = layer[4:-2]

                file_path = os.path.join(temp_dir, f"{layer_name}.geojson")

                SQL = ""
                prm = []

                if layer_name == "到達圏域":
                    isochroneGeoJSON = json.loads(isochrone)
                    file_path = os.path.join(temp_dir, "isochrone.geojson")
                    with open(file_path, "w") as f:
                        json.dump(isochroneGeoJSON, f, ensure_ascii=False)

                    if count == 1 and layerscount == 1:
                        with open(file_path, "rb") as f:
                            response = HttpResponse(
                                f, content_type="application/geo+json"
                            )
                            return response
                elif layer_name == "鉄道路線":
                    SQL += "SELECT "
                    SQL += "jsonb_build_object("
                    SQL += "    'type', 'FeatureCollection', "
                    SQL += "    'features', jsonb_agg(feature)"
                    SQL += ") FROM ("
                    SQL += "    SELECT jsonb_build_object("
                    SQL += "        'type', 'Feature', "
                    SQL += "        'id', id,"
                    SQL += "        'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb, "
                    SQL += "        'properties', to_jsonb(inputs) - 'id' - 'geom'"
                    SQL += "    ) AS feature FROM ("
                    SQL += (
                        "        SELECT * from app_railroadsection where prefs like %s"
                    )
                    SQL += "    ) inputs"
                    SQL += ") features"

                    prm.append(f"%[{pref}]%")

                    with connection.cursor() as cursor:
                        cursor.execute(SQL, prm)

                        geojson_data = cursor.fetchone()[0]
                        with open(file_path, "w") as f:
                            f.write(geojson_data)

                        if count == 1 and layerscount == 1:
                            with open(file_path, "rb") as f:
                                response = HttpResponse(
                                    f, content_type="application/geo+json"
                                )

                                return response

                elif layer_name.startswith("メッシュ人口") or layer_name.startswith(
                    "メッシュ5人口"
                ):

                    geoserver_url = f"http://geoserver:8080/geoserver/traffic_info/wfs?service=WFS&version=1.1.0&request=GetFeature&typename=traffic_info:{layer_name}&outputFormat=application/json&srsname=EPSG:4326"
                    if pref:
                        geoserver_url += (
                            f"&CQL_FILTER=prefs%20like%20%27%25%5B{pref}%5D%25%27"
                        )

                    try:
                        response = requests.get(geoserver_url)
                        response.encoding = "utf-8"
                        response.raise_for_status()
                        geojson_data = response.json()

                        file_path = os.path.join(temp_dir, f"{layer_name}.geojson")
                        with open(
                            file_path, "w", encoding="utf-8"
                        ) as f:
                            json.dump(geojson_data, f, ensure_ascii=False)
                        if count == 1 and layerscount == 1:
                            return HttpResponse(
                                json.dumps(geojson_data, ensure_ascii=False),
                                content_type="application/geo+json",
                            )

                    except requests.exceptions.RequestException as e:
                        print(f"Error requesting data from GeoServer: {e}")
                        return HttpResponse(status=500)

                elif layer_name.startswith("小地域人口") or layer_name.startswith(
                    "利用交通手段"
                ):
                    geoserver_url = f"http://geoserver:8080/geoserver/traffic_info/wfs?service=WFS&version=1.1.0&request=GetFeature&typename=traffic_info:{layer_name}&outputFormat=application/json&srsname=EPSG:4326"
                    if pref:
                        geoserver_url += f"&CQL_FILTER=pref={pref}"

                    try:
                        response = requests.get(geoserver_url)
                        response.encoding = "utf-8"
                        response.raise_for_status()
                        geojson_data = response.json()

                        file_path = os.path.join(temp_dir, f"{layer_name}.geojson")
                        with open(
                            file_path, "w", encoding="utf-8"
                        ) as f:
                            json.dump(geojson_data, f, ensure_ascii=False)
                        if count == 1 and layerscount == 1:
                            return HttpResponse(
                                json.dumps(geojson_data, ensure_ascii=False),
                                content_type="application/geo+json",
                            )

                    except requests.exceptions.RequestException as e:
                        print(f"Error requesting data from GeoServer: {e}")
                        return HttpResponse(status=500)
            for csv_ in csvs:
                filename = csv_[4:-2]
                file_path = os.path.join(temp_dir, f"{filename}.csv")

                if filename == "運行本数集計":
                    service_ids = (
                        AppTrips.objects.filter(
                            file_name=session_id,
                            trip_id__in=AppStopTimes.objects.filter(
                                file_name=session_id
                            ).values_list("trip_id", flat=True),
                        )
                        .values_list("service_id", flat=True)
                        .distinct()
                    )

                    if len(service_ids) == 2 and "平日" in service_ids:
                        other_service_id = next(
                            sid for sid in service_ids if sid != "平日"
                        )
                        if any(
                            keyword in other_service_id
                            for keyword in ["土", "祝", "祭"]
                        ):
                            service_ids = ["平日", other_service_id]

                    routes = AppRoutes.objects.filter(file_name=session_id).values(
                        "route_id", "route_long_name", "route_short_name"
                    )
                    routes_df = pd.DataFrame(list(routes))

                    header = ["route_name", "route_id"]
                    for day_type in service_ids:
                        for hour in range(4, 26):
                            header.append(f"{day_type}__{str(hour).zfill(2)}")
                        header.append(f"{day_type}__合計")

                    data = []

                    for index, row in routes_df.iterrows():
                        route_id = row["route_id"]
                        route_name = (
                            row["route_short_name"]
                            if row["route_long_name"] == "nan"
                            else row["route_long_name"]
                        )
                        row_data = [route_name, route_id]

                        for day_type in service_ids:
                            hour_counts = defaultdict(
                                set
                            )
                            trips = AppTrips.objects.filter(
                                file_name=session_id,
                                route_id=route_id,
                                service_id=day_type,
                            ).values_list("trip_id", flat=True)
                            stop_times = AppStopTimes.objects.filter(
                                file_name=session_id, trip_id__in=trips
                            )

                            for stop_time in stop_times:
                                hour = int(stop_time.departure_time.split(":")[0])
                                if stop_time.trip_id not in hour_counts[hour]:
                                    hour_counts[hour].add(stop_time.trip_id)

                            total_count = 0
                            for hour in range(4, 26):
                                t_count = len(
                                    hour_counts[hour]
                                )
                                row_data.append(t_count)
                                total_count += t_count
                            row_data.append(total_count)

                        data.append(row_data)

                    if count == 1 and csvscount == 1:
                        response = HttpResponse(content_type="text/csv; charset=utf-8")
                        response["Content-Disposition"] = (
                            "attachment; filename='route_frequency.csv'"
                        )
                        writer = csv.writer(response)
                        writer.writerow(header)
                        writer.writerows(data)
                        return response
                    else:
                        with open(
                            file_path, "w", newline="", encoding="utf-8"
                        ) as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(header)
                            writer.writerows(data)
                else:
                    SQL = ""
                    prm = []

                    if filename == "メッシュ人口及び世帯":
                        SQL = "select a.* from app_stat_mesh_pop a inner join app_mesh b on a.KEY_CODE = b.KEY_CODE and b.prefs like %s and a.year = %s"
                        prm.append("%[" + str(pref) + "]%")
                        prm.append(year)

                    elif filename == "男女別人口総数及び世帯数":
                        pass
                    elif filename == "小地域年齢（5階級）別男女別人口":
                        pass
                    elif filename == "利用交通手段別通勤者・通学者数":
                        pass

                    if SQL != "":
                        with connection.cursor() as cursor:
                            cursor.execute(SQL, prm)
                            record_count = cursor.rowcount

                            rows = cursor.fetchall()

                            df = pd.DataFrame(
                                rows,
                                columns=[column[0] for column in cursor.description],
                            )

                            if count == 1 and csvscount == 1:

                                response = HttpResponse(
                                    df.to_csv(index=False), content_type="text/csv"
                                )
                                response["Content-Disposition"] = (
                                    'attachment; filename="output.csv"'
                                )
                                return response
                            else:
                                df.to_csv(file_path, index=False)
            zip_file_path = os.path.join(temp_dir, "export.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for filename in os.listdir(temp_dir):
                    if filename.endswith(".zip"):
                        continue

                    file_path = os.path.join(temp_dir, filename)
                    zipf.write(
                        file_path, arcname=filename
                    )

            with open(zip_file_path, "rb") as f:
                response = HttpResponse(f, content_type="application/zip")
                response["Content-Disposition"] = 'attachment; filename="export.zip"'

                return response

    return HttpResponse(status=400)


def get_time_table(request, session_id, service_id, route_id, stop_id):

    if not stop_id:
        return HttpResponseBadRequest("stop_id is required")

    stops = pd.DataFrame(AppStops.objects.filter(file_name=session_id).values())
    stop_times = pd.DataFrame(
        AppStopTimes.objects.filter(file_name=session_id).values()
    )
    trips = pd.DataFrame(AppTrips.objects.filter(file_name=session_id).values())
    routes = pd.DataFrame(AppRoutes.objects.filter(file_name=session_id).values())

    routes[["route_short_name", "route_long_name"]] = routes[
        ["route_short_name", "route_long_name"]
    ].fillna("-")

    routes["route_id"] = routes["route_id"].astype(str)
    trips["route_id"] = trips["route_id"].astype(str)

    timetable = stop_times.merge(trips, on="trip_id").merge(routes, on="route_id")
    timetable = timetable[timetable["service_id"] == service_id]
    if route_id != "-1":
        timetable = timetable[timetable["route_id"] == route_id]
    timetable = timetable[timetable["stop_id"] == stop_id]

    timetable = timetable[
        [
            "trip_headsign",
            "departure_time",
            "service_id",
            "route_id",
            "route_short_name",
            "route_long_name",
        ]
    ]
    timetable = timetable.sort_values("departure_time")

    hourly_timetable = defaultdict(lambda: defaultdict(list))
    for _, row in timetable.iterrows():
        hour = row["departure_time"].split(":")[0]
        minute = row["departure_time"].split(":")[1]
        hourly_timetable[row["service_id"]][hour].append(
            {
                "trip_headsign": row["trip_headsign"],
                "departure_time": minute,
            }
        )

    sorted_hourly_timetable = dict(sorted(hourly_timetable.items()))

    return HttpResponse(
        json.dumps(
            {
                "stop_id": stop_id,
                "stop_name": stops[stops["stop_id"] == stop_id]["stop_name"].values[0],
                "route_id": route_id,
                "route_short_name": (
                    timetable["route_short_name"].values[0]
                    if len(timetable) > 0
                    else routes[routes["route_id"] == route_id][
                        "route_short_name"
                    ].values[0]
                ),
                "route_long_name": (
                    timetable["route_long_name"].values[0]
                    if len(timetable) > 0
                    else routes[routes["route_id"] == route_id][
                        "route_long_name"
                    ].values[0]
                ),
                "hourly_timetable": (
                    sorted_hourly_timetable if len(timetable) > 0 else {}
                ),
            },
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_uniq_service_id(request, session_id):
    trips_service_ids = set(
        AppTrips.objects.filter(file_name=session_id)
        .values_list("service_id", flat=True)
        .distinct()
    )

    calendars = (
        AppCalendar.objects.filter(file_name=session_id)
        .values("service_id")
        .order_by("id")
    )
    calendar_service_ids_ordered = [
        item["service_id"] for item in calendars
    ]

    final_service_ids = [
        service_id
        for service_id in calendar_service_ids_ordered
        if service_id in trips_service_ids
    ]

    return HttpResponse(
        json.dumps(
            {"service_ids": final_service_ids},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_route_to_trip_ids(request, file_name, route_id, direction_id):
    direction = []
    if direction_id == "0":
        direction = ["0"]
    if direction_id == "1":
        direction = ["1"]
    if len(direction) == 0:
        direction = ["0", "1", "nan", ""]

    trips = (
        AppTrips.objects.filter(
            file_name=file_name, route_id=route_id, direction_id__in=direction
        )
        .values_list("trip_id", flat=True)
        .distinct()
    )

    return HttpResponse(
        json.dumps(
            {"trips": list(trips)},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_route_to_jisseki_data(request, file_name, trip_id, direction_id, hour):
    if (hour == "undefined") or (hour == ""):
        hour = "-1"

    direction = []
    if direction_id == "0":
        direction = ["0"]
    if direction_id == "1":
        direction = ["1"]
    if len(direction) == 0:
        direction = ["0", "1", "nan", ""]

    file_path = f"/.media/{file_name}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)

    trips = AppTrips.objects.filter(
        file_name=file_name, trip_id=trip_id, direction_id__in=direction
    ).values_list("trip_id", flat=True)

    filtered_data = excel_data[excel_data["trip_id"].isin([trip_id])]
    filtered_data["departure_time"] = pd.to_datetime(
        filtered_data["departure_time"], format="%H:%M:%S"
    ).dt.time

    if int(hour) > 0:
        start_time = pd.to_datetime(f"{int(hour):02d}:00:00").time()
        end_time = pd.to_datetime(f"{int(hour):02d}:59:59").time()
        filtered_data = filtered_data[
            (filtered_data["departure_time"] >= start_time)
            & (filtered_data["departure_time"] <= end_time)
        ]

    unique_route_name = filtered_data["route_name"].unique().tolist()
    return HttpResponse(
        json.dumps(
            {
                "route_name": unique_route_name,
                "data": filtered_data[
                    [
                        "stop_sequence",
                        "stop_id",
                        "stop_name",
                        "乗車中人数",
                        "乗車数",
                        "降車数",
                    ]
                ]
                .fillna("")
                .to_dict(orient="records"),
            },
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def current_to_copy(file_name):
    st = AppStopTimes.objects.filter(file_name=file_name)
    if st.count() == 0:
        print("current_to_copy start", file_name, datetime.now())
        org_file = os.path.join("/", ".media", "NO_DATA-GTFS")
        copy_file = os.path.join("/", ".media", file_name + "-GTFS")
        if os.path.exists(copy_file):
            shutil.rmtree(copy_file)
        shutil.copytree(org_file, copy_file)

        print("current_to_copy db", file_name, datetime.now())
        with transaction.atomic():
            AppCalendar.objects.bulk_create(
                list(
                    AppCalendar(
                        file_name=file_name,
                        service_id=cal.service_id,
                        monday=cal.monday,
                        tuesday=cal.tuesday,
                        wednesday=cal.wednesday,
                        thursday=cal.thursday,
                        friday=cal.friday,
                        saturday=cal.saturday,
                        sunday=cal.sunday,
                        start_date=cal.start_date,
                        end_date=cal.end_date,
                    )
                    for cal in AppCalendar.objects.filter(file_name="NO_DATA")
                )
            )
            AppCalendarDates.objects.bulk_create(
                list(
                    AppCalendarDates(
                        file_name=file_name,
                        service_id=cal.service_id,
                        date=cal.date,
                        exception_type=cal.exception_type,
                    )
                    for cal in AppCalendarDates.objects.filter(file_name="NO_DATA")
                )
            )
            AppTrips.objects.bulk_create(
                list(
                    AppTrips(
                        file_name=file_name,
                        route_id=trip.route_id,
                        service_id=trip.service_id,
                        trip_id=trip.trip_id,
                        trip_headsign=trip.trip_headsign,
                        block_id=trip.block_id,
                        trip_short_name=trip.trip_short_name,
                        direction_id=trip.direction_id,
                        shape_id=trip.shape_id,
                    )
                    for trip in AppTrips.objects.filter(file_name="NO_DATA")
                )
            )
            AppStopTimes.objects.bulk_create(
                list(
                    AppStopTimes(
                        file_name=file_name,
                        trip_id=stop.trip_id,
                        arrival_time=stop.arrival_time,
                        departure_time=stop.departure_time,
                        stop_id=stop.stop_id,
                        stop_sequence=stop.stop_sequence,
                        stop_headsign=stop.stop_headsign,
                        pickup_type=stop.pickup_type,
                        drop_off_type=stop.drop_off_type,
                        timepoint=stop.timepoint,
                    )
                    for stop in AppStopTimes.objects.filter(file_name="NO_DATA")
                )
            )
            AppStops.objects.bulk_create(
                list(
                    AppStops(
                        file_name=file_name,
                        stop_id=stop.stop_id,
                        similar_stop_id=stop.similar_stop_id,
                        stop_name=stop.stop_name,
                        geom=stop.geom,
                        route_ids=stop.route_ids,
                    )
                    for stop in AppStops.objects.filter(file_name="NO_DATA")
                )
            )
            AppRoutes.objects.bulk_create(
                list(
                    AppRoutes(
                        file_name=file_name,
                        route_id=route.route_id,
                        geom=route.geom,
                        route_name=route.route_name,
                        route_color=route.route_color,
                        route_short_name=route.route_short_name,
                        route_long_name=route.route_long_name,
                    )
                    for route in AppRoutes.objects.filter(file_name="NO_DATA")
                )
            )
            AppAggregatorRoutes.objects.bulk_create(
                list(
                    AppAggregatorRoutes(
                        file_name=file_name,
                        geom=route.geom,
                        frequency=route.frequency,
                        prev_stop_id=route.prev_stop_id,
                        prev_stop_name=route.prev_stop_name,
                        next_stop_id=route.next_stop_id,
                        next_stop_name=route.next_stop_name,
                        agency_id=route.agency_id,
                        agency_name=route.agency_name,
                        service_id=route.service_id,
                        hour=route.hour,
                    )
                    for route in AppAggregatorRoutes.objects.filter(file_name="NO_DATA")
                )
            )
            AppMergedRoutes.objects.bulk_create(
                list(
                    AppMergedRoutes(
                        file_name=file_name,
                        geom=route.geom,
                        route_id=route.route_id,
                        route_name=route.route_name,
                        route_color=route.route_color,
                    )
                    for route in AppMergedRoutes.objects.filter(file_name="NO_DATA")
                )
            )
            AppAggregatorStops.objects.bulk_create(
                list(
                    AppAggregatorStops(
                        file_name=file_name,
                        geom=stop.geom,
                        poly_geom=stop.poly_geom,
                        similar_stop_id=stop.similar_stop_id,
                        similar_stop_name=stop.similar_stop_name,
                        count=stop.count,
                        service_id=stop.service_id,
                        hour=stop.hour,
                    )
                    for stop in AppAggregatorStops.objects.filter(file_name="NO_DATA")
                )
            )
            AppAggregatorStopsBuffer300.objects.bulk_create(
                list(
                    AppAggregatorStopsBuffer300(
                        file_name=file_name,
                        geom=stop.geom,
                        similar_stop_id=stop.similar_stop_id,
                        similar_stop_name=stop.similar_stop_name,
                        count=stop.count,
                    )
                    for stop in AppAggregatorStopsBuffer300.objects.filter(
                        file_name="NO_DATA"
                    )
                )
            )

        print("current_to_copy end", file_name, datetime.now())


def aggr_stop_id_to_stop_ids(request, file_name, stop_id):
    result = stop_id[: stop_id.rfind("_")] if "_" in stop_id else stop_id
    result = stop_id[: stop_id.rfind("_") + 1] if "_" in stop_id else f"{stop_id}_"

    stop_ids = (
        AppStops.objects.filter(stop_id__startswith=result, file_name=file_name)
        .values("stop_id", "stop_name")
        .distinct()
    )

    return HttpResponse(
        json.dumps(list(stop_ids), cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def aggr_stop_id_to_route_ids(request, file_name, stop_id):
    splt_stop_ids = stop_id.split(",")
    parent_ids = [sid[: sid.rfind("_")] if "_" in sid else sid for sid in splt_stop_ids]

    query = Q()
    for parent_id in parent_ids:
        query |= Q(stop_id__startswith=parent_id)

    stop_ids = (
        AppStops.objects.filter(query, file_name=file_name)
        .values_list("stop_id", flat=True)
        .distinct()
    )
    trip_ids = (
        AppStopTimes.objects.filter(stop_id__in=stop_ids, file_name=file_name)
        .values_list("trip_id", flat=True)
        .distinct()
    )
    route_ids = (
        AppTrips.objects.filter(trip_id__in=trip_ids, file_name=file_name)
        .values_list("route_id", flat=True)
        .distinct()
    )
    routes = (
        AppRoutes.objects.filter(route_id__in=route_ids, file_name=file_name)
        .values("route_id", "route_name", "route_short_name", "route_long_name")
        .distinct()
    )
    routes = [
        {
            key: ("" if value in [None, "NaN", "nan", "Nan"] else value)
            for key, value in route.items()
        }
        for route in routes
    ]

    return HttpResponse(
        json.dumps(list(routes), cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_route_service_to_trip_ids(request, file_name, route_id, service_id):
    trips = (
        AppTrips.objects.filter(
            file_name=file_name, route_id=route_id, service_id=service_id
        )
        .values_list("trip_id", flat=True)
        .distinct()
    )

    return HttpResponse(
        json.dumps(
            {"trips": list(trips)},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_route_service_to_jisseki_data(request, file_name, route_id, service_id):
    file_path = f"/.media/{file_name}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)

    filtered_data = excel_data[excel_data["route_id"].isin([route_id])]

    trips = AppTrips.objects.filter(
        file_name=file_name, route_id=route_id, service_id=service_id
    ).values_list("trip_id", flat=True)

    filtered_data = excel_data[excel_data["trip_id"].isin(trips)]

    unique_route_name = filtered_data["route_name"].unique().tolist()
    return HttpResponse(
        json.dumps(
            {
                "route_name": unique_route_name,
                "data": filtered_data[
                    [
                        "stop_sequence",
                        "stop_id",
                        "stop_name",
                        "乗車中人数",
                        "乗車数",
                        "降車数",
                    ]
                ].to_dict(orient="records"),
            },
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_aggregator_routes_info(
    request, file_name, service_id, prev_stop_id, next_stop_id
):
    prev_stop_ids = [
        stops.stop_id
        for stops in AppStops.objects.filter(
            file_name=file_name, stop_id__startswith=prev_stop_id.split("_")[0]
        )
    ]
    next_stop_ids = [
        stops.stop_id
        for stops in AppStops.objects.filter(
            file_name=file_name, stop_id__startswith=next_stop_id.split("_")[0]
        )
    ]

    service_id_to_trip_ids = (
        AppTrips.objects.filter(file_name=file_name, service_id=service_id)
        .values_list("trip_id", flat=True)
        .distinct()
    )

    pn_stop_times_list = pd.DataFrame(
        list(
            AppStopTimes.objects.filter(
                file_name=file_name,
                trip_id__in=service_id_to_trip_ids,
            ).values()
        )
    )
    pn_stop_times_list["next_stop_id"] = pn_stop_times_list["stop_id"].shift(-1)
    pn_stop_times_list["next_stop_sequence"] = pn_stop_times_list[
        "stop_sequence"
    ].shift(-1)
    pn_stop_times_list["next_departure_time"] = pn_stop_times_list[
        "departure_time"
    ].shift(-1)
    pn_stop_times_list["next_trip_id"] = pn_stop_times_list["trip_id"].shift(-1)
    pn_stop_times_list = pn_stop_times_list[
        pn_stop_times_list["trip_id"] == pn_stop_times_list["next_trip_id"]
    ]
    pn_stop_times_list["next_stop_sequence"] = pn_stop_times_list[
        "next_stop_sequence"
    ].astype(int)
    pn_stop_times_list = pn_stop_times_list.drop(
        columns=[
            "arrival_time",
            "next_trip_id",
            "stop_headsign",
            "pickup_type",
            "drop_off_type",
            "timepoint",
        ]
    )
    pn_stop_times_list = pn_stop_times_list.rename(
        columns={
            "stop_id": "prev_stop_id",
            "stop_sequence": "prev_stop_sequence",
            "departure_time": "prev_departure_time",
        }
    )

    filtered_stop_times = pn_stop_times_list[
        pn_stop_times_list["prev_stop_id"].isin(prev_stop_ids)
    ]
    filtered_stop_times = filtered_stop_times[
        filtered_stop_times["next_stop_id"].isin(next_stop_ids)
    ]

    if len(filtered_stop_times) == 0:
        filtered_stop_times = pn_stop_times_list[
            pn_stop_times_list["prev_stop_id"].isin(next_stop_ids)
        ]
        filtered_stop_times = filtered_stop_times[
            filtered_stop_times["next_stop_id"].isin(prev_stop_ids)
        ]

    filtered_prev_next_match_route_ids = AppTrips.objects.filter(
        file_name=file_name,
        trip_id__in={
            item["trip_id"] for item in filtered_stop_times.to_dict("records")
        },
    ).values_list("route_id", flat=True)
    filtered_route_id_counts = dict(
        sorted(
            dict(Counter(filtered_prev_next_match_route_ids)).items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    hour_counts = Counter(
        [
            int(rr["prev_departure_time"].split(":")[0])
            for rr in filtered_stop_times.to_dict("records")
        ]
    )
    routes_dict = {hour: count for hour, count in hour_counts.items()}
    complete_routes = [
        {"hour": hour, "frequency": routes_dict.get(hour, 0)} for hour in range(5, 24)
    ]

    return HttpResponse(
        json.dumps(
            {"route_count": filtered_route_id_counts, "route_graph": complete_routes},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def generate_pdf(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        pdf_orientation = data.get("paperSize")
        image_data = data.get("pict")
        legends = data.get("legend")
        canvas_data = data.get("graph", [])
        backdrop_source = data.get("backdropsource")

        graphtitle = data.get("graphtitle")
        graphinfo1 = data.get("graphinfo1")
        graphinfo2 = data.get("graphinfo2")

        options = {
            "page-size": pdf_orientation,
            "orientation": "Landscape",
            "zoom": "1.0",
            "dpi": "120",
        }

        if pdf_orientation == "A3":
            width = 1900
            height = 1300
            graph_h_height = 50
            graph_label_height = 60
            graph_td_height = (height / 2) - graph_h_height - graph_label_height
            fsize = 1
            lsize = 1.4
            legendpercent = 100
            hval = 3
            graphtitle = "<h2>" + graphtitle + "</h2>"
        else:
            width = 1290
            height = 890
            graph_h_height = 40
            graph_label_height = 55
            graph_td_height = (height / 2) - graph_h_height - graph_label_height
            fsize = 0.8
            lsize = 1
            legendpercent = 80
            hval = 5
            graphtitle = "<h3>" + graphtitle + "</h3>"

        html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset='UTF-8'>
            <style>
            body {{
              width: {width}px;
              height: {height}px;
              margin: 0;
            }}
            table {{
              width: {width}px;
              height: {height}px;
              table-layout: fixed;
              border-collapse: collapse;
            }}
            td {{
              padding: 0;
            }}
            .graphtable {{
              width: {width}px;
              height: {height}px;
              table-layout: fixed;
              border-collapse: collapse;
            }}
            .h_td {{
              height: {graph_h_height}px;
              width: {width}px;
              padding-left: 7px;
            }}
            .label_td {{
              height: {graph_label_height}px;
              width: {width}px;
              padding-left: 7px;
              font-size: {lsize}em;
            }}
            .img_td {{
              width: {width}px;
              height: {graph_td_height}px;
              text-align: left;
              vertical-align: middle;
              padding-left: 7px;
            }}
            .img_td img {{
              max-width: 98%;
              max-height: 98%;
              width: auto;
              height: auto;
              border:1px solid skyblue;
              display: inline-block;
            }}
            .graphtable td label {{
              margin-left: 7px;
              font-size: {fsize * 1.5}em;
            }}
            .left-div {{
              width: 80%;
              height: 100%;
              border-top:1px solid black;
              border-bottom:1px solid black;
              border-left:1px solid black;
            }}
            .right-div {{
              position: relative;
              vertical-align:top;
              margin-top:10px;
              width: 20%;
              height: 100%;
              border:1px solid black;
            }}
            .right-div label {{
              position: absolute;
              bottom: 0;
              left: 0;
              width: 100%;
              margin:3px;
              font-size: {fsize}em;
            }}
            h3, h5 {{
              margin-left: 5px;
            }}
            p {{
              margin-left: 5px;
              font-size:{fsize}em;
            }}
            img {{
              display:block;
              margin-left: 1px;
              max-width: 98%;
              max-height: 98%;
              width: auto;
              height: auto;
              object-fit: contain;
              margin: 0 auto;
            }}
            .legend {{
              margin-left: 5px;
              max-width: {legendpercent}%;
              max-height: {legendpercent}%;
            }}
            </style>
            <script>
              function resizeImage(img) {{
                const container = img.parentNode;
                const containerWidth = container.offsetWidth;
                const containerHeight = container.offsetHeight;
                const imgWidth = img.naturalWidth;
                const imgHeight = img.naturalHeight;
                if (imgWidth / imgHeight > containerWidth / containerHeight) {{
                  img.style.width = '100%';
                  img.style.height = 'auto';
                }} else {{
                  img.style.width = 'auto';
                  img.style.height = '100%';
                }}
              }}
              </script>
            </head>
            <table>
              <tr>
                <td class='left-div'>
                  <img src='%image_data%' alt='Map Image' onload='resizeImage(this)'>
                </td>
                <td class='right-div'>
                  <h{hval}>凡例</h{hval}>
        """

        for legend in legends:
            html += "<p>" + legend["buttonText"] + "<br />"
            html += "<img class='legend' src='" + legend["base64"] + "'></p>"

        if backdrop_source != "":
            if backdrop_source == "国土地理院":
                html += "<label>出典：<a href='https://maps.gsi.go.jp/development/ichiran.html'>国土地理院</a></label>"
            else:
                html += "<label>出典：<a href='https://github.com/gsi-cyberjapan/gsimaps-vector-experiment#readme'>国土地理院ベクトルタイル提供実験</a></label>"

        html += """
                </td>
              </tr>
            </table>
        """

        if canvas_data:

            for i in range(0, len(canvas_data), 2):

                html += "<table>"
                html += f"<tr><td class='h_td'>{graphtitle}</td></tr>"
                for j in range(i, min(i + 2, len(canvas_data) + 1)):
                    if j < len(canvas_data):
                        html += f"<tr><td class='label_td'><label>{graphinfo1[j]}</label><br /><label>{graphinfo2[j]}</label></td></tr>"
                        html += f"<tr><td class='img_td'><img src='{canvas_data[j]}' onload='resizeImage(this)'></td></tr>"
                    else:
                        html += f"<tr><td class='label_td'></td></tr>"
                        html += f"<tr><td class='img_td'></td></tr>"
                html += "</table>"

        html += """
            </body>
            </html>
        """

        try:
            html = html.replace("%image_data%", image_data)

            config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
            pdf = pdfkit.from_string(html, False, options=options, configuration=config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename='map.pdf'"
            return response

        except Exception as e:
            print(f"PDF generation failed: {e}")
            return HttpResponse(status=500)

    else:
        return HttpResponseNotAllowed(["POST"])


def get_jisseki_days(request, service_id):
    file_path = f"/.media/{service_id}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = pd.to_datetime(
        excel_data["date"], format="%Y%m%d", errors="coerce"
    )
    excel_data.dropna(subset=["date"], inplace=True)
    excel_data.drop_duplicates(subset=["date"], inplace=True)
    excel_data.sort_values(by=["date"], inplace=True)

    formatted_dates = []
    dates = []
    for date in excel_data["date"]:
        weekday_mapping = {
            0: "月",
            1: "火",
            2: "水",
            3: "木",
            4: "金",
            5: "土",
            6: "日",
        }
        weekday_num = date.weekday()
        formatted_dates.append(
            date.strftime(f"%Y/%-m/%-d ({weekday_mapping[weekday_num]})")
        )
        dates.append(date.strftime("%Y%m%d"))
    return HttpResponse(
        json.dumps(
            {
                "days": dates,
                "days_f": formatted_dates,
            },
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_jisseki_routes(request, service_id):
    file_path = f"/.media/{service_id}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    routes = excel_data["route_id"].unique().tolist()
    routes_list = []
    for route in routes:
        route_title = ""
        ap_route = AppRoutes.objects.filter(
            route_id=route, file_name=service_id
        ).first()
        if ap_route == None:
            continue
        s_name = ap_route.route_short_name
        l_name = ap_route.route_long_name
        if s_name == None:
            s_name = ""
        if l_name == None:
            l_name = ""
        if s_name == "nan" or s_name == "NaN":
            s_name = ""
        if l_name == "nan" or l_name == "NaN":
            l_name = ""
        route_title = s_name + " " + l_name
        routes_list.append(
            {
                "route_id": route,
                "route_name": route_title,
                "route_short_name": ap_route.route_short_name,
                "route_long_name": ap_route.route_long_name,
            }
        )
    return HttpResponse(
        json.dumps(
            {"routes": routes_list},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_jisseki_directions(request, service_id):
    directions = (
        AppTrips.objects.filter(file_name=service_id).values("direction_id").distinct()
    ).values_list("direction_id", flat=True)
    cleaned_directions = [
        "" if direction is None or str(direction) == "nan" else direction
        for direction in directions
    ]
    return HttpResponse(
        json.dumps(
            {"directions": list(cleaned_directions)},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_datefilter_service_ids(request, session_id, days):
    file_path = f"/.media/{session_id}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = excel_data["date"].astype(str)
    excel_data = excel_data[excel_data["date"] == str(days)]
    unique_trip_ids = excel_data["trip_id"].unique().tolist()
    unique_service_ids = (
        AppTrips.objects.filter(file_name=session_id, trip_id__in=unique_trip_ids)
        .values_list("service_id", flat=True)
        .distinct()
    )
    return HttpResponse(
        json.dumps(
            {"service_ids": list(unique_service_ids)},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_jisseki_graph(request, service_id, days, time, time_range, routes, direction):
    file_path = f"/.media/{service_id}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = excel_data["date"].astype(str)
    excel_data["agency_id"] = excel_data["agency_id"].astype(str)
    excel_data["stop_id"] = excel_data["stop_id"].astype(str)
    excel_data["route_id"] = excel_data["route_id"].astype(str)
    excel_data["stop_sequence"] = excel_data["stop_sequence"].fillna(0).astype(int)

    excel_data = excel_data[excel_data["date"] == str(days)]
    if routes != "all":
        excel_data = excel_data[excel_data["route_id"] == str(routes)]

    st_tr = pd.DataFrame(
        [
            {
                "trip_id": trip.trip_id,
                "direction_id": trip.direction_id,
            }
            for trip in AppTrips.objects.filter(
                file_name=service_id, trip_id__in=excel_data["trip_id"].unique()
            )
        ]
    )
    st_df = pd.DataFrame(
        [
            {
                "trip_id": stop.trip_id,
                "stop_id": stop.stop_id,
                "stop_sequence": int(stop.stop_sequence),
                "departure_time": stop.departure_time,
            }
            for stop in AppStopTimes.objects.filter(
                file_name=service_id, trip_id__in=excel_data["trip_id"].unique()
            )
        ]
    )
    stops_df = pd.DataFrame(
        [
            {
                "stop_id": stop.stop_id,
                "similar_stop_id": stop.similar_stop_id,
                "stop_name": stop.stop_name,
                "latitude": stop.geom.y,
                "longitude": stop.geom.x,
            }
            for stop in AppStops.objects.filter(file_name=service_id)
        ]
    )
    if st_df.empty or stops_df.empty:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )

    centroids = stops_df.groupby("similar_stop_id")[["latitude", "longitude"]].mean()
    centroids.rename(
        columns={"latitude": "centroid_latitude", "longitude": "centroid_longitude"},
        inplace=True,
    )
    stops_df = stops_df.merge(centroids, on="similar_stop_id", how="left")
    st_df = st_df.merge(st_tr, on="trip_id", how="left")
    st_stops = st_df.merge(stops_df, on="stop_id", how="left")
    merged_data = pd.merge(
        st_stops, excel_data, on=["trip_id", "stop_id", "stop_sequence"], how="left"
    )
    merged_data.fillna(
        {"count_geton": 0, "count_getoff": 0, "during_ride": 0}, inplace=True
    )

    merged_data["agency_id"] = merged_data["agency_id"].astype(str)
    merged_data["date"] = merged_data["date"].astype(str)
    merged_data["route_id"] = merged_data["route_id"].astype(str)
    merged_data["date"] = merged_data["date"].astype(str)

    merged_data = merged_data.sort_values(["trip_id", "stop_sequence"])

    merged_data["direction_id"] = (
        merged_data["direction_id"]
        .fillna("0")
        .astype(str)
        .replace(["nan", "None", "NaT", ""], "0", regex=True)
    )

    merged_data["during_ride"] = [0] * len(merged_data)
    merged_data["during_ride"] = merged_data["during_ride"].astype(int)

    merged_data["during_ride"] = (
        merged_data.groupby("trip_id")["count_geton"].cumsum()
        - merged_data.groupby("trip_id")["count_getoff"].cumsum()
    )

    if int(direction) > -1:
        merged_data = merged_data[merged_data["direction_id"] == direction]

    return HttpResponse(
        json.dumps(
            {"data": merged_data.fillna("")},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def delete_csv_file(csv_filepath):
    """
    CSVファイルを削除する関数。

    Args:
        csv_filepath: 削除するCSVファイルのパス
    """

    msg = ""
    try:
        os.remove(csv_filepath)
        msg = "OK"
    except FileNotFoundError:
        msg = f"File '{csv_filepath}' は既に削除されているか、存在しないパスが指定されています。"
    except PermissionError:
        msg = f"File '{csv_filepath}' を削除する権限がありません。"
    except OSError as e:
        msg = f"File '{csv_filepath}' の削除時にエラーが発生しています。\r\n{e}"

    return msg


def jisseki_csv_delete(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    temp_csv_path = os.path.join("/", ".media", f"{session_id}-JISSEKI.csv")

    msg = delete_csv_file(temp_csv_path)

    return JsonResponse(
        {
            "message": msg,
            "session_id": session_id,
        }
    )


def get_route_id_to_name(request, file_name, route_id):
    route = AppRoutes.objects.filter(file_name=file_name, route_id=route_id).first()
    if route == None:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )

    def nan_to_empty(value):
        return "" if value in [None, "NaN", "nan", "Nan"] else value

    route_name = nan_to_empty(route.route_short_name) + nan_to_empty(
        route.route_long_name
    )
    if route_name == None:
        route_name = ""
    return HttpResponse(
        json.dumps(
            {"route_name": route_name},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def upload_od_data(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file was uploaded"}, status=400)

    uploaded_file = request.FILES["file"]
    if not uploaded_file.name.endswith(".csv"):
        return JsonResponse(
            {"error": "Uploaded file must be a CSV archive"}, status=400
        )

    temp_csv_path = os.path.join("/", ".media", f"{session_id}-OD.csv")
    with open(temp_csv_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    msg = ""
    agency_ids = set()
    try:
        with open(temp_csv_path, "r", encoding="utf-8-sig") as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)

            if not header:
                msg = "行ヘッダが無いCSVファイルが指定されています。"
            else:
                required_headers = {
                    "date",
                    "route_id",
                    "stopid_geton",
                    "stopid_getoff",
                    "count",
                    "agency_id",
                }

                processed_header = {
                    h.strip('"').lower().replace('"', "") for h in header
                }

                if required_headers.issubset(processed_header):
                    msg = "OK"
                else:
                    missing_headers = required_headers - processed_header
                    msg = f"ODデータの処理に必要な列({', '.join(missing_headers)})が不足しています。"

            if msg == "OK":
                agency_id_index = [h.lower() for h in header].index("agency_id")
                expected_column_count = len(processed_header)
                ngcount = 0
                for row_number, row in enumerate(reader, start=2):
                    if row:
                        if len(row) != expected_column_count:
                            ngcount += 1
                        else:
                            agency_id = row[agency_id_index]
                            agency_ids.add(agency_id)

                if ngcount > 0:
                    msg = f"所定の列数が無い行が{ngcount}行ありました。ファイルの内容を確認してください。"

    except UnicodeDecodeError:
        msg = "CSVのエンコードがUTF-8であるか確認してください。"
    except csv.Error as e:
        msg = "CSVの読み取り時にエラーが発生しました。ファイルの内容を確認してください。\r\n" + str(
            e
        )
    except FileNotFoundError:
        msg = "CSVファイルを読み込めませんでした。"

    if msg == "OK":
        for agency_id in agency_ids:
            count = AppAggregatorRoutes.objects.filter(
                agency_id=agency_id, file_name=session_id
            ).count()
            if count == 0:
                msg = "読み込み済のGTFSデータのagency_idと合致しないCSVが指定されています。"
                break

        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            data = f.read()

        with open(temp_csv_path, "w", encoding="utf-8") as f:
            f.write(data)

    if msg != "OK":
        print(delete_csv_file(temp_csv_path))

    return JsonResponse(
        {
            "message": msg,
            "session_id": session_id,
        }
    )


def get_od_data_dateonly(request, session_id):
    file_path = f"/.media/{session_id}-OD.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = pd.to_datetime(
        excel_data["date"], format="%Y%m%d", errors="coerce"
    )
    excel_data.dropna(subset=["date"], inplace=True)
    excel_data.drop_duplicates(subset=["date"], inplace=True)
    excel_data.sort_values(by=["date"], inplace=True)

    formatted_dates = []
    dates = []
    for date in excel_data["date"]:
        weekday_mapping = {
            0: "月",
            1: "火",
            2: "水",
            3: "木",
            4: "金",
            5: "土",
            6: "日",
        }
        weekday_num = date.weekday()
        formatted_dates.append(
            date.strftime(f"%Y/%-m/%-d ({weekday_mapping[weekday_num]})")
        )
        dates.append(date.strftime("%Y/%m/%d"))
    return HttpResponse(
        json.dumps(
            {
                "dates": dates,
                "dates_f": formatted_dates,
            },
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_od_data(request, session_id, filter_date):
    file_path = f"/.media/{session_id}-OD.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = pd.to_datetime(excel_data["date"], format="%Y%m%d")
    excel_data = excel_data.fillna("")

    if filter_date != "ALL":
        excel_data = excel_data[excel_data["date"] == filter_date]

    stops_queryset = AppStops.objects.filter(file_name=session_id).values(
        "stop_id", "stop_name"
    )
    stops_df = pd.DataFrame(list(stops_queryset))
    merged_data = pd.merge(
        excel_data,
        stops_df,
        left_on="stopid_geton",
        right_on="stop_id",
        how="left",
    )
    merged_data = merged_data.rename(columns={"stop_name": "stopname_geton"})
    merged_data = pd.merge(
        merged_data,
        stops_df,
        left_on="stopid_getoff",
        right_on="stop_id",
        how="left",
    )
    merged_data = merged_data.rename(columns={"stop_name": "stopname_getoff"})
    merged_data = merged_data.fillna("")

    return HttpResponse(
        json.dumps(
            {"data": merged_data.to_dict(orient="records")},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def od_csv_delete(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    temp_csv_path = os.path.join("/", ".media", f"{session_id}-OD.csv")

    msg = delete_csv_file(temp_csv_path)

    return JsonResponse(
        {
            "message": msg,
            "session_id": session_id,
        }
    )


def load_csv(filepath):
    df = pd.read_csv(filepath)
    df.columns = [col.lower() for col in df.columns]
    return df


def order_service_ids(service_ids):

    weekday = []
    weekday_containing = []
    holiday_containing = []
    others = []

    for sid in service_ids:
        if sid == "平日":
            weekday.append(sid)
        elif "平日" in sid:
            weekday_containing.append(sid)
        elif any(keyword in sid for keyword in ["土", "祝", "祭"]):
            holiday_containing.append(sid)
        else:
            others.append(sid)

    weekday_containing.sort(key=len)
    holiday_containing.sort(key=len)

    ordered_list = weekday + weekday_containing + holiday_containing + others
    return ordered_list


def od_stopid_exists(request, session_id, filter_date):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            stops = data.get("stops")
            geton_or_getoff = data.get("mode")

            csv_file_path = os.path.join("/", ".media", f"{session_id}-OD.csv")
            excel_data = load_csv(csv_file_path)
            excel_data["date"] = pd.to_datetime(excel_data["date"], format="%Y%m%d")
            excel_data = excel_data.fillna("")

            if filter_date != "ALL":
                excel_data = excel_data[excel_data["date"] == filter_date]

            stop_ids = [stop["stopid"] for stop in stops]

            if geton_or_getoff == "0":
                exists = any(excel_data["stopid_geton"].astype(str).isin(stop_ids))
            elif geton_or_getoff == "1":
                exists = any(excel_data["stopid_getoff"].astype(str).isin(stop_ids))
            else:
                exists = False

            return JsonResponse({"exists": exists})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def get_jisseki_routes2(request, service_id, filter_date):
    file_path = f"/.media/{service_id}-JISSEKI.csv"
    if os.path.exists(file_path) is False:
        return HttpResponse(
            json.dumps({}),
            content_type="application/json;charset=utf-8",
        )
    excel_data = load_csv(file_path)
    excel_data["date"] = pd.to_datetime(excel_data["date"], format="%Y%m%d")
    excel_data = excel_data.fillna("")
    if filter_date != "ALL":
        excel_data = excel_data[excel_data["date"] == filter_date]
    trips_df = pd.DataFrame(
        list(AppTrips.objects.filter(file_name=service_id).values("trip_id"))
    )

    stop_times_df = pd.DataFrame(
        list(AppStopTimes.objects.filter(file_name=service_id).values("trip_id"))
    )

    valid_trip_ids = pd.merge(trips_df, stop_times_df, on="trip_id", how="inner")[
        "trip_id"
    ].unique()

    excel_data = excel_data[excel_data["trip_id"].isin(valid_trip_ids)]

    routes = excel_data["route_id"].drop_duplicates().sort_values().tolist()

    routes_list = []
    for route in routes:
        route_title = ""
        ap_route = AppRoutes.objects.filter(
            route_id=route, file_name=service_id
        ).first()
        if ap_route == None:
            continue
        s_name = ap_route.route_short_name
        l_name = ap_route.route_long_name
        if s_name == None:
            s_name = ""
        if l_name == None:
            l_name = ""
        if s_name == "nan" or s_name == "NaN":
            s_name = ""
        if l_name == "nan" or l_name == "NaN":
            l_name = ""
        route_title = s_name + " " + l_name
        routes_list.append(
            {
                "route_id": route,
                "route_name": route_title,
                "route_short_name": ap_route.route_short_name,
                "route_long_name": ap_route.route_long_name,
            }
        )
    return HttpResponse(
        json.dumps(
            {"routes": routes_list},
            cls=MyEncoder,
        ),
        content_type="application/json;charset=utf-8",
    )


def get_aggr_stop_to_stop_ids_with_route_id(
    request, open_key, stop_id, route_id, service_id
):
    if "_" in stop_id:
        result = stop_id.split("_")[0] + "_"

        qs = AppStops.objects.filter(stop_id__startswith=result, file_name=open_key)
    else:
        qs = AppStops.objects.filter(stop_id=stop_id, file_name=open_key)

    trip_qs = AppTrips.objects.filter(service_id=service_id, file_name=open_key)
    if route_id != "-1":
        trip_qs = trip_qs.filter(route_id=route_id)
    trip_ids = trip_qs.values_list("trip_id", flat=True)

    valid_stop_ids = (
        AppStopTimes.objects.filter(trip_id__in=trip_ids)
        .values_list("stop_id", flat=True)
        .distinct()
    )
    qs = qs.filter(stop_id__in=valid_stop_ids)

    stop_ids = qs.values("stop_id", "stop_name").distinct()

    return HttpResponse(
        json.dumps(list(stop_ids), cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def stop_id_to_route_ids(request, file_name, stop_id):

    trip_ids = (
        AppStopTimes.objects.filter(stop_id=stop_id, file_name=file_name)
        .values_list("trip_id", flat=True)
        .distinct()
    )
    route_ids = (
        AppTrips.objects.filter(trip_id__in=trip_ids, file_name=file_name)
        .values_list("route_id", flat=True)
        .distinct()
    )
    routes = (
        AppRoutes.objects.filter(route_id__in=route_ids, file_name=file_name)
        .values("route_id", "route_name", "route_short_name", "route_long_name")
        .distinct()
    )
    routes = [
        {
            key: ("" if value in [None, "NaN", "nan", "Nan"] else value)
            for key, value in route.items()
        }
        for route in routes
    ]

    return HttpResponse(
        json.dumps(list(routes), cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_route_start_end(request, file_name, service_id, route_id):

    if not route_id or not service_id:
        return JsonResponse(
            {"error": "route_id and service_id are required."}, status=400
        )

    try:
        first_trip = (
            AppTrips.objects.filter(
                file_name=file_name, route_id=route_id, service_id=service_id
            )
            .order_by("trip_id")
            .first()
        )

        if not first_trip:
            return JsonResponse(
                {"error": "No trips found for the given route_id and service_id."},
                status=404,
            )

        trip_id = first_trip.trip_id

        try:
            stop_times = AppStopTimes.objects.filter(
                file_name=file_name, trip_id=trip_id
            ).order_by(Cast("stop_sequence", IntegerField()))
        except ValidationError:
            stop_times = AppStopTimes.objects.filter(
                file_name=file_name, trip_id=trip_id
            ).order_by("stop_sequence")

        if not stop_times:
            return JsonResponse(
                {"error": "No stop times found for the given trip_id."}, status=404
            )

        first_stop_id = stop_times.first().stop_id
        last_stop_id = stop_times.last().stop_id

        first_stop = AppStops.objects.get(file_name=file_name, stop_id=first_stop_id)
        last_stop = AppStops.objects.get(file_name=file_name, stop_id=last_stop_id)

        response_data = {
            "first_stop": {"stop_id": first_stop_id, "stop_name": first_stop.stop_name},
            "last_stop": {"stop_id": last_stop_id, "stop_name": last_stop.stop_name},
        }

        return JsonResponse(response_data)

    except AppTrips.DoesNotExist:
        return JsonResponse(
            {"error": "No trips found for the given route_id and service_id."},
            status=404,
        )
    except AppStopTimes.DoesNotExist:
        return JsonResponse(
            {"error": "No stop times found for the given trip_id."}, status=404
        )
    except AppStops.DoesNotExist:
        return JsonResponse(
            {"error": "Stop not found for the given stop_id."}, status=404
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_aggr_stop_to_route_ids_with_service_id(request, file_name, stop_id, service_id):
    splt_stop_ids = stop_id.split(",")

    query = Q()
    for sid in splt_stop_ids:
        if "_" in sid:
            parent_id = sid[: sid.rfind("_")] + "_"
            query |= Q(stop_id__startswith=parent_id)
        else:
            query |= Q(stop_id=sid)

    stop_ids = (
        AppStops.objects.filter(query, file_name=file_name)
        .values_list("stop_id", flat=True)
        .distinct()
    )

    trip_ids = (
        AppStopTimes.objects.filter(stop_id__in=stop_ids, file_name=file_name)
        .values_list("trip_id", flat=True)
        .distinct()
    )

    route_ids = (
        AppTrips.objects.filter(
            trip_id__in=trip_ids, service_id=service_id, file_name=file_name
        )
        .values_list("route_id", flat=True)
        .distinct()
    )

    if not route_ids:
        return HttpResponse(
            json.dumps([], cls=MyEncoder),
            content_type="application/json;charset=utf-8",
        )

    routes = (
        AppRoutes.objects.filter(route_id__in=route_ids, file_name=file_name)
        .values("route_id", "route_name", "route_short_name", "route_long_name")
        .distinct()
    )
    routes = [
        {
            key: ("" if value in [None, "NaN", "nan", "Nan"] else value)
            for key, value in route.items()
        }
        for route in routes
    ]

    return HttpResponse(
        json.dumps(list(routes), cls=MyEncoder),
        content_type="application/json;charset=utf-8",
    )


def get_aggr_stop_id_from_stop_id(request, file_name, stop_id):
    try:
        app_stop = AppStops.objects.filter(stop_id=stop_id, file_name=file_name).first()

        if not app_stop:
            return JsonResponse({"error": "Stop not found"}, status=404)

        aggregator_stop = AppAggregatorStops.objects.filter(
            similar_stop_id=app_stop.similar_stop_id, file_name=file_name
        ).first()

        if aggregator_stop:
            stop_data = {
                "stop_id": app_stop.stop_id,
                "wkt": aggregator_stop.geom.wkt,
                "similar_stop_id": app_stop.similar_stop_id,
            }
            return JsonResponse(stop_data)
        else:
            return JsonResponse({"error": "Aggregator stop not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_route_start_end_jisseki(request, file_name, service_id, route_id, trip_id):

    if not route_id or not service_id:
        return JsonResponse(
            {"error": "route_id and service_id are required."}, status=400
        )

    try:
        if trip_id == "-1":
            first_trip = (
                AppTrips.objects.filter(
                    file_name=file_name, route_id=route_id, service_id=service_id
                )
                .order_by("trip_id")
                .first()
            )

            if not first_trip:
                first_trip = (
                    AppTrips.objects.filter(file_name=file_name, route_id=route_id)
                    .order_by("trip_id")
                    .first()
                )

            if not first_trip:
                return JsonResponse(
                    {"error": "No trips found for the given route_id and service_id."},
                    status=404,
                )

            trip_id = first_trip.trip_id

        try:
            stop_times = AppStopTimes.objects.filter(
                file_name=file_name, trip_id=trip_id
            ).order_by(Cast("stop_sequence", IntegerField()))
        except ValidationError:
            stop_times = AppStopTimes.objects.filter(
                file_name=file_name, trip_id=trip_id
            ).order_by("stop_sequence")

        if not stop_times:
            return JsonResponse(
                {"error": "No stop times found for the given trip_id."}, status=404
            )

        first_stop_id = stop_times.first().stop_id
        last_stop_id = stop_times.last().stop_id

        first_stop = AppStops.objects.get(file_name=file_name, stop_id=first_stop_id)
        last_stop = AppStops.objects.get(file_name=file_name, stop_id=last_stop_id)

        route = AppRoutes.objects.get(file_name=file_name, route_id=route_id)

        response_data = {
            "first_stop": {"stop_id": first_stop_id, "stop_name": first_stop.stop_name},
            "last_stop": {"stop_id": last_stop_id, "stop_name": last_stop.stop_name},
            "route_short_name": route.route_short_name.replace("nan", ""),
            "route_long_name": route.route_long_name.replace("nan", ""),
        }

        return JsonResponse(response_data)

    except AppTrips.DoesNotExist:
        return JsonResponse(
            {"error": "No trips found for the given route_id and service_id."},
            status=404,
        )
    except AppStopTimes.DoesNotExist:
        return JsonResponse(
            {"error": "No stop times found for the given trip_id."}, status=404
        )
    except AppStops.DoesNotExist:
        return JsonResponse(
            {"error": "Stop not found for the given stop_id."}, status=404
        )
    except AppRoutes.DoesNotExist:
        return JsonResponse(
            {"error": "route not found for the given route_id."}, status=404
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_aggr_stop_id_from_stop_name(request, file_name, stop_name):
    try:
        app_stop = AppStops.objects.filter(
            file_name=file_name, stop_name=stop_name
        ).first()

        if not app_stop:
            return JsonResponse({"error": "Stop not found"}, status=404)

        aggregator_stop = AppAggregatorStops.objects.filter(
            similar_stop_id=app_stop.similar_stop_id, file_name=file_name
        ).first()

        if aggregator_stop:
            stop_data = {
                "stop_id": app_stop.stop_id,
                "wkt": aggregator_stop.geom.wkt,
                "similar_stop_id": app_stop.similar_stop_id,
            }
            return JsonResponse(stop_data)
        else:
            return JsonResponse({"error": "Aggregator stop not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
