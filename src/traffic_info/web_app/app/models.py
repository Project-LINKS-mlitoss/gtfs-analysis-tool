from django.contrib.gis.db import models


class AppAggregatorRoutes(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.LineStringField(blank=True, null=True)
    frequency = models.IntegerField(blank=True, null=True)
    prev_stop_id = models.CharField(max_length=255, blank=True, null=True)
    prev_stop_name = models.CharField(max_length=255, blank=True, null=True)
    next_stop_id = models.CharField(max_length=255, blank=True, null=True)
    next_stop_name = models.CharField(max_length=255, blank=True, null=True)
    agency_id = models.CharField(max_length=255, blank=True, null=True)
    agency_name = models.CharField(max_length=255, blank=True, null=True)
    service_id = models.CharField(max_length=255, blank=True, null=True)
    hour = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_aggregator_routes"


class AppAggregatorStops(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.PointField(blank=True, null=True)
    similar_stop_name = models.CharField(max_length=255, blank=True, null=True)
    similar_stop_id = models.CharField(max_length=255, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)
    poly_geom = models.PolygonField(blank=True, null=True)
    service_id = models.CharField(max_length=255, blank=True, null=True)
    hour = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_aggregator_stops"


class AppAggregatorStopsBuffer300(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.PolygonField(blank=True, null=True)
    similar_stop_name = models.CharField(max_length=255, blank=True, null=True)
    similar_stop_id = models.CharField(max_length=255, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_aggregator_stops_buffer300"


class AppCalendar(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    service_id = models.CharField(max_length=255, blank=True, null=True)
    monday = models.CharField(max_length=255, blank=True, null=True)
    tuesday = models.CharField(max_length=255, blank=True, null=True)
    wednesday = models.CharField(max_length=255, blank=True, null=True)
    thursday = models.CharField(max_length=255, blank=True, null=True)
    friday = models.CharField(max_length=255, blank=True, null=True)
    saturday = models.CharField(max_length=255, blank=True, null=True)
    sunday = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.CharField(max_length=255, blank=True, null=True)
    end_date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_calendar"


class AppCalendarDates(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    service_id = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)
    exception_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_calendar_dates"


class AppChoaza(models.Model):
    id = models.AutoField(primary_key=True)
    geom = models.MultiPolygonField(srid=6668, blank=True, null=True)
    key_code = models.CharField(max_length=11, blank=True, null=True)
    pref = models.CharField(max_length=2, blank=True, null=True)
    s_name = models.CharField(max_length=96, blank=True, null=True)

    class Meta:
        db_table = "app_choaza"


class AppCity(models.Model):
    id = models.BigAutoField(primary_key=True)
    geom = models.MultiPolygonField(srid=6668, blank=True, null=True)
    n03_003 = models.CharField(max_length=20, blank=True, null=True)
    n03_004 = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = "app_city"


class AppFeedInfo(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    feed_publisher_name = models.CharField(max_length=255, blank=True, null=True)
    feed_publisher_url = models.CharField(max_length=255, blank=True, null=True)
    feed_contact_url = models.CharField(max_length=255, blank=True, null=True)
    feed_contact_email = models.CharField(max_length=255, blank=True, null=True)
    feed_lang = models.CharField(max_length=255, blank=True, null=True)
    feed_start_date = models.CharField(max_length=255, blank=True, null=True)
    feed_end_date = models.CharField(max_length=255, blank=True, null=True)
    feed_version = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_feed_info"


class AppHospital(models.Model):
    id = models.BigAutoField(primary_key=True)
    geom = models.PointField(srid=6668, blank=True, null=True)
    p04_001 = models.IntegerField(blank=True, null=True)
    p04_002 = models.CharField(max_length=182, blank=True, null=True)
    pref = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        db_table = "app_hospital"


class AppMergedRoutes(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.MultiLineStringField(blank=True, null=True)
    route_id = models.CharField(max_length=255, blank=True, null=True)
    route_name = models.CharField(max_length=255, blank=True, null=True)
    route_color = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_merged_routes"


class AppMesh(models.Model):
    key_code = models.CharField(primary_key=True, max_length=20)
    geom = models.PolygonField(srid=4612, blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_mesh"


class AppMesh5(models.Model):
    key_code = models.CharField(primary_key=True, max_length=20)
    geom = models.PolygonField(srid=4612, blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_mesh5"


class AppRailroadYusoumitsudo(models.Model):
    gid = models.BigAutoField(primary_key=True)
    geom = models.MultiLineStringField(srid=4326, blank=True, null=True)
    attr09 = models.IntegerField(blank=True, null=True)
    attr10 = models.IntegerField(blank=True, null=True)
    attr11 = models.IntegerField(blank=True, null=True)
    attr12 = models.IntegerField(blank=True, null=True)
    attr13 = models.IntegerField(blank=True, null=True)
    attr14 = models.IntegerField(blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_railroad_yusoumitsudo"


class AppRailroadsection(models.Model):
    id = models.AutoField(primary_key=True)
    geom = models.MultiLineStringField(srid=6668, blank=True, null=True)
    n02_003 = models.CharField(max_length=254, blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_railroadsection"


class AppRoutes(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.MultiLineStringField(blank=True, null=True)
    route_id = models.CharField(max_length=255, blank=True, null=True)
    route_name = models.CharField(max_length=255, blank=True, null=True)
    route_color = models.CharField(max_length=255, blank=True, null=True)
    route_long_name = models.CharField(max_length=255, blank=True, null=True)
    route_short_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_routes"


class AppSchool(models.Model):
    id = models.BigAutoField(primary_key=True)
    geom = models.PointField(srid=6668, blank=True, null=True)
    p29_003 = models.CharField(max_length=5, blank=True, null=True)
    p29_004 = models.CharField(max_length=254, blank=True, null=True)
    pref = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        db_table = "app_school"


class AppStatChoazaAge5Pop(models.Model):
    id = models.BigAutoField(primary_key=True)
    year = models.IntegerField()
    key_code = models.CharField(max_length=20)
    t001082001 = models.IntegerField(blank=True, null=True)
    t001082002 = models.IntegerField(blank=True, null=True)
    t001082003 = models.IntegerField(blank=True, null=True)
    t001082004 = models.IntegerField(blank=True, null=True)
    t001082005 = models.IntegerField(blank=True, null=True)
    t001082006 = models.IntegerField(blank=True, null=True)
    t001082007 = models.IntegerField(blank=True, null=True)
    t001082008 = models.IntegerField(blank=True, null=True)
    t001082009 = models.IntegerField(blank=True, null=True)
    t001082010 = models.IntegerField(blank=True, null=True)
    t001082011 = models.IntegerField(blank=True, null=True)
    t001082012 = models.IntegerField(blank=True, null=True)
    t001082013 = models.IntegerField(blank=True, null=True)
    t001082014 = models.IntegerField(blank=True, null=True)
    t001082015 = models.IntegerField(blank=True, null=True)
    t001082016 = models.IntegerField(blank=True, null=True)
    t001082020 = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_stat_choaza_age5pop"


class AppStatChoazaTransport(models.Model):
    id = models.BigAutoField(primary_key=True)
    year = models.IntegerField(null=False)
    key_code = models.CharField(max_length=20, null=False)
    総数 = models.IntegerField(blank=True, null=True)
    徒歩のみ = models.IntegerField(blank=True, null=True)
    鉄道_電車 = models.IntegerField(blank=True, null=True)
    乗合バス = models.IntegerField(blank=True, null=True)
    勤め先_学校のバス = models.IntegerField(blank=True, null=True)
    自家用車 = models.IntegerField(blank=True, null=True)
    ハイヤー_タクシー = models.IntegerField(blank=True, null=True)
    オートバイ = models.IntegerField(blank=True, null=True)
    自転車 = models.IntegerField(blank=True, null=True)
    その他 = models.IntegerField(blank=True, null=True)
    利用交通手段不詳 = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_stat_choaza_transport"


class AppStatMesh5Pop(models.Model):
    id = models.BigAutoField(primary_key=True)
    year = models.IntegerField(null=False)
    key_code = models.CharField(max_length=20, null=False)
    t001102001 = models.IntegerField(blank=True, null=True)
    t001102013 = models.IntegerField(blank=True, null=True)
    t001102019 = models.IntegerField(blank=True, null=True)
    t001102022 = models.IntegerField(blank=True, null=True)
    t001102028 = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_stat_mesh5_pop"


class AppStatMeshPop(models.Model):
    id = models.BigAutoField(primary_key=True)
    year = models.IntegerField(null=False)
    key_code = models.CharField(max_length=20, null=False)
    t001100001 = models.IntegerField(blank=True, null=True)
    t001100013 = models.IntegerField(blank=True, null=True)
    t001100019 = models.IntegerField(blank=True, null=True)
    t001100022 = models.IntegerField(blank=True, null=True)
    t001100028 = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "app_stat_mesh_pop"


class AppStation(models.Model):
    id = models.AutoField(primary_key=True)
    geom = models.MultiLineStringField(srid=6668, blank=True, null=True)
    n02_005 = models.CharField(max_length=254, blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_station"


class AppStopTimes(models.Model):
    id = models.BigAutoField(primary_key=True)
    trip_id = models.CharField(max_length=255, blank=True, null=True)
    arrival_time = models.CharField(max_length=255, blank=True, null=True)
    departure_time = models.CharField(max_length=255, blank=True, null=True)
    stop_id = models.CharField(max_length=255, blank=True, null=True)
    stop_sequence = models.CharField(max_length=255, blank=True, null=True)
    stop_headsign = models.CharField(max_length=255, blank=True, null=True)
    pickup_type = models.IntegerField(blank=True, null=True)
    drop_off_type = models.IntegerField(blank=True, null=True)
    timepoint = models.IntegerField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_stop_times"


class AppStops(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    geom = models.PointField(blank=True, null=True)
    stop_id = models.CharField(max_length=255, blank=True, null=True)
    stop_name = models.CharField(max_length=255, blank=True, null=True)
    route_ids = models.TextField(blank=True, null=True)
    similar_stop_id = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "app_stops"


class AppTrips(models.Model):
    id = models.BigAutoField(primary_key=True)
    route_id = models.CharField(max_length=255, blank=True, null=True)
    service_id = models.CharField(max_length=255, blank=True, null=True)
    trip_id = models.CharField(max_length=255, blank=True, null=True)
    trip_headsign = models.CharField(max_length=255, blank=True, null=True)
    block_id = models.CharField(max_length=255, blank=True, null=True)
    trip_short_name = models.CharField(max_length=255, blank=True, null=True)
    direction_id = models.CharField(max_length=255, blank=True, null=True)
    shape_id = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_trips"


class AppUnkouHonsuKukan2024(models.Model):
    id = models.BigAutoField(primary_key=True)
    geom = models.LineStringField(srid=4326, blank=True, null=True)
    順方向運行本数2024 = models.IntegerField(blank=True, null=True)
    逆方向運行本数2024 = models.IntegerField(blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_unkouhonsu_kukan2024"


class AppUnkouHonsuKukan2024R(models.Model):
    id = models.BigAutoField(primary_key=True)
    geom = models.LineStringField(srid=4326, blank=True, null=True)
    順方向運行本数2024 = models.IntegerField(blank=True, null=True)
    逆方向運行本数2024 = models.IntegerField(blank=True, null=True)
    prefs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "app_unkouhonsu_kukan2024r"


