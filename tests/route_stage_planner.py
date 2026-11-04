#!/usr/bin/env python3
"""Reference GPX physics and constrained stage planner.

This module is a Python reference implementation/specification for a later PHP
port. It deliberately separates route physics from rider physiology. Estimates
are planning outputs, not measured power or a medical performance prediction.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

G = 9.80665
EARTH_M = 6_371_000.0


def haversine_m(a, b):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_M * math.asin(math.sqrt(h))


def moving_median(values, radius):
    out = []
    for i in range(len(values)):
        out.append(statistics.median(values[max(0, i-radius):min(len(values), i+radius+1)]))
    return out


def moving_average(values, radius):
    out = []
    for i in range(len(values)):
        window = values[max(0, i-radius):min(len(values), i+radius+1)]
        out.append(sum(window) / len(window))
    return out


def parse_gpx(path):
    root = ET.parse(path).getroot()
    points = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] in ("trkpt", "rtept"):
            lat, lon = node.attrib.get("lat"), node.attrib.get("lon")
            ele = next((x.text for x in node if x.tag.rsplit("}", 1)[-1] == "ele"), None)
            if lat is None or lon is None:
                continue
            points.append({"lat": float(lat), "lon": float(lon),
                           "ele_m": float(ele) if ele not in (None, "") else None})
    if len(points) < 2:
        raise ValueError("GPX must contain at least two track/route points")
    return points


def analyze_points(points, bin_m=250.0, median_radius=3, smooth_radius=4,
                   elevation_noise_floor_m=1.5):
    """Clean elevation, compute distance/grade and aggregate into fixed-distance bins."""
    if bin_m <= 0:
        raise ValueError("bin_m must be positive")
    raw = [p.get("ele_m") for p in points]
    known = [x for x in raw if x is not None]
    if len(known) < 2:
        raise ValueError("At least two elevation samples are required")
    # Fill isolated missing elevations by nearest known sample; report missing ratio.
    filled = []
    last = known[0]
    for value in raw:
        if value is not None:
            last = value
        filled.append(last)
    med = moving_median(filled, median_radius)
    smooth = moving_average(med, smooth_radius)

    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + haversine_m((a["lat"], a["lon"]), (b["lat"], b["lon"])))
    total = cumulative[-1]
    if total <= 0:
        raise ValueError("GPX distance is zero")

    # Convert irregular trackpoints into distance bins. Elevation at bin boundaries
    # is linearly interpolated from the smoothed profile.
    def interp(distance, values):
        lo, hi = 0, len(cumulative) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < distance:
                lo = mid + 1
            else:
                hi = mid
        j = lo
        if j == 0:
            return values[0]
        d0, d1 = cumulative[j-1], cumulative[j]
        f = 0 if d1 == d0 else (distance-d0)/(d1-d0)
        return values[j-1] + f*(values[j]-values[j-1])

    bins = []
    start = 0.0
    while start < total:
        end = min(total, start + bin_m)
        z0, z1 = interp(start, smooth), interp(end, smooth)
        mid = (start + end) / 2
        # Interpolate coordinate by the same distance index.
        lo, hi = 0, len(cumulative)-1
        while lo < hi:
            m = (lo+hi)//2
            if cumulative[m] < mid: lo=m+1
            else: hi=m
        j=lo
        if j == 0: lat, lon = points[0]["lat"], points[0]["lon"]
        else:
            d0,d1=cumulative[j-1],cumulative[j]
            f=0 if d1==d0 else (mid-d0)/(d1-d0)
            lat=points[j-1]["lat"]+f*(points[j]["lat"]-points[j-1]["lat"])
            lon=points[j-1]["lon"]+f*(points[j]["lon"]-points[j-1]["lon"])
        delta=z1-z0
        # Ignore sub-threshold elevation wiggles at the bin scale.
        if abs(delta) < elevation_noise_floor_m:
            z1=z0
            delta=0.0
        grade=delta/max(end-start,1)
        def coord_at(distance):
            lo2,hi2=0,len(cumulative)-1
            while lo2<hi2:
                m2=(lo2+hi2)//2
                if cumulative[m2]<distance: lo2=m2+1
                else: hi2=m2
            q=lo2
            if q==0: return {"lat":points[0]["lat"],"lon":points[0]["lon"]}
            da,db=cumulative[q-1],cumulative[q]
            f2=0 if db==da else (distance-da)/(db-da)
            return {"lat":points[q-1]["lat"]+f2*(points[q]["lat"]-points[q-1]["lat"]),
                    "lon":points[q-1]["lon"]+f2*(points[q]["lon"]-points[q-1]["lon"])}
        bins.append({"start_m":start,"end_m":end,"distance_m":end-start,
                     "ele_start_m":z0,"ele_end_m":z1,"gain_m":max(0,delta),
                     "loss_m":max(0,-delta),"grade":grade,"lat":lat,"lon":lon,
                     "start_coordinate":coord_at(start),"end_coordinate":coord_at(end)})
        start=end

    raw_gain=sum(max(0, b["ele_m"]-a["ele_m"]) for a,b in zip(points,points[1:])
                 if a.get("ele_m") is not None and b.get("ele_m") is not None)
    smooth_gain=sum(x["gain_m"] for x in bins)
    smooth_loss=sum(x["loss_m"] for x in bins)
    return {
        "distance_km": total/1000,
        "raw_elevation_gain_m": raw_gain,
        "smoothed_elevation_gain_m": smooth_gain,
        "smoothed_elevation_loss_m": smooth_loss,
        "elevation_min_m": min(smooth),
        "elevation_max_m": max(smooth),
        "elevation_missing_fraction": 1-len(known)/len(raw),
        "elevation_method": {"median_radius_points":median_radius,
                             "moving_average_radius_points":smooth_radius,
                             "distance_bin_m":bin_m,
                             "noise_floor_m":elevation_noise_floor_m},
        "bins": bins,
        "start": {"lat":points[0]["lat"],"lon":points[0]["lon"]},
        "finish": {"lat":points[-1]["lat"],"lon":points[-1]["lon"]},
    }


def _power_required(speed_mps, grade, total_mass_kg, crr, cda, rho, wind_mps, drivetrain_eff):
    theta = math.atan(grade)
    rolling = crr * total_mass_kg * G * math.cos(theta)
    gravity = total_mass_kg * G * math.sin(theta)
    relative_air = speed_mps + wind_mps
    aero = 0.5 * rho * cda * relative_air * abs(relative_air)
    wheel_power = (rolling + gravity + aero) * speed_mps
    return max(0.0, wheel_power / drivetrain_eff)


def _solve_speed(power_w, grade, mass, crr, cda, rho, wind, drivetrain_eff,
                 max_speed_mps=25.0):
    if power_w <= 0:
        return 0.5
    lo, hi = 0.3, max_speed_mps
    # If the rider has ample power, return capped speed; otherwise solve P(v)=Pavailable.
    if _power_required(hi, grade, mass, crr, cda, rho, wind, drivetrain_eff) <= power_w:
        return hi
    for _ in range(45):
        mid=(lo+hi)/2
        if _power_required(mid, grade, mass, crr, cda, rho, wind, drivetrain_eff) > power_w:
            hi=mid
        else:
            lo=mid
    return (lo+hi)/2


def _calibrate_power(rider, physics):
    if rider.get("critical_power_w"):
        return float(rider["critical_power_w"]) * float(rider.get("touring_power_fraction", 0.68)), "critical_power"
    if rider.get("ftp_w"):
        # FTP is not identical to critical power; use a conservative configurable fraction.
        return float(rider["ftp_w"]) * float(rider.get("touring_power_fraction", 0.68)), "ftp_proxy"
    if rider.get("typical_speed_kmh"):
        speed=float(rider["typical_speed_kmh"])/3.6
        mass=float(rider["body_mass_kg"])+float(rider.get("bike_mass_kg",14))+float(rider.get("luggage_mass_kg",0))
        # The user's observed typical speed is a calibration point, not a universal constant.
        p=_power_required(speed, float(rider.get("reference_grade",0.0)), mass,
                          physics["crr"], physics["cda"], physics["air_density"],
                          float(rider.get("reference_headwind_mps",0)), physics["drivetrain_efficiency"])
        return p, "typical_speed_calibration"
    raise ValueError("Provide critical_power_w, ftp_w, or typical_speed_kmh plus body_mass_kg")


def _bin_time_and_energy(bin_data, rider, physics, sustainable_power_w):
    mass=float(rider["body_mass_kg"])+float(rider.get("bike_mass_kg",14))+float(rider.get("luggage_mass_kg",0))
    grade=max(-0.25,min(0.25,bin_data["grade"]))
    wind=float(physics.get("headwind_mps",0))
    speed=_solve_speed(sustainable_power_w,grade,mass,physics["crr"],physics["cda"],
                       physics["air_density"],wind,physics["drivetrain_efficiency"])
    # A low gear / technical / surface penalty is explicit and configurable.
    surface_factor=float(physics.get("surface_speed_factors",{}).get(bin_data.get("surface","unknown"),1.0))
    technical_factor=float(bin_data.get("technical_speed_factor",1.0))
    speed*=max(0.25,min(1.0,surface_factor*technical_factor))
    seconds=bin_data["distance_m"]/max(speed,0.5)
    power=_power_required(speed,grade,mass,physics["crr"],physics["cda"],
                          physics["air_density"],wind,physics["drivetrain_efficiency"])
    mechanical_kj=power*seconds/1000
    gross_eff=float(rider.get("gross_efficiency",0.22))
    metabolic_kj=mechanical_kj/max(0.10,min(0.30,gross_eff))
    return seconds,mechanical_kj,metabolic_kj,speed*3.6,power


def plan_stages(route, rider, constraints, physics=None):
    """Split route into exactly N stages, balancing estimated riding time.

    Daily time limits are soft constraints: the planner still returns N stages
    and reports the amount of overrun rather than silently changing trip days.
    """
    physics={**{"crr":0.006,"cda":0.40,"air_density":1.20,
                "drivetrain_efficiency":0.975,"headwind_mps":0.0,
                "surface_speed_factors":{"unknown":1.0,"paved":1.0,"gravel":0.92,
                                         "compacted":0.96,"rough":0.78,"singletrack":0.68}},
             **(physics or {})}
    days=int(constraints["days"])
    if days < 1 or days > len(route["bins"]):
        raise ValueError("days must be between 1 and number of route bins")
    if "body_mass_kg" not in rider:
        raise ValueError("body_mass_kg is required for the physics model")
    power, power_source = _calibrate_power(rider,physics)
    bins=route["bins"]
    per_bin=[]
    for b in bins:
        t,mk,metk,v,p=_bin_time_and_energy(b,rider,physics,power)
        per_bin.append({"seconds":t,"mechanical_kj":mk,"metabolic_kj":metk,
                        "speed_kmh":v,"power_w":p})
    # Prefix sums make the dynamic-programming partition fast and deterministic.
    prefixes={k:[0.0] for k in ("seconds","mechanical_kj","metabolic_kj","distance_m","gain_m","loss_m")}
    for b,x in zip(bins,per_bin):
        vals={"seconds":x["seconds"],"mechanical_kj":x["mechanical_kj"],
              "metabolic_kj":x["metabolic_kj"],"distance_m":b["distance_m"],
              "gain_m":b["gain_m"],"loss_m":b["loss_m"]}
        for k,v in vals.items(): prefixes[k].append(prefixes[k][-1]+v)
    n=len(bins); target=prefixes["seconds"][-1]/days
    max_hours=constraints.get("max_riding_hours_per_day")
    min_hours=constraints.get("min_riding_hours_per_day",0)
    # Candidate cuts every ~1 km, plus endpoints. This keeps the DP practical on long GPX.
    stride=max(1,int(round(1000/max(1,route["elevation_method"]["distance_bin_m"]))))
    cuts=sorted(set([0,n]+list(range(stride,n,stride))))
    # DP state: first j candidate bins partitioned into k non-empty days.
    inf=float("inf"); dp={(0,0):(0.0,[])}
    for k in range(1,days+1):
        for j in cuts:
            if j < k: continue
            best=(inf,None)
            for i in cuts:
                if i >= j or (k-1,i) not in dp: continue
                sec=prefixes["seconds"][j]-prefixes["seconds"][i]
                hrs=sec/3600
                # Balance time (primary objective), with soft penalties for user time limits.
                cost=((hrs-target/3600)/(target/3600))**2
                if max_hours is not None and hrs>float(max_hours):
                    cost += 8.0*((hrs-float(max_hours))/max(1,float(max_hours)))**2
                if hrs<float(min_hours):
                    cost += 1.0*((float(min_hours)-hrs)/max(1,float(min_hours)))**2
                candidate=dp[(k-1,i)][0]+cost
                if candidate<best[0]:
                    best=(candidate,dp[(k-1,i)][1]+[j])
            if best[1] is not None: dp[(k,j)]=best
    if (days,n) not in dp:
        raise ValueError("Could not construct the requested number of non-empty stages")
    cuts_selected=dp[(days,n)][1]
    stages=[]; start=0
    for day,end in enumerate(cuts_selected,1):
        sec=prefixes["seconds"][end]-prefixes["seconds"][start]
        dist=(prefixes["distance_m"][end]-prefixes["distance_m"][start])/1000
        gain=prefixes["gain_m"][end]-prefixes["gain_m"][start]
        loss=prefixes["loss_m"][end]-prefixes["loss_m"][start]
        metabolic=prefixes["metabolic_kj"][end]-prefixes["metabolic_kj"][start]
        mechanical=prefixes["mechanical_kj"][end]-prefixes["mechanical_kj"][start]
        avg_speed=dist/(sec/3600) if sec else 0
        hours=sec/3600
        stage={
            "day":day,"start_distance_km":prefixes["distance_m"][start]/1000,
            "end_distance_km":prefixes["distance_m"][end]/1000,
            "distance_km":dist,"elevation_gain_m":gain,"elevation_loss_m":loss,
            "estimated_moving_hours":hours,"estimated_average_speed_kmh":avg_speed,
            "mechanical_work_kj":mechanical,"estimated_metabolic_energy_kj":metabolic,
            "estimated_metabolic_energy_kcal":metabolic/4.184,
            "start_coordinate":bins[start]["start_coordinate"],
            "end_coordinate":bins[end-1]["end_coordinate"],
            "time_limit_hours":max_hours,
            "time_limit_overrun_hours":max(0,hours-float(max_hours)) if max_hours is not None else None,
            "load_status":"over_user_time_limit" if max_hours is not None and hours>float(max_hours) else "within_user_time_limit",
        }
        stages.append(stage); start=end
    return {
        "model_version":"gpx-physics-stage-planner-0.1",
        "route_summary":{"distance_km":route["distance_km"],
                         "raw_elevation_gain_m":route["raw_elevation_gain_m"],
                         "smoothed_elevation_gain_m":route["smoothed_elevation_gain_m"]},
        "rider_model":{"sustainable_power_estimate_w":power,"power_calibration_source":power_source,
                       "total_system_mass_kg":float(rider["body_mass_kg"])+float(rider.get("bike_mass_kg",14))+float(rider.get("luggage_mass_kg",0)),
                       "gross_efficiency":float(rider.get("gross_efficiency",0.22)),
                       "uncertainty":"high_without_measured_power_or_individual_calibration"},
        "constraints":{"days":days,"max_riding_hours_per_day":max_hours},
        "objective":"balance_estimated_moving_time_with_soft_daily_time_limit_penalty",
        "stages":stages,
        "limitations":["No wind forecast, verified surface map, technical trail classification or stops unless supplied.",
                       "Average speed calibration is context-dependent and cannot identify fitness by itself.",
                       "Energy is a mechanical-to-metabolic estimate using assumed gross efficiency; not a nutrition prescription.",
                       "No physiological fatigue accumulation model is applied yet."],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("gpx")
    parser.add_argument("--days",type=int,required=True)
    parser.add_argument("--body-mass-kg",type=float,required=True)
    parser.add_argument("--bike-mass-kg",type=float,default=14)
    parser.add_argument("--luggage-mass-kg",type=float,default=8)
    parser.add_argument("--typical-speed-kmh",type=float)
    parser.add_argument("--critical-power-w",type=float)
    parser.add_argument("--ftp-w",type=float)
    parser.add_argument("--max-hours",type=float)
    parser.add_argument("--output")
    args=parser.parse_args()
    rider={"body_mass_kg":args.body_mass_kg,"bike_mass_kg":args.bike_mass_kg,
           "luggage_mass_kg":args.luggage_mass_kg}
    for key,val in (("typical_speed_kmh",args.typical_speed_kmh),
                    ("critical_power_w",args.critical_power_w),("ftp_w",args.ftp_w)):
        if val is not None:rider[key]=val
    route=analyze_points(parse_gpx(args.gpx))
    result=plan_stages(route,rider,{"days":args.days,"max_riding_hours_per_day":args.max_hours})
    output=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(output,encoding="utf-8")
    else:print(output)

if __name__=="__main__":
    main()
