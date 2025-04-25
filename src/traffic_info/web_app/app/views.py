from datetime import date
import hashlib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from app.apis import current_to_copy


@login_required
def index(request):
    if not request.session.session_key:
        request.session.save()
    comb_key = request.session.session_key + settings.SECRET_KEY
    unique_id = hashlib.sha256(comb_key.encode()).hexdigest()
    return render(request, "index.html", {"open_key": unique_id})


@login_required
def gtfs_list(request):
    if "open_key" not in request.GET:
        return redirect("/")

    params = {
        "today": date.today().strftime("%Y-%m-%d"),
        "oid": request.GET["open_key"],
    }
    return render(request, "gtfs_list.html", params)


@login_required
def map(request):
    if "open_key" not in request.GET:
        return redirect("/")

    pref = ""
    if "pref" in request.session:
        pref = request.session["pref"]
    else:
        pref = "16"

    selData = []
    if "selData" in request.session:
        selData = request.session["selData"]
    else:
        selData = [
            {
                "download-url": "https://api.gtfs-data.jp/v2/organizations/chitetsu/feeds/chitetsubus/files/feed.zip?uid=31da622a-49d9-42e2-b560-e29fbb1c755f",
                "organization": "富山地方鉄道",
                "feed": "富山地方鉄道バス",
                "pref": "富山県",
                "from_date": "2024-04-01",
                "to_date": "2025-03-31",
                "license": "CC0 1.0",
            }
        ]

    params = {
        "today": date.today().strftime("%Y-%m-%d"),
        "oid": request.GET["open_key"],
        "pref": pref,
        "selData": selData,
    }
    current_to_copy(request.GET["open_key"])
    return render(request, "map.html", params)


@login_required
def uphistory(request):
    return render(request, "uphistory.html")
