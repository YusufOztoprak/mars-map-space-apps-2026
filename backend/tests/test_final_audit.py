"""Independent numerical references and current real-data acceptance checks."""
import heapq
import io
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.warp import transform as project
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app
from explorer import ROOT,RADIUS
from routing import astar


@pytest.mark.parametrize('points',[[77.4,18.4],[[True,2]],[[1]],[[1,2,3]],[[None,2]],['bad']])
def test_height_batch_rejects_invalid_pairs(points):
    with app.test_client() as c:
        assert c.post('/api/explorer/heights',json=points).status_code==400


def test_ctx_point_matches_independent_geotiff_projection():
    with rasterio.open(ROOT/'data/jezero_dem.tif') as dem:
        x,y=project('+proj=longlat +R=3396190 +no_defs',dem.crs,[77.4],[18.45])
        expected=float(next(dem.sample([(x[0],y[0])]))[0])
    with app.test_client() as c:
        point=c.get('/api/explorer/point?lon=77.4&lat=18.45&model=ctx').json
        assert point['terrain']['height']['value']==pytest.approx(expected,abs=.011)


@pytest.mark.parametrize('start,end',[
    ((77.42,18.44),(77.40,18.46)),  # Jezero CTX
    ((137.35,-4.7),(137.8,-4.8)),  # Gale MOLA
    ((-134,18),(-133,19)),         # Olympus region
    ((-70,-12),(-68,-13)),         # Valles Marineris
    ((165,40),(168,42)),           # no local DEM / sparse rover observations
])
def test_real_routes_connect_exact_points_and_distance_reference(start,end):
    with app.test_client() as c:
        response=c.post('/api/explorer/routes',json={'start':{'lon':start[0],'lat':start[1]},
            'end':{'lon':end[0],'lat':end[1]},'coverage':['radiation','temperature','dust','geology']})
    assert response.status_code==200,response.json
    for feature in response.json['features']:
        coords=np.asarray(feature['geometry']['coordinates'])
        assert coords[0]==pytest.approx(start,abs=1e-7)
        assert coords[-1]==pytest.approx(end,abs=1e-7)
        # atan2 of 3D unit-vector cross/dot is independent of the API's haversine.
        lon,lat=np.radians(coords.T)
        xyz=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
        angle=np.arctan2(np.linalg.norm(np.cross(xyz[:-1],xyz[1:]),axis=1),(xyz[:-1]*xyz[1:]).sum(axis=1))
        p=feature['properties']
        assert p['distance_km']==pytest.approx(angle.sum()*RADIUS/1000,abs=.003)
        assert p['max_slope_deg']<=20
        assert p['coverage']['radiation']['status']=='missing'
        assert p['coverage']['temperature']['status']=='missing'
        assert p['coverage']['dust']['status']=='missing'


def test_astar_custom_geographic_cost_matches_independent_dijkstra():
    grid=np.array([[1,2,1,1],[1,np.inf,3,1],[1,1,2,1],[1,1,1,1.]])
    lat=np.radians([82,81,80,79]);lon=np.radians([0,3,6,9])
    def distance(r,c,nr,nc):
        a=np.array([math.cos(lat[r])*math.cos(lon[c]),math.cos(lat[r])*math.sin(lon[c]),math.sin(lat[r])])
        b=np.array([math.cos(lat[nr])*math.cos(lon[nc]),math.cos(lat[nr])*math.sin(lon[nc]),math.sin(lat[nr])])
        return math.atan2(float(np.linalg.norm(np.cross(a,b))),float(a@b))
    queue=[(0,(0,0))];best={(0,0):0}
    while queue:
        cost,(r,c)=heapq.heappop(queue)
        if cost>best[(r,c)]:continue
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                nr,nc=r+dr,c+dc
                if (not dr and not dc) or not 0<=nr<4 or not 0<=nc<4:continue
                if dr and dc and (not np.isfinite(grid[r,nc]) or not np.isfinite(grid[nr,c])):continue
                candidate=cost+grid[nr,nc]*distance(r,c,nr,nc)
                if candidate<best.get((nr,nc),math.inf):
                    best[nr,nc]=candidate;heapq.heappush(queue,(candidate,(nr,nc)))
    path=astar(grid,(0,0),(3,3),weight=1,edge_distance=distance,heuristic=lambda r,c:distance(r,c,3,3))
    actual=sum(grid[b]*distance(*a,*b) for a,b in zip(path,path[1:]))
    assert actual==pytest.approx(best[3,3],rel=1e-12)


def test_raster_layer_outputs_are_distinct_and_geology_is_not_elevation():
    with app.test_client() as c:
        arrays={kind:np.asarray(Image.open(io.BytesIO(c.get(f'/api/explorer/raster/{kind}/0/0/0.png').data)))
                for kind in ('height','slope','roughness','relief','coverage')}
        assert all(a.shape==(256,256,4) for a in arrays.values())
        assert all(not np.array_equal(arrays[a],arrays[b]) for a,b in (('height','slope'),('height','roughness'),('height','relief')))
        point=c.get('/api/explorer/point?lon=77.4&lat=18.45').json
        assert isinstance(point['terrain']['height']['value'],(int,float))
        assert isinstance(point['geology']['unit'],str)
