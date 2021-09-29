RGB_vis_params_sentinel2 = {'bands': ['B4', 'B3', 'B2'], 'min': 0.0, 'max': 10000.0, 'opacity': 1.0, 'gamma': 1.58}
NDVI_vis_params_sentinel2 = {'bands' : ['NDVI'] , "min": -0.5, "max": 1, "palette": ["f90800","fff81a", "31e900"]}
NDTI_vis_params_sentinel2 = {"min": -0.02, "max": 0.19, "palette": ["5a2f00","fffb2d"]}
RC_vis_params_sentinel2 = {"min": 0, "max": 100, "palette": ["5a2f00","fffb2d"]}
#landsat 8 

RGB_vis_params_L8 = {"bands": ['B4', 'B3', 'B2'],"min": 0, "max": 3000, "gamma": 1.4}
NDVI_vis_params_L8 = {'bands' : ['NDVI'] ,"min": -0.5, "max": 1, "palette": ["f90800","fff81a", "31e900"]}
NDTI_vis_params_L8 = {"min": -0.02, "max": 0.19, "palette": ["5a2f00","fffb2d"]}
RC_vis_params_L8 = {"min": 0, "max": 100, "palette": ["5a2f00","fffb2d"]}