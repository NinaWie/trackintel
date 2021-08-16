import datetime
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point
from sklearn.cluster import DBSCAN

import trackintel as ti
from trackintel.geogr.distances import calculate_distance_matrix


@pytest.fixture
def example_staypoints():
    """Staypoints for location generation.
    Staypoints have non-continous ids and should result in noise and several locations per user.
    The following staypoint ids should form a location (1, 15), (5,6), (80, 3)
    The following staypoint ids should be noise (2, 7)

    for agg_level="dataset"
    The following staypoint ids should form a location (1, 15), (5,6, 80, 3),
    The following staypoint ids should be noise (2, 7)
    """
    p1 = Point(8.5067847, 47.4)
    p2 = Point(8.5067847, 47.5)
    p3 = Point(8.5067847, 47.6)
    p4 = Point(8.5067847, 47.7)

    t1 = pd.Timestamp("1971-01-01 00:00:00", tz="utc")
    t2 = pd.Timestamp("1971-01-01 05:00:00", tz="utc")
    t3 = pd.Timestamp("1971-01-02 07:00:00", tz="utc")
    t4 = pd.Timestamp("1971-01-02 08:00:00", tz="utc")
    t5 = pd.Timestamp("1971-01-02 09:00:00", tz="utc")
    t6 = pd.Timestamp("1971-01-02 10:00:00", tz="utc")
    one_hour = datetime.timedelta(hours=1)

    list_dict = [
        {"id": 1, "user_id": 0, "started_at": t1, "finished_at": t2, "geom": p1},
        {"id": 5, "user_id": 0, "started_at": t2, "finished_at": t3, "geom": p2},
        {"id": 2, "user_id": 0, "started_at": t3, "finished_at": t4, "geom": p3},
        {"id": 6, "user_id": 0, "started_at": t4, "finished_at": t5, "geom": p2},
        {"id": 15, "user_id": 0, "started_at": t5, "finished_at": t6, "geom": p1},
        {"id": 7, "user_id": 1, "started_at": t3, "finished_at": t4, "geom": p4},
        {"id": 80, "user_id": 1, "started_at": t4, "finished_at": t5, "geom": p2},
        {"id": 3, "user_id": 1, "started_at": t5, "finished_at": t6, "geom": p2},
    ]
    sp = gpd.GeoDataFrame(data=list_dict, geometry="geom", crs="EPSG:4326")
    sp = sp.set_index("id")
    assert sp.as_staypoints
    return sp


@pytest.fixture
def example_staypoints_merge():
    """
    Staypoints for merge operation

    The following staypoints should be merged: id 2,6,15 for user 0 and 7, 80 for user 1
    Note: id 5 and 2 should not be merged because of time gap
    It must be ensured that 15 and 7 are not merged (different user)
    """
    p1 = Point(8.5067847, 47.4)

    t1 = pd.Timestamp("1971-01-01 00:00:00", tz="utc")
    t2 = pd.Timestamp("1971-01-02 05:00:00", tz="utc")
    t3 = pd.Timestamp("1971-01-02 06:45:00", tz="utc")
    t4 = pd.Timestamp("1971-01-02 08:55:00", tz="utc")
    t45 = pd.Timestamp("1971-01-02 08:57:00", tz="utc")
    t5 = pd.Timestamp("1971-01-02 09:00:00", tz="utc")
    t6 = pd.Timestamp("1971-01-02 09:20:00", tz="utc")
    one_hour = datetime.timedelta(hours=1)

    list_dict = [
        {"id": 1, "user_id": 0, "started_at": t1, "finished_at": t2, "geom": p1, "location_id": 1},
        {"id": 5, "user_id": 0, "started_at": t2, "finished_at": t2, "geom": p1, "location_id": 2},
        {"id": 2, "user_id": 0, "started_at": t3, "finished_at": t4, "geom": p1, "location_id": 2},
        {"id": 6, "user_id": 0, "started_at": t4, "finished_at": t45, "geom": p1, "location_id": 2},
        {"id": 15, "user_id": 0, "started_at": t5, "finished_at": t6, "geom": p1, "location_id": 2},
        {"id": 7, "user_id": 1, "started_at": t3, "finished_at": t4, "geom": p1, "location_id": 2},
        {"id": 80, "user_id": 1, "started_at": t45, "finished_at": t5, "geom": p1, "location_id": 2},
        {"id": 3, "user_id": 1, "started_at": t5, "finished_at": t6, "geom": p1, "location_id": 4},
    ]
    sp = gpd.GeoDataFrame(data=list_dict, geometry="geom", crs="EPSG:4326")
    sp = sp.set_index("id")
    assert sp.as_staypoints

    # generate example triplegs for the merge function
    tpls = gpd.GeoDataFrame(columns=["user_id", "started_at", "finished_at"])
    return sp, tpls


