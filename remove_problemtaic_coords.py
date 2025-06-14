import pandas as pd

def ignore_null_coords_locations(locations : list , locations_orig : list, index : int , ignore_geolocator=False) -> list:
        """
        Remove locations with problematic coordinates.
        If ignore_geolocator is True, it will not use geolocator to fix coordinates.
        """
        df_locations = pd.DataFrame(locations)
        cols = ["lat", "lon"]
        df_coords = df_locations[cols]
        df_locations.to_csv(f"output/locations{index}.csv", index=False)
        bool_outlier = (df_coords - df_coords.median()  ).abs() < df_coords.std()*2.5
        df_fix = df_locations.loc[bool_outlier.sum(1)<2]
        df_locations = df_locations.drop(df_fix.index)
        locations = list(df_locations.T.to_dict().values())
        print (f"Removed locations : {','.join(df_fix['name'].tolist())} outliers based on distance from median.")
        if ignore_geolocator:
            for i, row in df_fix.iterrows():
                locations[i] = locations_orig[i]
        # Remove locations with None coordinates
        locations = [loc for loc in locations if loc.get("lat") is not None and loc.get("lon") is not None]
        return locations