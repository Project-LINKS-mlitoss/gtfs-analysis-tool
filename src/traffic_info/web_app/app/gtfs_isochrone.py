import datetime
import json

from collections import namedtuple
import geopandas
import os
import numpy as np
import pandas as pd
import jpholiday

from app.models import (
    AppStops,
    AppStopTimes,
    AppTrips,
    AppCalendar,
    AppRoutes,
    AppCalendarDates,
)
from django.db.models import F, Func, FloatField


EARTH_RADIUS_METERS = 6_371_000
WALKING_SPEED_M_S = 1.10


def compute_isochrone(session_id, lat, lon, start_datetime):
    all_geojsons = []
    max_duration_seconds = [5400, 4800, 4200, 3600, 3000, 2400, 1800, 1200, 600]

    data = load_prepared_data(session_id)
    for d_seconds in max_duration_seconds:
        geojson = compute_isochrone_with_data(data, lat, lon, start_datetime, d_seconds)
        for feature in geojson:
            if "id" in feature:
                del feature["id"]
            feature["properties"]["time"] = d_seconds
        all_geojsons.append(geojson[0])
    return all_geojsons


def load_prepared_data(session_id):
    Data = namedtuple(
        "Data",
        [
            "stops",
            "stop_times",
            "trips",
            "calendar",
            "routes",
            "calendar_dates",
            "durations",
            "trips_dates",
        ],
    )
    dataframes = {}
    queryset_mappings = {
        "stops": AppStops.objects.filter(file_name=session_id).values(),
        "stop_times": AppStopTimes.objects.filter(file_name=session_id).values(),
        "trips": AppTrips.objects.filter(file_name=session_id).values(),
        "calendar": AppCalendar.objects.filter(file_name=session_id).values(),
        "routes": AppRoutes.objects.filter(file_name=session_id).values(),
        "calendar_dates": AppCalendarDates.objects.filter(
            file_name=session_id
        ).values(),
    }
    for field, queryset in queryset_mappings.items():
        try:
            dataframes[field] = (
                pd.DataFrame(list(queryset)) if queryset.exists() else pd.DataFrame()
            )
        except Exception as e:
            print(f"Error converting {field}: {e}")

    class AsLat(Func):
        function = "ST_Y"
        output_field = FloatField()

    class AsLon(Func):
        function = "ST_X"
        output_field = FloatField()

    stops_queryset = (
        AppStops.objects.filter(file_name=session_id)
        .annotate(stop_lat=AsLat(F("geom")), stop_lon=AsLon(F("geom")))
        .values("stop_id", "stop_lat", "stop_lon")
    )
    dataframes["stops"] = pd.DataFrame(list(stops_queryset))

    try:
        feed_start_date = pd.to_datetime(
            dataframes["calendar"]["start_date"].min(), format="%Y%m%d"
        )
        feed_end_date = pd.to_datetime(
            dataframes["calendar"]["end_date"].max(), format="%Y%m%d"
        )

        date_range = pd.date_range(start=feed_start_date, end=feed_end_date)
        calendar_dates = []
        for date in date_range:
            if jpholiday.is_holiday(date) or date.weekday() >= 5:
                calendar_dates.append(
                    {
                        "service_id": "平日",
                        "date": date.strftime("%Y%m%d"),
                        "exception_type": 2,
                    }
                )
                calendar_dates.append(
                    {
                        "service_id": "土日祝",
                        "date": date.strftime("%Y%m%d"),
                        "exception_type": 1,
                    }
                )
            else:
                calendar_dates.append(
                    {
                        "service_id": "平日",
                        "date": date.strftime("%Y%m%d"),
                        "exception_type": 1,
                    }
                )
                calendar_dates.append(
                    {
                        "service_id": "土日祝",
                        "date": date.strftime("%Y%m%d"),
                        "exception_type": 2,
                    }
                )
        new_calendar_dates = pd.DataFrame(calendar_dates)
        dataframes["calendar_dates"] = new_calendar_dates

    except Exception as e:
        print(f"Error: Unable to create new calendar_dates.txt file. {e}")

    dataframes["durations"] = prepare_stop_walk_duration(dataframes["stops"])
    dataframes["trips_dates"] = prepare_trips_dates(
        dataframes["trips"], dataframes["calendar_dates"], dataframes["routes"]
    )

    return Data(**dataframes)


