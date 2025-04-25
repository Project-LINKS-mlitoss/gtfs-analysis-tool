from datetime import datetime, date
import json
import os
import shutil
import zipfile
import re
import requests
import math
import osmnx as ox
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import shape
from shapely.ops import linemerge, unary_union

from celery import current_task
from celery_progress.backend import ProgressRecorder
import gtfs_parser
from gtfs_parser.gtfs import GTFS
from gtfs_parser.parse import read_routes, read_stops
from gtfs_parser.aggregate import Aggregator
from app.service_aggregate import ServiceAggregator

from django.core.management import call_command
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiLineString, LineString
from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.measure import D
from django.db.models import Func, Q, F, Sum
from django.db import connection
from django.db import transaction

import psycopg2
import psycopg2.extras

from app.models import (
    AppAggregatorRoutes,
    AppAggregatorStops,
    AppAggregatorStopsBuffer300,
    AppRoutes,
    AppMergedRoutes,
    AppStopTimes,
    AppStops,
    AppTrips,
    AppCalendar,
    AppCalendarDates,
    AppFeedInfo,
)

import csv
import copy


def convert_gtfs(log_obj, session_id, zip_file):
    file_path = os.path.join(zip_file)

    if zip_file.endswith(".zip"):
        unzip_folder = os.path.join(os.path.splitext(zip_file)[0])
        os.makedirs(unzip_folder, exist_ok=True)

        try:
            print("Unzipping", zip_file)
            log_obj.write(f"\n   - Unzipping {zip_file}")
            log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(unzip_folder)

            print("Read GTFS")
            log_obj.write(f"\n   - Read GTFS")
            log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            gtfs = gtfs_parser.GTFSFactory(unzip_folder)

            print("Import GTFS to PostGIS")
            log_obj.write(f"\n   - Import GTFS to PostGIS")
            log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            error_messages = set()
            import_gtfs_to_postgis(
                gtfs,
                session_id,
                error_messages,
                "",
                None,
                0,
                1,
                {"organization": "", "feed": ""},
            )
            if error_messages:
                log_obj.write(f"\n  - GTFS変換エラー: " + ", ".join(error_messages))
                log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(e)
            log_obj.write(f"\n   - Error: {e}")
            log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        finally:
            shutil.rmtree(unzip_folder)


def extract_system(trip_id):
    match = re.search(r"系統.*", trip_id)
    if match:
        return match.group(0)
    else:
        return None


