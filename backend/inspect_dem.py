import rasterio

with rasterio.open("../data/jezero_dem.tif") as src:
    print("CRS:", src.crs)
    print("Transform:", src.transform)
    print("Bounds:", src.bounds)
    print("Width/Height:", src.width, src.height)
    print("Dtype:", src.dtypes)
    print("Nodata:", src.nodata)