def compute_isochrone_with_data(data, lat, lon, start_datetime, max_duration_seconds):
    end_datetime = start_datetime + datetime.timedelta(seconds=max_duration_seconds)

    data = prepare_data_for_query(data, start_datetime, end_datetime)
    points = compute_arrival_points(data, lat, lon, start_datetime, end_datetime)
    distances = walk_from_points(points, end_datetime)
    return build_isochrone_from_points(distances)


def compute_arrival_points(data, lat, lon, start_datetime, end_datetime):
    stops = data.stops
    stoptimes = data.stoptimes.sort_values(by=["trip_id", "datetime"])
    stoptimes_columns = stoptimes.columns
    durations = data.durations

    reached_stops = walk_from_origin(start_datetime, lat, lon, stops)
    reached_stops = reached_stops.loc[
        reached_stops["arrival_datetime"] < end_datetime,
        ["stop_id", "arrival_datetime"],
    ]

    for num_changement in range(4):
        reachable_stoptimes = stoptimes.merge(reached_stops, on="stop_id", how="left")
        reachable_stoptimes["reachable"] = np.nan
        reachable_stoptimes.loc[
            reachable_stoptimes["datetime"] > reachable_stoptimes["arrival_datetime"],
            "reachable",
        ] = 1
        group_reachable_stoptimes = reachable_stoptimes.groupby("trip_id")[
            "reachable"
        ].ffill()
        reachable_stoptimes["reachable"] = group_reachable_stoptimes

        valids = reachable_stoptimes["reachable"].notnull()
        stoptimes = reachable_stoptimes.loc[~valids, stoptimes_columns]
        reachable_stoptimes = reachable_stoptimes.loc[valids]

        if len(reachable_stoptimes) == 0:
            break

        reachable_stoptimes["arrival_datetime"] = reachable_stoptimes.loc[
            :, ["arrival_datetime", "datetime"]
        ].min(axis=1)
        reached_stops = (
            pd.concat(
                [reached_stops, reachable_stoptimes[["stop_id", "arrival_datetime"]]]
            )
            .sort_values(by="arrival_datetime")
            .drop_duplicates(subset=["stop_id"], keep="first")
        )

        reached_stops, has_not_changed = walk_from_stops(
            reached_stops, durations, end_datetime
        )

        if has_not_changed:
            break

    reached_stops = reached_stops.merge(stops, how="left", on="stop_id").rename(
        columns={"stop_lat": "lat", "stop_lon": "lon"}
    )
    return pd.concat(
        [
            reached_stops,
            pd.DataFrame(
                {
                    "stop_id": ["origin"],
                    "lat": [lat],
                    "lon": [lon],
                    "arrival_datetime": [start_datetime],
                }
            ),
        ],
        ignore_index=True,
    )


def walk_from_origin(start_datetime, lat, lon, stops):
    reached_stops = stops.copy()
    reached_stops["arrival_datetime"] = arrival_datetime(
        start_datetime, lat, stops["stop_lat"], lon, stops["stop_lon"]
    )

    return reached_stops


def arrival_datetime(start_datetime, lat1, lat2, lon1, lon2):
    walk_duration_seconds = walk_duration(lat1, lat2, lon1, lon2)
    return walk_duration_seconds + start_datetime


def walk_duration(lat1, lat2, lon1, lon2):
    distances_meters = distance_meters(lat1, lat2, lon1, lon2)
    return pd.to_timedelta(distances_meters / WALKING_SPEED_M_S, unit="s").round("S")


def distance_meters(lat1, lat2, lon1, lon2):
    lat1, lat2, lon1, lon2 = [np.radians(col) for col in [lat1, lat2, lon1, lon2]]
    return (
        2
        * EARTH_RADIUS_METERS
        * np.arcsin(
            np.sqrt(
                np.sin((lat1 - lat2) / 2) ** 2
                + np.cos(lat1) * np.cos(lat2) * (np.sin((lon1 - lon2) / 2) ** 2)
            )
        )
    )