@pytest.fixture
def example_triplegs_merge(example_staypoints_merge):
    """Example triplegs for merge operation
    If tripleg is between two staypoint, we don't merge those staypoints
    See staypoints example data above --> tripleg between 5 and 2 and between 6 and 15
    """
    # get staypoints from above
    stps, _ = example_staypoints_merge
    # create triplegs inbetween
    # tripleg between 5 and 2
    t21 = pd.Timestamp("1971-01-02 05:10:00", tz="utc")
    t22 = pd.Timestamp("1971-01-02 05:40:00", tz="utc")
    # tripleg between 6 and 15
    t45 = pd.Timestamp("1971-01-02 08:57:00", tz="utc")
    t5 = pd.Timestamp("1971-01-02 09:00:00", tz="utc")
    list_dict = [
        {"id": 0, "user_id": 0, "started_at": t45, "finished_at": t5},
        {"id": 1, "user_id": 0, "started_at": t21, "finished_at": t22},
    ]
    # geometry is not required for the merge operation, so we leave it away
    tpls = gpd.GeoDataFrame(data=list_dict, crs="EPSG:4326")
    tpls = tpls.set_index("id")
    return stps, tpls


class TestGenerate_locations:
    """Tests for generate_locations() method."""

    def test_dbscan_hav_euc(self):
        """Test if using haversine and euclidean distances will generate the same location result."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")

        # haversine calculation
        _, loc_har = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=100, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )
        # WGS_1984
        stps.crs = "epsg:4326"
        # WGS_1984_UTM_Zone_49N
        stps = stps.to_crs("epsg:32649")

        # euclidean calculation
        _, loc_eu = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=100, num_samples=0, distance_metric="euclidean", agg_level="dataset"
        )

        assert len(loc_har) == len(loc_eu)

    def test_dbscan_haversine(self):
        """Test haversine dbscan location result with manually calling the DBSCAN method."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")

        # haversine calculation using sklearn.metrics.pairwise_distances
        stps, locs = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )

        # calculate pairwise haversine matrix and fed to dbscan
        sp_distance_matrix = calculate_distance_matrix(stps, dist_metric="haversine")
        db = DBSCAN(eps=10, min_samples=0, metric="precomputed")
        labels = db.fit_predict(sp_distance_matrix)

        assert len(set(locs.index)) == len(set(labels))

    def test_dbscan_loc(self):
        """Test haversine dbscan location result with manually grouping the locations method."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")
        stps, locs = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )

        # create locations as grouped staypoints, another way to create locations
        other_locs = pd.DataFrame(columns=["user_id", "id", "center"])
        grouped_df = stps.groupby(["user_id", "location_id"])
        for combined_id, group in grouped_df:
            user_id, location_id = combined_id
            group.set_geometry(stps.geometry.name, inplace=True)

            if int(location_id) != -1:
                temp_loc = {}
                temp_loc["user_id"] = user_id
                temp_loc["id"] = location_id

                # point geometry of place
                temp_loc["center"] = Point(group.geometry.x.mean(), group.geometry.y.mean())
                other_locs = other_locs.append(temp_loc, ignore_index=True)

        other_locs = gpd.GeoDataFrame(other_locs, geometry="center", crs=stps.crs)
        other_locs.set_index("id", inplace=True)

        assert all(other_locs["center"] == locs["center"])
        assert all(other_locs.index == locs.index)

    def test_dbscan_user_dataset(self):
        """Test user and dataset location generation."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")
        # take the first row and duplicate once
        stps = stps.head(1)
        stps = stps.append(stps, ignore_index=True)
        # assign a different user_id to the second row
        stps.iloc[1, 4] = 1

        # duplicate for a certain number
        stps = stps.append([stps] * 5, ignore_index=True)
        _, locs_ds = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )
        _, locs_us = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="user"
        )
        loc_dataset_num = len(locs_ds.index.unique())
        loc_user_num = len(locs_us.index.unique())
        assert loc_dataset_num == 1
        assert loc_user_num == 2

    def test_dbscan_min(self):
        """Test with small epsilon parameter."""
        pfs_file = os.path.join("tests", "data", "positionfixes.csv")
        pfs = ti.read_positionfixes_csv(pfs_file, sep=";", tz="utc", index_col="id")
        _, stps = pfs.as_positionfixes.generate_staypoints(
            method="sliding", gap_threshold=1e6, dist_threshold=0, time_threshold=0
        )
        _, locs_user = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=1e-18, num_samples=0, agg_level="user"
        )
        _, locs_data = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=1e-18, num_samples=0, agg_level="dataset"
        )
        # With small hyperparameters, clustering should not reduce the number
        assert len(locs_user) == len(stps)
        assert len(locs_data) == len(stps)

    def test_dbscan_max(self):
        """Test with large epsilon parameter."""
        pfs_file = os.path.join("tests", "data", "positionfixes.csv")
        pfs = ti.read_positionfixes_csv(pfs_file, sep=";", tz="utc", index_col="id")
        _, stps = pfs.as_positionfixes.generate_staypoints(
            method="sliding", gap_threshold=1e6, dist_threshold=0, time_threshold=0
        )
        _, locs_user = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=1e18, num_samples=1000, agg_level="user"
        )
        _, locs_data = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=1e18, num_samples=1000, agg_level="dataset"
        )
        # "With large epsilon, every user location is an outlier"
        assert len(locs_user) == 0
        assert len(locs_data) == 0

    def test_missing_link(self):
        """Test nan is assigned for missing link between stps and locs."""
        pfs_file = os.path.join("tests", "data", "positionfixes.csv")
        pfs = ti.read_positionfixes_csv(pfs_file, sep=";", tz="utc", index_col="id")
        _, stps = pfs.as_positionfixes.generate_staypoints(
            method="sliding", gap_threshold=1e6, dist_threshold=0, time_threshold=0
        )
        stps, _ = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=1e18, num_samples=1000, agg_level="user"
        )

        assert pd.isna(stps["location_id"]).any()

    def test_num_samples_high(self):
        """Test higher values of num_samples for generate_locations."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")
        stps_ns_5, _ = stps.as_staypoints.generate_locations(
            epsilon=50, distance_metric="haversine", agg_level="user", num_samples=2
        )
        non_noise_stps = stps_ns_5[stps_ns_5["location_id"] != -1]

        # group_by_user_id and check that no two different user ids share a common location id
        grouped = list(non_noise_stps.groupby(["user_id"])["location_id"].unique())
        loc_set = []
        for loc_list in grouped:
            loc_set.append(set(loc_list))

        # we assert that the count of overlaps is equal to the count of users
        # (each user has overlap with the same user)
        assert sum([int(len(p & q) > 0) for p in loc_set for q in loc_set]) == len(loc_set)

    def test_dtype_consistent(self):
        """Test the dtypes for the generated columns."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")
        #
        stps, locs = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )
        assert stps["user_id"].dtype == locs["user_id"].dtype
        assert stps["location_id"].dtype == "Int64"
        assert locs.index.dtype == "int64"
        # change the user_id to string
        stps["user_id"] = stps["user_id"].apply(lambda x: str(x))
        stps, locs = stps.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=0, distance_metric="haversine", agg_level="dataset"
        )
        assert stps["user_id"].dtype == locs["user_id"].dtype
        assert stps["location_id"].dtype == "Int64"
        assert locs.index.dtype == "int64"

    def test_index_start(self):
        """Test the generated index start from 0 for different methods."""
        stps_file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        stps = ti.read_staypoints_csv(stps_file, tz="utc", index_col="id")

        distance_metric_ls = ["haversine", "euclidean"]
        agg_level_ls = ["dataset", "user"]
        for distance_metric in distance_metric_ls:
            for agg_level in agg_level_ls:
                _, locations = stps.as_staypoints.generate_locations(
                    method="dbscan", epsilon=10, num_samples=0, distance_metric=distance_metric, agg_level=agg_level
                )
                assert (locations.index == np.arange(len(locations))).any()

    def test_print_progress_flag(self, capsys):
        """Test if the print_progress bar controls the printing behavior."""
        file = os.path.join("tests", "data", "geolife", "geolife_staypoints.csv")
        staypoints = ti.read_staypoints_csv(file, tz="utc", index_col="id")

        staypoints.as_staypoints.generate_locations(print_progress=True)
        captured_print = capsys.readouterr()
        assert captured_print.err != ""

        staypoints.as_staypoints.generate_locations(print_progress=False)
        captured_print = capsys.readouterr()
        assert captured_print.err == ""

    def test_index_stability(self, example_staypoints):
        """Test if the index of the staypoints remains stable"""
        sp = example_staypoints
        sp2, locs = sp.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=2, distance_metric="haversine", agg_level="user"
        )
        assert sp.index.equals(sp2.index)

    def test_location_ids_and_noise(self, example_staypoints):
        """Test if all test cases in the example_staypoints dataset get identified correctly.
        See docstring of example_staypoints for more information"""
        sp = example_staypoints
        sp2, locs = sp.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=2, distance_metric="haversine", agg_level="user"
        )
        assert sp2.loc[1, "location_id"] == sp2.loc[15, "location_id"]
        assert sp2.loc[5, "location_id"] == sp2.loc[6, "location_id"]
        assert sp2.loc[80, "location_id"] == sp2.loc[3, "location_id"]
        assert sp2.loc[1, "location_id"] != sp2.loc[6, "location_id"]
        assert sp2.loc[1, "location_id"] != sp2.loc[80, "location_id"]

        assert sp2.loc[[2, 7], "location_id"].isnull().all()

    def test_location_ids_and_noise_dataset(self, example_staypoints):
        """Test if all test cases in the example_staypoints dataset get identified correctly.
        See docstring of example_staypoints for more information"""
        sp = example_staypoints
        sp2, locs = sp.as_staypoints.generate_locations(
            method="dbscan", epsilon=10, num_samples=2, distance_metric="haversine", agg_level="dataset"
        )

        assert (sp2.loc[[5, 6, 80, 3], "location_id"] == sp2.loc[5, "location_id"]).all()
        assert sp2.loc[1, "location_id"] == sp2.loc[15, "location_id"]
        assert sp2.loc[1, "location_id"] != sp2.loc[5, "location_id"]

        assert sp2.loc[[2, 7], "location_id"].isnull().all()


