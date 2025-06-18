import pandas as pd
from geopy.distance import geodesic
import numpy as np
from sklearn.cluster import AgglomerativeClustering

def locations_clusters(coords, threshold_km=100):
    """
    Performs agglomerative clustering on latitude/longitude coordinates
    using a distance threshold in kilometers.

    Args:
        coords: List of (lat, lon) tuples.
        threshold_km: Distance threshold in kilometers.

    Returns:
        List of cluster labels for each coordinate.
    """
    n = len(coords)
    # Compute distance matrix
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist = geodesic(coords[i], coords[j]).kilometers
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist

    # Perform clustering
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='precomputed',
        linkage='single',
        distance_threshold=threshold_km
    )
    labels = clustering.fit_predict(dist_matrix)

    label_keep = pd.Series(labels).value_counts().index[0]
    return labels == label_keep
 
def ignore_null_coords_locations(locations : list , locations_orig : list, index : int , threshold_km  : int, ignore_geolocator : bool) -> list:
        """
        Remove locations with problematic coordinates.
        If ignore_geolocator is True, it will not use geolocator to fix coordinates.
        """
        locations = [loc for loc in locations if loc.get("lat") is not None and loc.get("lon") is not None]
        df_locations = pd.DataFrame(locations)
        cols = ["lat", "lon"]
        df_coords = df_locations[cols]
        include_coords = locations_clusters(df_coords.values, threshold_km=threshold_km)
        #return df_coords[include_coords]

        # df_locations.to_csv(f"output/locations{index}.csv", index=False)
        # bool_outlier = (df_coords - df_coords.median()  ).abs() < df_coords.std()*2.5
        # df_fix = df_locations.loc[bool_outlier.sum(1)<2]
        print (f"Removed locations : {','.join(df_locations[~include_coords]['name'].tolist())} outliers based on clustered coordinates.")

        df_locations = df_locations[include_coords]
        locations = list(df_locations.T.to_dict().values())
        if ignore_geolocator:
            for ix, bool_val  in enumerate(include_coords):
                if not bool_val:
                    locations[ix] = locations_orig[ix]
        # Remove locations with None coordinates
        locations = [loc for loc in locations if loc.get("lat") is not None and loc.get("lon") is not None]
        return locations