def prepare_data_for_query(data, start_datetime, end_datetime):
    trips_dates = data.trips_dates.copy()
    trips_dates["date"] = pd.to_datetime(trips_dates["date"], format="%Y%m%d")
    trips_dates = trips_dates.loc[trips_dates["date"].dt.date == start_datetime.date()]

    valid_routes = []
    valid_routes.append(3)
    valid_routes.append(0)

    stoptimes = data.stop_times.copy()
    stoptimes = stoptimes.merge(trips_dates, on="trip_id", how="inner")
    stoptimes["datetime"] = pd.to_datetime(
        stoptimes["date"].dt.strftime("%Y%m%d") + " " + stoptimes["arrival_time"]
    )
    stoptimes = stoptimes.loc[
        (stoptimes["datetime"] > start_datetime)
        & (stoptimes["datetime"] < end_datetime),
        ["trip_id", "stop_id", "datetime"],
    ]

    stops = data.stops.copy()
    stops = stops.loc[stops["stop_id"].isin(stoptimes["stop_id"].unique())]

    durations = data.durations.copy()
    durations = durations.loc[
        (durations["walk_duration"] < (end_datetime - start_datetime))
        & durations["stop_id_from"].isin(stops["stop_id"])
        & durations["stop_id_to"].isin(stops["stop_id"])
    ]

    n_data = namedtuple("Data", ["stops", "durations", "trips_dates", "stoptimes"])
    return n_data(
        stops=stops, durations=durations, trips_dates=trips_dates, stoptimes=stoptimes
    )


def prepare_stop_walk_duration(stops):
    stops = stops.copy()
    stops["fake"] = True
    distances = stops.merge(stops, on="fake", suffixes=["_from", "_to"])
    lat1, lat2, lon1, lon2 = map(
        lambda col: distances[col],
        ["stop_lat_from", "stop_lat_to", "stop_lon_from", "stop_lon_to"],
    )

    distances["walk_duration"] = walk_duration(lat1, lat2, lon1, lon2)

    return distances.loc[
        distances["stop_id_from"] != distances["stop_id_to"],
        ["stop_id_from", "stop_id_to", "walk_duration"],
    ]


def prepare_trips_dates(trips, calendar_dates, routes):
    return (
        trips.merge(calendar_dates, on="service_id")
        .merge(routes, on="route_id")
        .loc[:, ["trip_id", "date"]]
    )


def walk_from_points(points, end_datetime):
    points["duration_seconds"] = (end_datetime - points["arrival_datetime"]).dt.seconds
    points["walking_distance_m"] = points["duration_seconds"] * WALKING_SPEED_M_S
    return points.loc[:, ["lat", "lon", "walking_distance_m"]]


def walk_from_stops(reached_stops, durations, end_datetime):
    new = reached_stops.merge(
        durations, how="left", left_on="stop_id", right_on="stop_id_from"
    )
    new["arrival_datetime"] = new["arrival_datetime"] + new["walk_duration"]

    new = (
        pd.concat(
            [
                new.loc[
                    new["arrival_datetime"] < end_datetime,
                    ["stop_id_to", "arrival_datetime"],
                ].rename(columns={"stop_id_to": "stop_id"}),
                reached_stops,
            ]
        )
        .sort_values(by="arrival_datetime")
        .drop_duplicates(subset="stop_id", keep="first")
    )

    has_not_changed = (len(new) == len(reached_stops)) & new.equals(reached_stops)

    return new, has_not_changed


def build_isochrone_from_points(distances):
    points = geopandas.GeoDataFrame(
        distances,
        geometry=geopandas.points_from_xy(distances["lon"], distances["lat"]),
    )

    mapping_CRS = "EPSG:3857"
    lonlat_CRS = "EPSG:4326"
    points = points.set_crs(lonlat_CRS)
    gdf = points.to_crs(mapping_CRS)
    gdf = gdf.buffer(gdf["walking_distance_m"])
    shape = gdf.unary_union
    shape = geopandas.GeoSeries(shape, crs=mapping_CRS)
    shape = shape.to_crs(lonlat_CRS)
    return json.loads(shape.to_json())["features"]
