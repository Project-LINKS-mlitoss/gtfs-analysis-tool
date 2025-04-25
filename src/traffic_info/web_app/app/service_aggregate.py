import datetime
import pandas as pd
from gtfs_parser.gtfs import GTFS


class ServiceAggregator:
    def __init__(
        self,
        gtfs: GTFS,
        no_unify_stops=False,
        delimiter="",
        max_distance_degree=0.003,
        yyyymmdd="",
        begin_time="",
        end_time="",
        service_id="",
    ):
        self.gtfs = gtfs
        self.stop_times = ServiceAggregator.__filter_stop_times(
            self.gtfs, yyyymmdd, begin_time, end_time, service_id
        )
        similar_results = ServiceAggregator.__unify_similar_stops(
            self.gtfs.stops, delimiter, max_distance_degree
        )
        self.similar_stops, self.stop_relations = similar_results

    def __filter_stop_times(gtfs, yyyymmdd, begin_time, end_time, service_id):
        filtered_stop_times = gtfs.stop_times.copy()
        filtered_stop_times = filtered_stop_times.merge(
            gtfs.trips[["trip_id", "service_id"]], on="trip_id"
        )

        def parse_time(time_str):
            try:
                return datetime.datetime.strptime(time_str, "%H:%M:%S").time()
            except ValueError:
                if time_str == "24:00:00":
                    return datetime.time(0, 0, 0)
                return None

        filtered_stop_times["departure_time"] = filtered_stop_times[
            "departure_time"
        ].apply(parse_time)
        if begin_time:
            begin_time_obj = parse_time(
                str(begin_time).zfill(6)[:2]
                + ":"
                + str(begin_time).zfill(6)[2:4]
                + ":"
                + str(begin_time).zfill(6)[4:]
            )
        if end_time:
            end_time_obj = parse_time(
                str(end_time).zfill(6)[:2]
                + ":"
                + str(end_time).zfill(6)[2:4]
                + ":"
                + str(end_time).zfill(6)[4:]
            )

        if begin_time and end_time:
            filtered_stop_times = filtered_stop_times[
                ~filtered_stop_times["departure_time"].isnull()
            ]

            filtered_stop_times = filtered_stop_times[
                (filtered_stop_times["departure_time"] >= begin_time_obj)
                & (filtered_stop_times["departure_time"] <= end_time_obj)
            ]
        if service_id:
            filtered_stop_times = filtered_stop_times[
                filtered_stop_times["service_id"] == service_id
            ]

        return filtered_stop_times

    def __unify_similar_stops(stops, delimiter, max_distance_degree):
        child_similar_stop = None
        child_id_pair = None

        if "location_type" in stops.columns:
            child_similar_stop, child_id_pair = ServiceAggregator.__unify_child_stops(
                stops
            )

            solo_stops = stops[
                ~stops["stop_id"].isin(child_id_pair["stop_id"])
                & (stops["location_type"] == 0)
            ]
        else:
            solo_stops = stops

        solo_similar_stops, solo_id_pair = ServiceAggregator.__unify_solo_stops(
            solo_stops, delimiter, max_distance_degree
        )

        return pd.concat([child_similar_stop, solo_similar_stops]), pd.concat(
            [child_id_pair, solo_id_pair]
        )

    def __get_trips_on_a_date(gtfs, yyyymmdd: str):
        """
        get trips are on service on a date.

        Args:
            yyyymmdd (str): [description]

        Returns:
            [type]: [description]
        """
        day_of_week = (
            datetime.date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
            .strftime("%A")
            .lower()
        )

        if gtfs.calendar is None:
            service_ids_on = pd.Series(name="service_id", dtype=str)
        else:
            calendar = gtfs.calendar.astype({"start_date": int, "end_date": int})
            calendar = calendar[calendar[day_of_week] == "1"]
            calendar = calendar.query(
                f"start_date <= {int(yyyymmdd)} and {int(yyyymmdd)} <= end_date",
                engine="python",
            )
            service_ids_on = calendar["service_id"]

        if gtfs.calendar_dates is not None:
            filtered = gtfs.calendar_dates[gtfs.calendar_dates["date"] == yyyymmdd][
                ["service_id", "exception_type"]
            ]
            to_be_removed_service_ids = filtered[filtered["exception_type"] == "2"][
                "service_id"
            ]
            to_be_appended_services_ids = filtered[filtered["exception_type"] == "1"][
                "service_id"
            ]

            service_ids_on = service_ids_on[
                ~service_ids_on.isin(to_be_removed_service_ids)
            ]
            service_ids_on = pd.concat([service_ids_on, to_be_appended_services_ids])

        trips_in_services = gtfs.trips[gtfs.trips["service_id"].isin(service_ids_on)]

        return trips_in_services["trip_id"]

    def __unify_child_stops(stops):
        child_id_pair = stops[
            stops["parent_station"].isin(stops["stop_id"])
            & (stops["location_type"] == 0)
        ][["stop_id", "parent_station"]]

        child_id_pair.rename(
            columns={"parent_station": "similar_stop_id"}, inplace=True
        )

        similar_ids = child_id_pair["similar_stop_id"].unique()

        similar_stops = stops[stops["stop_id"].isin(similar_ids)][
            ["stop_id", "stop_name", "stop_lon", "stop_lat"]
        ]

        similar_stops["similar_stops_centroid"] = similar_stops[
            ["stop_lon", "stop_lat"]
        ].values.tolist()
        similar_stops.drop(columns=["stop_lon", "stop_lat"], inplace=True)

        similar_stops.rename(
            columns={
                "stop_id": "similar_stop_id",
                "stop_name": "similar_stop_name",
            },
            inplace=True,
        )

        return similar_stops, child_id_pair

    def __unify_solo_stops(solo_stops, delimiter, max_distance_degree):
        delimited_id_pair = []
        if delimiter:
            stop_id_delimited = (
                solo_stops["stop_id"]
                .str.split(delimiter)
                .str[0]
                .rename("similar_stop_id")
            )
            delimited_id_pair = pd.concat(
                [solo_stops["stop_id"], stop_id_delimited], axis=1
            )[solo_stops["stop_id"] != stop_id_delimited]
        if len(delimited_id_pair) == len(solo_stops):
            solo_id_pair = delimited_id_pair
        else:
            if len(delimited_id_pair) > 0:
                undelimited_stops = solo_stops[
                    ~solo_stops["stop_id"].isin(delimited_id_pair["stop_id"])
                ]
            else:
                undelimited_stops = solo_stops
            near_id_pair = ServiceAggregator.__calc_near_id_pair(
                undelimited_stops, max_distance_degree
            )

            if len(delimited_id_pair) == 0:
                solo_id_pair = near_id_pair
            else:
                solo_id_pair = pd.concat([delimited_id_pair, near_id_pair])

        if len(solo_id_pair) == 0:
            return None, None

        solo_stops_with_similar = pd.merge(solo_stops, solo_id_pair, on="stop_id")
        solo_similar_stops = (
            solo_stops_with_similar.groupby("similar_stop_id")
            .agg({"stop_name": "min", "stop_lon": "mean", "stop_lat": "mean"})
            .reset_index()
        )
        solo_similar_stops.rename(
            columns={"stop_name": "similar_stop_name"}, inplace=True
        )
        solo_similar_stops["similar_stops_centroid"] = solo_similar_stops[
            ["stop_lon", "stop_lat"]
        ].values.tolist()
        solo_similar_stops.drop(columns=["stop_lon", "stop_lat"], inplace=True)
        return solo_similar_stops, solo_id_pair

    def __calc_near_id_pair(solo_stops, max_distance_degree):
        stop_matrix = pd.merge(
            solo_stops, solo_stops, on="stop_name", suffixes=("", "_r")
        )
        near_matrix = stop_matrix[
            (stop_matrix["stop_lon"] - stop_matrix["stop_lon_r"]) ** 2
            + (stop_matrix["stop_lat"] - stop_matrix["stop_lat_r"]) ** 2
            <= max_distance_degree**2
        ]

        near_matrix = near_matrix[["stop_id", "stop_id_r"]]
        near_id_pair = near_matrix.groupby("stop_id").min().reset_index()

        near_id_pair = ServiceAggregator.__join_near_group(near_id_pair)
        return near_id_pair.rename(columns={"stop_id_r": "similar_stop_id"})

    def __join_near_group(near_id_pair):
        for i in range(5):
            leaf_pair = near_id_pair.query("stop_id != stop_id_r").rename(
                columns={"stop_id": "stop_id_r", "stop_id_r": "stop_id_r2"}
            )
            sub_pair = pd.merge(near_id_pair, leaf_pair, on="stop_id_r").drop(
                columns=["stop_id_r"]
            )
            if len(sub_pair) == 0:
                break
            mod_id_trio = pd.merge(near_id_pair, sub_pair, on="stop_id", how="left")
            mod_id_trio.loc[~mod_id_trio["stop_id_r2"].isna(), "stop_id_r"] = (
                mod_id_trio["stop_id_r2"]
            )
            near_id_pair = mod_id_trio.drop(columns=["stop_id_r2"])

        return near_id_pair

    def read_interpolated_stops(self):
        stop_pass_count = self.stop_times.groupby("stop_id").size().rename("count")
        stop_pass_count = pd.merge(
            self.stop_relations, stop_pass_count, on="stop_id", how="left"
        )
        similar_pass_count = (
            stop_pass_count.groupby("similar_stop_id").sum("count").astype(int)
        )
        similar_stop_summary = self.similar_stops.merge(
            similar_pass_count, on="similar_stop_id"
        )

        stop_dicts = similar_stop_summary.to_dict(orient="records")

        return [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": stop["similar_stops_centroid"],
                },
                "properties": {
                    "similar_stop_name": stop["similar_stop_name"],
                    "similar_stop_id": stop["similar_stop_id"],
                    "count": stop["count"],
                },
            }
            for stop in stop_dicts
        ]

    def read_route_frequency(self):
        stop_times_df = pd.merge(
            self.stop_times[["trip_id", "stop_sequence", "stop_id"]],
            self.stop_relations,
            on="stop_id",
        )
        trip_agency_df = pd.merge(
            self.gtfs.trips[["trip_id", "route_id"]],
            self.gtfs.routes[["route_id", "agency_id"]],
            on="route_id",
        )
        stop_times_df = pd.merge(stop_times_df, trip_agency_df, on="trip_id")
        stop_times_df = stop_times_df.sort_values(["trip_id", "stop_sequence"])

        stop_times_df["next_stop_id"] = stop_times_df["similar_stop_id"].shift(-1)
        stop_times_df["next_trip_id"] = stop_times_df["trip_id"].shift(-1)
        stop_times_df = stop_times_df[
            stop_times_df["trip_id"] == stop_times_df["next_trip_id"]
        ]
        path_df = stop_times_df.rename(columns={"similar_stop_id": "prev_stop_id"})

        path_freq_sr = path_df.groupby(
            ["agency_id", "prev_stop_id", "next_stop_id"]
        ).size()
        path_freq_sr.name = "frequency"
        path_freq_df = path_freq_sr.reset_index()

        for order in ["prev", "next"]:
            path_freq_df = pd.merge(
                path_freq_df,
                self.similar_stops,
                left_on=f"{order}_stop_id",
                right_on="similar_stop_id",
            )
            path_freq_df.rename(
                columns={
                    "similar_stop_name": f"{order}_stop_name",
                    "similar_stops_centroid": f"{order}_similar_stops_centroid",
                },
                inplace=True,
            )
            path_freq_df.drop(columns="similar_stop_id", inplace=True)

        path_freq_df = pd.merge(
            path_freq_df, self.gtfs.agency[["agency_id", "agency_name"]], on="agency_id"
        )
        path_freq_dict = path_freq_df.to_dict(orient="records")
        return [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": (
                        path["prev_similar_stops_centroid"],
                        path["next_similar_stops_centroid"],
                    ),
                },
                "properties": {
                    "frequency": path["frequency"],
                    "prev_stop_id": path["prev_stop_id"],
                    "prev_stop_name": path["prev_stop_name"],
                    "next_stop_id": path["next_stop_id"],
                    "next_stop_name": path["next_stop_name"],
                    "agency_id": path["agency_id"],
                    "agency_name": path["agency_name"],
                },
            }
            for path in path_freq_dict
        ]