class TestMergeStaypoints:
    def test_merge_staypoints(self, example_staypoints_merge):
        """Test staypoint merging"""
        stps, tpls = example_staypoints_merge
        # first test with empty tpls
        merged_stps = stps.as_staypoints.merge_staypoints(tpls, agg={"geom": "first", "location_id": "first"})
        assert len(merged_stps) == len(stps) - 3
        # some staypoints stay the same (not merged)
        assert (merged_stps.loc[1] == stps.loc[1]).all()
        assert (merged_stps.loc[5] == stps.loc[5]).all()
        assert (merged_stps.loc[3] == stps.loc[3]).all()

    def test_merge_staypoints_triplegs(self, example_triplegs_merge):
        """Test staypoint merging with triplegs inbetween"""
        # get triplegs inbetween
        stps, tpls = example_triplegs_merge
        merged_stps_with_tpls = stps.as_staypoints.merge_staypoints(tpls)
        # assert that staypoint 6 and 15 were not merged because of tpls inbetween
        assert len(merged_stps_with_tpls) == len(stps) - 2
        # 15 should not be merged
        assert 15 in merged_stps_with_tpls.index

    def test_merge_staypoints_time(self, example_staypoints_merge):
        """Test if all merged staypoints have the correct start and end time"""
        stps, tpls = example_staypoints_merge
        merged_stps = stps.as_staypoints.merge_staypoints(tpls)
        # user 1 - id 7 and 80 merged
        assert stps.loc[7, "started_at"] == merged_stps.loc[7, "started_at"]
        assert stps.loc[80, "finished_at"] == merged_stps.loc[7, "finished_at"]
        # user 0 - id 2,6, and 15 merged
        assert stps.loc[2, "started_at"] == merged_stps.loc[2, "started_at"]
        assert stps.loc[15, "finished_at"] == merged_stps.loc[2, "finished_at"]

    def test_merge_staypoints_max_time_gap(self, example_staypoints_merge):
        """Test it the max_time_gap argument works correctly"""
        stps, tpls = example_staypoints_merge
        merged_stps = stps.as_staypoints.merge_staypoints(tpls, max_time_gap="2h")
        assert len(merged_stps) == len(stps) - 4
        # user 0 - id 5, 2,6, and 15 merged
        assert stps.loc[5, "started_at"] == merged_stps.loc[5, "started_at"]
        assert stps.loc[15, "finished_at"] == merged_stps.loc[5, "finished_at"]

    def test_merge_staypoints_agg(self, example_staypoints_merge):
        """Test whether the user can specify the aggregation mode"""
        aggregation_dict = {"geom": "first", "finished_at": "first"}

        stps, tpls = example_staypoints_merge
        merged_stps = stps.as_staypoints.merge_staypoints(tpls, agg=aggregation_dict)

        # in contrast to the test above, the first of (7,80) should now be used for finished at
        assert stps.loc[7, "finished_at"] == merged_stps.loc[7, "finished_at"]
        assert stps.loc[2, "finished_at"] == merged_stps.loc[2, "finished_at"]
        # the geom should correspond to the first one
        assert stps.loc[7, "geom"] == merged_stps.loc[7, "geom"]
        assert stps.loc[2, "geom"] == merged_stps.loc[2, "geom"]