def make_gtfs_graph(G_osm, log_obj, stops, stop_times):
    print("AddNodes")
    log_obj.write(f"\n   - - AddNodes")
    log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for _, stop in stops.iterrows():
        G_osm.add_node(
            stop["stop_id"],
            y=float(stop["stop_lat"]),
            x=float(stop["stop_lon"]),
            street_count=4,
        )

    print("AddEdges")
    log_obj.write(f"\n   - - AddEdges")
    log_obj.write(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    stop_times["system"] = stop_times["trip_id"].apply(extract_system)
    for trip_id, trip_group in stop_times.groupby("system"):
        print(f"TripID: {trip_id}")
        log_obj.write(f"\n   - - - TripID: {trip_id}")
        sorted_trip_group = trip_group.sort_values(by="stop_sequence")
        for i in range(len(sorted_trip_group) - 1):
            stop_a = sorted_trip_group.iloc[i]
            stop_b = sorted_trip_group.iloc[i + 1]

            node_a = stops.loc[stops["stop_id"] == stop_a["stop_id"]].iloc[0]
            node_b = stops.loc[stops["stop_id"] == stop_b["stop_id"]].iloc[0]
            node_osm = ox.nearest_nodes(
                G_osm, float(node_a["stop_lon"]), float(node_a["stop_lat"])
            )

            if G_osm.has_edge(stop_a["stop_id"], stop_b["stop_id"]) or G_osm.has_edge(
                stop_b["stop_id"], stop_a["stop_id"]
            ):
                continue

            G_osm.add_edge(
                stop_a["stop_id"],
                stop_b["stop_id"],
                osmid=trip_id,
                oneway=False,
                lanes="4",
                ref=f"{stop_a['stop_id']};{stop_b['stop_id']}",
                name=stop_a["stop_headsign"],
                highway="trunk",
                access="yes",
                reversed=True,
                length=geodesic(
                    (node_a["stop_lat"], node_a["stop_lon"]),
                    (node_b["stop_lat"], node_b["stop_lon"]),
                ).meters,
            )

            G_osm.add_edge(
                stop_a["stop_id"],
                node_osm,
                osmid=trip_id,
                oneway=False,
                lanes="4",
                ref=f"{stop_a['stop_id']};{node_osm}",
                name=stop_a["stop_headsign"],
                highway="trunk",
                access="yes",
                reversed=True,
                length=0,
            )
    return G_osm


def import_gtfs_to_postgis(
    gtfs,
    session_id,
    error_messages,
    gDate,
    progress_recorder,
    process_count,
    max_process_count,
    selInfo,
):
    fileCount = math.floor(process_count / 10) + 1
    fileInfo = (
        str(fileCount)
        + "番目のファイル["
        + selInfo["organization"]
        + " "
        + selInfo["feed"]
        + "]\t"
    )

    def replace_nan_field(field):
        if field == "NaN" or field == "nan":
            return ""
        return field

    print("import_gtfs_to_postgis")
    print(" >>> session_id", session_id)
    print(" >>> gDate", gDate)
    print(" >>> stops data", len(gtfs.stops))
    print(" >>> routes data", len(gtfs.routes))
    print(" >>> stop_times data", len(gtfs.stop_times))

    print("- Import Feed Info", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "feed_info.txtの処理中です．．．",
        )
        process_count += 1
    try:
        feed_info_records = gtfs.feed_info.to_dict("records")
        feed_info_objects = [
            AppFeedInfo(
                file_name=session_id,
                feed_publisher_name=(
                    feedinfo["feed_publisher_name"]
                    if "feed_publisher_name" in gtfs.feed_info
                    else ""
                ),
                feed_publisher_url=(
                    feedinfo["feed_publisher_url"]
                    if "feed_publisher_url" in gtfs.feed_info
                    else ""
                ),
                feed_contact_url=(
                    feedinfo["feed_contact_url"]
                    if "feed_contact_url" in gtfs.feed_info
                    else ""
                ),
                feed_contact_email=(
                    feedinfo["feed_contact_email"]
                    if "feed_contact_email" in gtfs.feed_info
                    else ""
                ),
                feed_lang=(
                    feedinfo["feed_lang"] if "feed_lang" in gtfs.feed_info else ""
                ),
                feed_start_date=(
                    feedinfo["feed_start_date"]
                    if "feed_start_date" in gtfs.feed_info
                    else ""
                ),
                feed_end_date=(
                    feedinfo["feed_end_date"]
                    if "feed_end_date" in gtfs.feed_info
                    else ""
                ),
                feed_version=(
                    feedinfo["feed_version"] if "feed_version" in gtfs.feed_info else ""
                ),
            )
            for feedinfo in feed_info_records
        ]
        AppFeedInfo.objects.bulk_create(feed_info_objects)
    except Exception as e:
        print(e)
        error_messages.add("feed_info.txtの処理でエラーが発生しています")

    print("- Import Calendars", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "calendars.txtの処理中です．．．",
        )
        process_count += 1
    try:
        calendars_records = gtfs.calendar.to_dict("records")
        calendars_objects = [
            AppCalendar(
                file_name=session_id,
                service_id=calendar["service_id"],
                monday=calendar["monday"],
                tuesday=calendar["tuesday"],
                wednesday=calendar["wednesday"],
                thursday=calendar["thursday"],
                friday=calendar["friday"],
                saturday=calendar["saturday"],
                sunday=calendar["sunday"],
                start_date=calendar["start_date"],
                end_date=calendar["end_date"],
            )
            for calendar in calendars_records
        ]
        AppCalendar.objects.bulk_create(calendars_objects)
    except Exception as e:
        print(e)
        error_messages.add("calendars.txtの処理でエラーが発生しています")

    print("- Import Calendar Dates", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "calendar_dates.txtの処理中です．．．",
        )
        process_count += 1
    try:
        if gtfs.calendar_dates is not None:
            calendar_dates_records = gtfs.calendar_dates.to_dict("records")
            calendar_dates_objects = [
                AppCalendarDates(
                    file_name=session_id,
                    service_id=calendar_date["service_id"],
                    date=calendar_date["date"],
                    exception_type=calendar_date["exception_type"],
                )
                for calendar_date in calendar_dates_records
            ]
            AppCalendarDates.objects.bulk_create(calendar_dates_objects)
    except Exception as e:
        print(e)
        error_messages.add("calendar_dates.txtの処理でエラーが発生しています")

    print("- Import Trips", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count, max_process_count, fileInfo + "trips.txtの処理中です．．．"
        )
        process_count += 1
    try:
        trips_records = gtfs.trips.to_dict("records")
        trips_objects = [
            AppTrips(
                file_name=session_id,
                route_id=trip["route_id"],
                service_id=trip["service_id"],
                trip_id=trip["trip_id"],
                trip_headsign=trip["trip_headsign"],
                block_id=replace_nan_field(trip["block_id"]),
                trip_short_name=(
                    replace_nan_field(trip["trip_short_name"])
                    if "trip_short_name" in gtfs.trips
                    else ""
                ),
                direction_id=(
                    replace_nan_field(trip["direction_id"])
                    if "direction_id" in gtfs.trips
                    else ""
                ),
                shape_id=(
                    replace_nan_field(trip["shape_id"])
                    if "shape_id" in gtfs.trips
                    else ""
                ),
            )
            for trip in trips_records
        ]
        AppTrips.objects.bulk_create(trips_objects)
    except Exception as e:
        print(e)
        error_messages.add("trips.txtの処理でエラーが発生しています")

    print("- Import Stop Times", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "stop_times.txtの処理中です．．．",
        )
        process_count += 1

    gtfs.stop_times["pickup_type"] = gtfs.stop_times.get(
        "pickup_type", pd.Series(0, index=gtfs.stop_times.index)
    ).fillna(0)
    gtfs.stop_times["drop_off_type"] = gtfs.stop_times.get(
        "drop_off_type", pd.Series(0, index=gtfs.stop_times.index)
    ).fillna(0)
    timepointexists = False
    if "timepoint" in gtfs.stop_times:
        gtfs.stop_times["timepoint"] = pd.to_numeric(
            gtfs.stop_times["timepoint"], errors="coerce"
        ).fillna(0)
        timepointexists = True

    try:
        stop_times_records = gtfs.stop_times.to_dict("records")
        stop_times_objects = [
            AppStopTimes(
                file_name=session_id,
                trip_id=st["trip_id"],
                arrival_time=st["arrival_time"],
                departure_time=st["departure_time"],
                stop_id=st["stop_id"],
                stop_sequence=st["stop_sequence"],
                stop_headsign=st["stop_headsign"],
                pickup_type=st["pickup_type"],
                drop_off_type=st["drop_off_type"],
                timepoint=st["timepoint"] if timepointexists else 0,
            )
            for st in stop_times_records
        ]
        AppStopTimes.objects.bulk_create(stop_times_objects)
    except Exception as e:
        print(e)
        error_messages.add("stop_times.txtの処理でエラーが発生しています")

    print("- Aggregate Stops Buffer300", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "stops.txtの300mバッファの作成処理中です．．．",
        )
        process_count += 1

    aggr_gtfs = ServiceAggregator(gtfs, yyyymmdd=gDate)
    try:
        aggregated_stops = aggr_gtfs.read_interpolated_stops()
        AppAggregatorStopsBuffer300.objects.bulk_create(
            [
                AppAggregatorStopsBuffer300(
                    geom=GEOSGeometry(json.dumps(stop["geometry"])).buffer(300),
                    file_name=session_id,
                    similar_stop_name=stop["properties"]["similar_stop_name"].replace(
                        "　", " "
                    ),
                    similar_stop_id=stop["properties"]["similar_stop_id"],
                    count=safe_number_conversion(stop["properties"]["count"]),
                )
                for stop in aggregated_stops
            ]
        )
    except Exception as e:
        print(e)
        error_messages.add("stops.txtの集計処理でエラーが発生しています")

    print("- Import Stops", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count, max_process_count, fileInfo + "stops.txtの処理中です．．．"
        )
        process_count += 1
    try:
        AppStops.objects.bulk_create(
            [
                AppStops(
                    geom=GEOSGeometry(json.dumps(stop["geometry"])),
                    file_name=session_id,
                    stop_id=stop["properties"]["stop_id"],
                    stop_name=stop["properties"]["stop_name"].replace("　", " "),
                    route_ids=stop["properties"]["route_ids"],
                )
                for stop in read_stops(gtfs)
            ]
        )

        stops_list = AppStops.objects.filter(file_name=session_id)
        delimiter = "_"
        delimited_stops = []
        for stop in stops_list:
            stop_id_delimited = stop.stop_id.split(delimiter)
            delimited_stops.append(
                {
                    "stop_id": stop.stop_id,
                    "stop_name": stop.stop_name,
                    "delimited": stop_id_delimited[0],
                }
            )
        grouped_stops = pd.DataFrame(delimited_stops).groupby("delimited")
        for group_name, group in grouped_stops:
            AppStops.objects.filter(
                file_name=session_id, stop_id__in=group["stop_id"].tolist()
            ).update(similar_stop_id=group["stop_id"].min())

    except Exception as e:
        print(e)
        error_messages.add("stops.txtの処理でエラーが発生しています")

    print("- Import Routes", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count, max_process_count, fileInfo + "routes.txtの処理中です．．．"
        )
        process_count += 1
    p_routes = None
    try:
        p_routes = read_routes(gtfs, ignore_shapes=False)
        if any(route["properties"]["route_id"] is None for route in p_routes):
            p_routes = read_routes(gtfs, ignore_shapes=True)
    except Exception:
        p_routes = read_routes(gtfs, ignore_shapes=True)

    if p_routes:

        def get_random_route_color(route, seed):
            color_map = {
                0: "ff6f61",
                1: "ffb400",
                2: "ffd700",
                3: "28a745",
                4: "17a2b8",
                5: "7427f2",
                6: "e83e8c",
                7: "fec61f",
                8: "fd7e14",
                9: "007bff",
            }
            route["properties"]["route_color"] = color_map.get(seed, "ff0000")
            return route["properties"]["route_color"]

        def line_string_to_multi_line_string(line_string):
            if isinstance(line_string, LineString):
                return MultiLineString(line_string)
            return line_string

        def search_short_name(route_id):
            return gtfs.routes[gtfs.routes["route_id"] == route_id][
                "route_short_name"
            ].iloc[0]

        def search_long_name(route_id):
            return gtfs.routes[gtfs.routes["route_id"] == route_id][
                "route_long_name"
            ].iloc[0]

        try:
            AppRoutes.objects.bulk_create(
                [
                    AppRoutes(
                        geom=line_string_to_multi_line_string(
                            GEOSGeometry(json.dumps(route["geometry"]))
                        ),
                        file_name=session_id,
                        route_id=route["properties"]["route_id"],
                        route_name=route["properties"]["route_name"],
                        route_color=get_random_route_color(route, idx % 10),
                        route_short_name=search_short_name(
                            route["properties"]["route_id"]
                        ),
                        route_long_name=search_long_name(
                            route["properties"]["route_id"]
                        ),
                    )
                    for idx, route in enumerate(p_routes)
                ]
            )
        except Exception as e:
            print(e)
            error_messages.add("routes.txtの処理でエラーが発生しています")

        print("- Import Merged Routes", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if progress_recorder:
            progress_recorder.set_progress(
                process_count,
                max_process_count,
                fileInfo + "routes.txtのマージ処理中です．．．",
            )
            process_count += 1
        grouped_routes = {}
        try:
            for route in p_routes:
                geom = shape(route["geometry"])
                geometrys = []
                if geom.geom_type == "LineString":
                    geometrys.append(LineString(list(geom.coords)))
                elif geom.geom_type == "MultiLineString":
                    for geom_line in geom.geoms:
                        geometrys.append(LineString(list(geom_line.coords)))
                else:
                    error_messages.add(f"Unexpected geometry type: {geom.geom_type}")

                for geometry in geometrys:
                    group_id = route["properties"]["route_name"]
                    if group_id not in grouped_routes:
                        grouped_routes[group_id] = {
                            "route_name": group_id,
                            "geometries": [geometry],
                            "route_color": route["properties"]["route_color"],
                        }
                    else:
                        grouped_routes[group_id]["geometries"].append(geometry)
        except Exception as e:
            print(e)
            error_messages.add("routes.txtのマージ処理でエラーが発生しています")

        try:
            AppMergedRoutes.objects.bulk_create(
                [
                    AppMergedRoutes(
                        geom=MultiLineString(data["geometries"]).ewkb.hex(),
                        file_name=session_id,
                        route_id=group_id,
                        route_name=data["route_name"],
                        route_color=data["route_color"],
                    )
                    for group_id, data in grouped_routes.items()
                ]
            )
        except Exception as e:
            print(e)
            error_messages.add("routes.txtのマージ処理でエラーが発生しています")

    print(
        "- Service_id Aggregate Stops/Routes",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    if progress_recorder:
        progress_recorder.set_progress(
            process_count,
            max_process_count,
            fileInfo + "service_id別の処理中です．．．",
        )
        process_count += 1
    try:
        aggregated_stops = []
        aggregated_routes = []
        for service_id in gtfs.trips["service_id"].unique():
            aggregator_si = ServiceAggregator(gtfs, service_id=service_id)

            a_stops = aggregator_si.read_interpolated_stops()
            aggregated_stops.extend(
                [
                    AppAggregatorStops(
                        geom=GEOSGeometry(json.dumps(a_stop["geometry"])),
                        file_name=session_id,
                        similar_stop_name=a_stop["properties"][
                            "similar_stop_name"
                        ].replace("　", " "),
                        similar_stop_id=a_stop["properties"]["similar_stop_id"],
                        count=safe_number_conversion(a_stop["properties"]["count"]),
                        service_id=service_id,
                        hour=-1,
                    )
                    for a_stop in a_stops
                ]
            )

            a_routes = aggregator_si.read_route_frequency()
            aggregated_routes.extend(
                [
                    AppAggregatorRoutes(
                        geom=GEOSGeometry(json.dumps(a_route["geometry"])),
                        file_name=session_id,
                        frequency=a_route["properties"]["frequency"],
                        prev_stop_id=a_route["properties"]["prev_stop_id"],
                        prev_stop_name=a_route["properties"]["prev_stop_name"].replace(
                            "　", " "
                        ),
                        next_stop_id=a_route["properties"]["next_stop_id"],
                        next_stop_name=a_route["properties"]["next_stop_name"].replace(
                            "　", " "
                        ),
                        agency_id=a_route["properties"]["agency_id"],
                        agency_name=a_route["properties"]["agency_name"].replace(
                            "　", " "
                        ),
                        service_id=service_id,
                        hour=-1,
                    )
                    for a_route in a_routes
                ]
            )

            for time in range(0, 24):
                bt = int(str(time).zfill(2) + "0000")
                et = int(str(time + 1).zfill(2) + "0000")
                aggregator_si_time = ServiceAggregator(
                    gtfs,
                    begin_time=str(bt),
                    end_time=str(et),
                    service_id=service_id,
                )
                at_stops = aggregator_si_time.read_interpolated_stops()
                aggregated_stops.extend(
                    [
                        AppAggregatorStops(
                            geom=GEOSGeometry(json.dumps(a_stop["geometry"])),
                            file_name=session_id,
                            similar_stop_name=a_stop["properties"][
                                "similar_stop_name"
                            ].replace("　", " "),
                            similar_stop_id=a_stop["properties"]["similar_stop_id"],
                            count=safe_number_conversion(a_stop["properties"]["count"]),
                            service_id=service_id,
                            hour=time,
                        )
                        for a_stop in at_stops
                    ]
                )
                at_routes = aggregator_si_time.read_route_frequency()
                aggregated_routes.extend(
                    [
                        AppAggregatorRoutes(
                            geom=GEOSGeometry(json.dumps(a_route["geometry"])),
                            file_name=session_id,
                            frequency=a_route["properties"]["frequency"],
                            prev_stop_id=a_route["properties"]["prev_stop_id"],
                            prev_stop_name=a_route["properties"][
                                "prev_stop_name"
                            ].replace("　", " "),
                            next_stop_id=a_route["properties"]["next_stop_id"],
                            next_stop_name=a_route["properties"][
                                "next_stop_name"
                            ].replace("　", " "),
                            agency_id=a_route["properties"]["agency_id"],
                            agency_name=a_route["properties"]["agency_name"].replace(
                                "　", " "
                            ),
                            service_id=service_id,
                            hour=time,
                        )
                        for a_route in at_routes
                    ]
                )

        AppAggregatorStops.objects.bulk_create(aggregated_stops)
        AppAggregatorRoutes.objects.bulk_create(aggregated_routes)

    except Exception as e:
        error_messages.add("service_id別の集計処理でエラーが発生しています")
        print(e)

    print("- gtfs to database done", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if progress_recorder:
        progress_recorder.set_progress(
            process_count, max_process_count, fileInfo + "処理終了しました．．．"
        )
        process_count += 1


def safe_number_conversion(value):
    try:
        float_value = float(value)
        if np.isnan(float_value):
            return 0
        return float_value
    except (ValueError, TypeError):
        return 0


def gtfs_data_delete(session_id):
    AppStopTimes.objects.filter(file_name=session_id).delete()
    AppStops.objects.filter(file_name=session_id).delete()
    AppRoutes.objects.filter(file_name=session_id).delete()
    AppMergedRoutes.objects.filter(file_name=session_id).delete()
    AppAggregatorStops.objects.filter(file_name=session_id).delete()
    AppAggregatorStopsBuffer300.objects.filter(file_name=session_id).delete()
    AppAggregatorRoutes.objects.filter(file_name=session_id).delete()
    AppTrips.objects.filter(file_name=session_id).delete()
    AppCalendar.objects.filter(file_name=session_id).delete()
    AppCalendarDates.objects.filter(file_name=session_id).delete()
    AppFeedInfo.objects.filter(file_name=session_id).delete()


def download_gtfs_data(
    url,
    session_id,
    gDate,
    progress_recorder=None,
    process_count=0,
    max_process_count=1,
    selInfo={"organization": "nodate", "feed": "nodate"},
):
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join("/", ".media", session_id + "-GTFS.zip")
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"GTFSデータをダウンロードしました: {session_id}")
        convert_gtfs_to_postgis(
            file_path,
            session_id,
            gDate,
            progress_recorder,
            process_count,
            max_process_count,
            selInfo,
        )
    else:
        print(f"ダウンロードエラー: {response.status_code}")


def convert_gtfs_to_postgis(
    file_path,
    session_id,
    gDate,
    progress_recorder=None,
    process_count=0,
    max_process_count=1,
    selInfo={"organization": "", "feed": ""},
):
    unzip_folder = os.path.join("/", ".media", os.path.splitext(file_path)[0])
    if os.path.exists(unzip_folder):
        shutil.rmtree(unzip_folder)
    os.makedirs(unzip_folder, exist_ok=True)

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(unzip_folder)

    error_messages = set()

    remove_bom_from_csv_files(unzip_folder)

    translations_file_path = os.path.join(unzip_folder, "translations.txt")

    if os.path.exists(translations_file_path):
        processed_rows = []
        with open(translations_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            headers_len = len(headers)
            translation_index = headers.index(
                "translation"
            )

            processed_rows.append(headers)

            for row in reader:
                row_len = len(row)
                if row_len == headers_len:
                    processed_rows.append(row)
                elif headers_len < row_len:
                    combined_column = ",".join(
                        row[translation_index:-3]
                    )
                    row[translation_index:-3] = [
                        f"{combined_column}"
                    ]
                    processed_rows.append(row)
                else:
                    print(f"Unexpected row length: {row_len}")
                    error_messages.add(
                        "translation.txtにヘッダ行と列数が一致しない行があります"
                    )

        with open(translations_file_path, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(processed_rows)

    try:
        gtfs = gtfs_parser.GTFSFactory(unzip_folder)
        import_gtfs_to_postgis(
            gtfs,
            session_id,
            error_messages,
            gDate,
            progress_recorder,
            process_count,
            max_process_count,
            selInfo,
        )
    except Exception as e:
        print("GTFS read error")
        raise Exception("GTFS変換エラー: " + ", ".join(error_messages))
    finally:
        os.remove(file_path)

    if error_messages:
        print("GTFS変換エラー: " + ", ".join(error_messages))
        raise Exception("GTFS変換エラー: " + ", ".join(error_messages))


def remove_bom_from_csv_files(folder_path):
    """
    指定フォルダ内の全てのCSVファイルからBOMを取り除き、上書き保存する

    Args:
    folder_path (str): CSVファイルが格納されているフォルダのパス
    """
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            remove_bom_and_overwrite(file_path)


def remove_bom_and_overwrite(csv_file):
    """
    CSVファイルからBOMを取り除き、同じファイルに上書き保存する

    Args:
        csv_file (str): CSVファイルのパス
    """
    with open(csv_file, "r", encoding="utf-8-sig") as f:
        data = f.read()

    with open(csv_file, "w", encoding="utf-8") as f:
        f.write(data)
