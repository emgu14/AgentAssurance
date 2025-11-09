#!/usr/bin/env python3
"""
shapes_to_geojson.py
Convertit shapes.txt (ou en fallback stop_times+stops) en lines.geojson utilisable par Leaflet.

Usage:
python shapes_to_geojson.py --gtfs ./gtfs --out public/data/lines.geojson
python shapes_to_geojson.py --gtfs ./gtfs --out public/data/lines.geojson --routes 12 45
"""

import os
import json
import argparse
import pandas as pd


def load_csv_safe(path, dtype=None):
    """Charge un CSV si le fichier existe, sinon retourne None"""
    if os.path.exists(path):
        return pd.read_csv(path, dtype=dtype)
    return None


def shapes_to_geojson(gtfs_folder, out_path, include_routes=None):
    """Convertit shapes.txt ou fallback stop_times+stops en GeoJSON"""
    shapes_path = os.path.join(gtfs_folder, 'shapes.txt')
    trips_path = os.path.join(gtfs_folder, 'trips.txt')
    routes_path = os.path.join(gtfs_folder, 'routes.txt')
    stops_path = os.path.join(gtfs_folder, 'stops.txt')
    stop_times_path = os.path.join(gtfs_folder, 'stop_times.txt')

    # ✅ Cas normal : utiliser shapes.txt
    if os.path.exists(shapes_path):
        shapes = pd.read_csv(shapes_path, dtype={'shape_id': str})
        if 'shape_pt_sequence' in shapes.columns:
            shapes['shape_pt_sequence'] = shapes['shape_pt_sequence'].astype(int)

        trips = load_csv_safe(trips_path, dtype={'trip_id': str, 'shape_id': str, 'route_id': str})
        routes = load_csv_safe(routes_path, dtype={'route_id': str})
        routes_map = {}
        if routes is not None and 'route_id' in routes.columns:
            routes_map = routes.set_index('route_id').to_dict('index')

        features = []
        for shape_id, group in shapes.groupby('shape_id'):
            group_sorted = group.sort_values('shape_pt_sequence') if 'shape_pt_sequence' in group.columns else group
            coords = [[float(row['shape_pt_lon']), float(row['shape_pt_lat'])]
                      for _, row in group_sorted.iterrows()
                      if not pd.isna(row['shape_pt_lon']) and not pd.isna(row['shape_pt_lat'])]
            if len(coords) < 2:
                continue

            # Lier aux routes
            route_ids = []
            if trips is not None and 'shape_id' in trips.columns:
                rids = trips[trips['shape_id'] == shape_id]['route_id'].dropna().unique().tolist()
                route_ids = [str(r) for r in rids]

            if include_routes and not set(route_ids).intersection(set(include_routes)):
                continue

            props = {'shape_id': str(shape_id), 'route_ids': route_ids}

            if route_ids and routes_map:
                meta = routes_map.get(route_ids[0])
                if meta:
                    props.update({k: meta[k] for k in ['route_short_name', 'route_long_name', 'route_type'] if k in meta})

            # Ajouter trip_id pour correspondre à route_probs
            if trips is not None and 'shape_id' in trips.columns and 'trip_id' in trips.columns:
                trip_ids = trips[trips['shape_id'] == shape_id]['trip_id'].dropna().tolist()
                if trip_ids:
                    props['trip_id'] = trip_ids[0]  # Prendre le premier trip_id comme référence

            features.append({
                'type': 'Feature',
                'geometry': {'type': 'LineString', 'coordinates': coords},
                'properties': props
            })

        fc = {'type': 'FeatureCollection', 'features': features}
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
        print(f"✅ OK -> {out_path} ({len(features)} features)")
        return

    # ⚠️ Fallback si shapes.txt n’existe pas
    print("⚠️ shapes.txt non trouvé. Fallback : stop_times.txt + stops.txt")
    if not (os.path.exists(stop_times_path) and os.path.exists(stops_path) and os.path.exists(trips_path)):
        raise FileNotFoundError("shapes.txt absent et stop_times/stops/trips manquants. Impossible de générer GeoJSON.")

    stop_times = pd.read_csv(stop_times_path, dtype={'trip_id': str, 'stop_id': str})
    stops = pd.read_csv(stops_path, dtype={'stop_id': str})
    trips = pd.read_csv(trips_path, dtype={'trip_id': str, 'route_id': str})
    stops_map = stops.set_index('stop_id').to_dict('index')

    features = []
    for trip_id, grp in stop_times.groupby('trip_id'):
        grp_sorted = grp.sort_values('stop_sequence') if 'stop_sequence' in grp.columns else grp
        coords = []
        for stop_id in grp_sorted['stop_id']:
            s = stops_map.get(stop_id)
            if not s:
                continue
            lat, lon = s.get('stop_lat'), s.get('stop_lon')
            if pd.isna(lat) or pd.isna(lon):
                continue
            coords.append([float(lon), float(lat)])
        if len(coords) < 2:
            continue

        route_id = trips.loc[trips['trip_id'] == trip_id, 'route_id'].values
        route_id = str(route_id[0]) if len(route_id) else None
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': coords},
            'properties': {'trip_id': trip_id, 'route_id': route_id}
        })

    fc = {'type': 'FeatureCollection', 'features': features}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    print(f"Fallback OK -> {out_path} ({len(features)} features)")


def main():
    parser = argparse.ArgumentParser(description="GTFS shapes -> GeoJSON lines")
    parser.add_argument('--gtfs', required=True, help='dossier contenant les fichiers GTFS')
    parser.add_argument('--out', required=True, help='chemin du geojson de sortie')
    parser.add_argument('--routes', nargs='*', help='liste optionnelle de route_id pour filtrer')
    args = parser.parse_args()
    shapes_to_geojson(args.gtfs, args.out, include_routes=args.routes)


if __name__ == "__main__":
    main()
