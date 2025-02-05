# This is not needed if the trackintel library is installed. ==================
import sys

sys.path.append("..")
sys.path.append("../trackintel")
# =============================================================================

import logging

import matplotlib.pyplot as plt

import trackintel as ti

logging.basicConfig(filename="examples/log/preprocessing.log", level=logging.INFO, filemode="w")

# GPS trajectory.
pfs = ti.read_positionfixes_csv("examples/data/geolife_trajectory.csv", sep=";", crs="EPSG:4326", index_col=None)
pfs.as_positionfixes.plot(out_filename="examples/out/gps_trajectory_positionfixes.png", plot_osm=True)

_, sp = pfs.as_positionfixes.generate_staypoints(method="sliding", dist_threshold=100, time_threshold=5)
sp.as_staypoints.plot(
    out_filename="examples/out/gps_trajectory_staypoints.png", radius=100, positionfixes=pfs, plot_osm=True
)

_, locs = sp.as_staypoints.generate_locations(method="dbscan", epsilon=100, num_samples=3)
locs.as_locations.plot(
    out_filename="examples/out/gps_trajectory_locations.png",
    radius=120,
    positionfixes=pfs,
    staypoints=sp,
    staypoints_radius=100,
    plot_osm=True,
)

_, tpls = pfs.as_positionfixes.generate_triplegs(staypoints=sp)
tpls.as_triplegs.plot(
    out_filename="examples/out/gpsies_trajectory_triplegs.png", staypoints=sp, staypoints_radius=100, plot_osm=True
)

# Geolife trajectory.
pfs = ti.read_positionfixes_csv("examples/data/geolife_trajectory.csv", sep=";", crs="EPSG:4326", index_col=None)
pfs.as_positionfixes.plot(out_filename="examples/out/geolife_trajectory_positionfixes.png", plot_osm=False)

_, sp = pfs.as_positionfixes.generate_staypoints(method="sliding", dist_threshold=100, time_threshold=10)
sp.as_staypoints.plot(
    out_filename="examples/out/geolife_trajectory_staypoints.png", radius=100, positionfixes=pfs, plot_osm=True
)

# Google trajectory.
pfs = ti.read_positionfixes_csv("examples/data/google_trajectory.csv", sep=";", crs="EPSG:4326", index_col=None)
_, sp = pfs.as_positionfixes.generate_staypoints(method="sliding", dist_threshold=75, time_threshold=10)
sp.as_staypoints.plot(
    out_filename="examples/out/google_trajectory_staypoints.png", radius=75, positionfixes=pfs, plot_osm=True
)

# Posmo trajectory.
pfs = ti.read_positionfixes_csv(
    "examples/data/posmo_trajectory.csv", sep=";", crs="EPSG:4326", index_col=None, tz="UTC"
)
_, sp = pfs.as_positionfixes.generate_staypoints(method="sliding", dist_threshold=50, time_threshold=1)
sp.as_staypoints.plot(
    out_filename="examples/out/posmo_trajectory_staypoints.png", radius=50, positionfixes=pfs, plot_osm=False
)
