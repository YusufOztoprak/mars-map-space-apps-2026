"""Check archive evidence and numerical/visual contracts with bundled real products."""
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app
from explorer import DATA


def test_rad_value_units_time_and_position_are_traceable():
    record=next(o for o in json.loads((DATA/'observations.json').read_text(encoding='utf8')) if o['id']=='radiation')
    label=(DATA/'rad-sol1500/source.lbl').read_bytes()
    excerpt=(DATA/'rad-sol1500/source-first-25000.txt').read_bytes()
    waypoint=json.loads((DATA/'rad-sol1500/waypoint.json').read_text())
    pointer=int(re.search(rb'\^OBS000_TOT_DOSE_E_ELEMENT\s*=\s*\("[^"]+",(\d+) <BYTES>\)',label).group(1))
    assert float(excerpt[pointer-1:pointer+7])==record['value']==10.92457
    assert b'microGray / Hour' in label and record['unit']=='µGy/h'
    assert hashlib.sha256(excerpt).hexdigest()==record['source_excerpt_sha256']
    assert b'START_OBS_UTC="2016-298 19:33:55"' in excerpt
    assert record['time']=='2016-10-24T19:33:55+00:00'
    assert waypoint['properties']['sol']==record['sol']
    assert record['point']==waypoint['geometry']['coordinates'][:2]
    assert 'not a time-matched' in record['location'] and 'no regional or global' in record['scope']


def test_mola_pixel_point_and_legend_agree():
    path=DATA/'mola16.img'
    if not path.exists():pytest.skip('Real MOLA raster is required')
    raw=np.memmap(path,dtype='>i2',mode='r',shape=(2880,5760))
    z,x,y,row,col=4,28,8,91,117
    lon=360*(x+(col+.5)/256)/2**(z+1)-180
    lat=90-180*(y+(row+.5)/256)/2**z
    value=float(raw[int(math.floor((90-lat)*16)),int(math.floor(lon*16))%5760])
    with app.test_client() as c:
        point=c.get(f'/api/explorer/point?lon={lon}&lat={lat}&model=mola').json
        assert point['terrain']['height']['value']==value
        scheme=c.get('/api/explorer/meta').json['legends']['height']
        colors=[tuple(bytes.fromhex(h[1:])) for h in scheme['colors']]
        expected=[int(np.interp(value,scheme['values'],channel)) for channel in zip(*colors)]
        image=Image.open(io.BytesIO(c.get(f'/api/explorer/raster/height/{z}/{x}/{y}.png?model=mola').data))
        assert image.getpixel((col,row))==(*expected,255)
        assert 'areoid' in c.get('/api/explorer/meta').json['elevation_reference']


def test_route_model_does_not_fall_back_outside_its_footprint():
    with app.test_client() as c:
        point=c.get('/api/explorer/point?lon=137.35&lat=-4.7&model=ctx').json
        assert point['terrain']['height'] is None
        assert point['coverage']['height']['status']=='missing'
        assert point['coverage']['radiation']['status']=='missing'
        image=Image.open(io.BytesIO(c.get('/api/explorer/raster/slope/0/0/0.png?model=ctx').data))
        assert image.getchannel('A').getextrema()==(0,0)
        assert c.get('/api/explorer/raster/height/0/0/0.png?model=unknown').status_code==400


def test_relief_uses_same_height_hues_and_validity():
    with app.test_client() as c:
        base=np.array(Image.open(io.BytesIO(c.get('/api/explorer/raster/height/2/6/2.png').data)))
        shaded=np.array(Image.open(io.BytesIO(c.get('/api/explorer/raster/relief/2/6/2.png').data)))
        assert np.array_equal(base[:,:,3],shaded[:,:,3])
        assert np.all(shaded[:,:,:3]<=base[:,:,:3])
        assert np.any(shaded[:,:,:3]!=base[:,:,:3])


def test_global_ctx_uses_advertised_external_tile_service():
    layers=json.loads((DATA/'imagery.json').read_text())['layers']
    global_ctx=next(p for p in layers if p['id']=='CTX_beta01_uncontrolled_5m_Caltech')
    assert global_ctx['template']=='https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX/MapServer/tile/{z}/{y}/{x}'
    assert global_ctx['max_level']==11 and global_ctx['tile_width']==512
    assert global_ctx['resolution_m']==pytest.approx(10.18,abs=.01)
    assert all(p['source_url'].startswith('https://trek.nasa.gov/') for p in layers)


def test_historical_dust_legend_matches_prepared_texture():
    product=json.loads((DATA/'dust-my34-sol400.json').read_text())
    image=Image.open(DATA/'dust-my34-sol400.png')
    values=product['legend']['values']
    channels=list(zip(*(tuple(bytes.fromhex(h[1:])) for h in product['legend']['colors'])))
    for x,y in ((2,4),(349,170),(710,330)):
        lon=-180+(x+.5)/2
        lat=90-(y+.5)/2
        value=product['values'][min(59,max(0,int((90-lat)//3)))][math.floor((lon+181.5)/3)%120]
        rgb=np.array([np.interp(value,values,channel) for channel in channels])
        assert np.max(np.abs(np.array(image.getpixel((x,y))[:3])-rgb))<1.1
    with app.test_client() as c:
        assert c.get('/api/explorer/meta').json['legends']['dust']==product['legend']
