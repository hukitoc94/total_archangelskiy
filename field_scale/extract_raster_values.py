def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]
PP = getFeatures(two_fields[two_fields['type'] == 'PP'])
array, transform  = mask(dataset=sen2, shapes=PP, crop=True)
array[array == 0] = np.nan
NDTI_array = array[7]
NDTI_array = NDTI_array[~np.isnan(NDTI_array)]


#чтобы не потерять эти функции я их отдельно сюда закину 
