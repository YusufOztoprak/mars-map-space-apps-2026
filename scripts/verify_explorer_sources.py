"""Refresh optical WMTS footprints and one traceable local RAD observation."""
import json
import re
import hashlib
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'explorer'
TREK = 'https://trek.nasa.gov'
NS = {'w':'http://www.opengis.net/wmts/1.0', 'o':'http://www.opengis.net/ows/1.1'}

def read(url, limit=None):
    request = Request(url, headers={'Range':f'bytes=0-{limit-1}'} if limit else {})
    with urlopen(request, timeout=40) as response:
        return response.read(limit) if limit else response.read()

def optical(product):
    label, title = product['productLabel'], product['title']
    try:
        url = f'{TREK}/tiles/Mars/EQ/{label}/1.0.0/WMTSCapabilities.xml'
        root = ET.fromstring(read(url))
        layer = root.find('.//w:Layer', NS)
        box = layer.find('o:WGS84BoundingBox', NS)
        if box is None:
            box = layer.find('o:BoundingBox', NS)
        west,south = map(float, box.find('o:LowerCorner',NS).text.split())
        east,north = map(float, box.find('o:UpperCorner',NS).text.split())
        matrix_name=layer.find('w:TileMatrixSetLink/w:TileMatrixSet',NS).text
        matrix_set=next(s for s in root.findall('.//w:Contents/w:TileMatrixSet',NS)
                        if s.find('o:Identifier',NS).text==matrix_name)
        matrices = matrix_set.findall('w:TileMatrix', NS)
        first,last = matrices[0],matrices[-1]
        if float(first.find('w:MatrixWidth',NS).text)!=2 or float(first.find('w:MatrixHeight',NS).text)!=1:
            raise ValueError('Not the geographic 2:1 tile matrix')
        level = int(last.find('o:Identifier',NS).text)
        width = float(last.find('w:MatrixWidth',NS).text)*int(last.find('w:TileWidth',NS).text)
        ext = layer.find('w:Format',NS).text.split('/')[-1].replace('jpeg','jpg')
        resource=layer.find('w:ResourceURL',NS)
        if resource is None:
            raise ValueError('No advertised tile template')
        template=resource.attrib['template'].replace('http://','https://')
        for old,new in {'{TileMatrix}':'{z}','{TileRow}':'{y}','{TileCol}':'{x}',
                        '{Style}':'default','{TileMatrixSet}':'default028mm'}.items():
            template=template.replace(old,new)
        tile_width=int(last.find('w:TileWidth',NS).text)
        tile_height=int(last.find('w:TileHeight',NS).text)
        metadata_url=url
        if any(float(m.find('w:MatrixWidth',NS).text)!=2**(int(m.find('o:Identifier',NS).text)+1)
               or float(m.find('w:MatrixHeight',NS).text)!=2**int(m.find('o:Identifier',NS).text)
               for m in matrices):
            # NASA's global HiRISE capabilities repeat z11 dimensions at z12–17.
            # Use the linked publisher's geographic LOD metadata, never guess.
            if not template.startswith('https://astro.arcgis.com/'):
                raise ValueError('Inconsistent geographic tile matrix dimensions')
            metadata_url=template.split('/tile/')[0]+'?f=pjson'
            service=json.loads(read(metadata_url));info=service['tileInfo']
            if info['origin']!={'x':-180,'y':90} or service['spatialReference']['wkid']!=104971:
                raise ValueError('Unexpected Mars tile origin or reference system')
            tile_width,tile_height=info['cols'],info['rows']
            lods={lod['level']:lod for lod in info['lods']}
            if not math.isclose(lods[level]['resolution'],360/(2**(level+1)*tile_width),rel_tol=1e-7):
                raise ValueError('Publisher LOD resolution does not match the geographic grid')
            width=360/lods[level]['resolution']
        if not -180.01 <= west < east <= 180.01 or not -90.01 <= south < north <= 90.01:
            raise ValueError('Footprint requires longitude conversion')
        return {'id':label,'title':title,'ext':ext,'max_level':level,'template':template,
                'tile_width':tile_width,'tile_height':tile_height,'grid_metadata_url':metadata_url,
                'bounds':[max(-180,west),max(-90,south),min(180,east),min(90,north)],
                'resolution_m':round(2*3.141592653589793*3396190/width,2),
                'source_url':url,'mission':'MRO','instrument':'HiRISE' if 'HiRISE' in title else 'CTX',
                'attribution':'NASA/JPL/University of Arizona · NASA Mars Trek' if 'HiRISE' in title else 'NASA/JPL/MSSS · NASA Mars Trek',
                'kind':'optical mosaic', 'time':'Archived mosaic; acquisition times vary by image'}
    except Exception as error:
        print(f'SKIP {label}: {error}')
        return {'id':label,'source_url':url,'error':str(error)}

def main():
    config=json.loads(read(f'{TREK}/tiles/apidoc/config/config.json'))['mars']
    url=config['service_endpoints']['listVisibleLayersUrl'].replace('PROJECTIONTYPE','eq')
    products=json.loads(read(url))['response']['docs']
    selected=[p for p in products if ('CTX' in p['title'] or 'HiRISE' in p['title'])
              and ('Mosaic' in p['title'] or 'orthomosaic' in p['title'].lower())
              and not any(k in p['title'].lower() for k in ('slope','hillshade','dtm','dem'))]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(optical,selected))
    layers=[p for p in results if 'error' not in p]
    layers.sort(key=lambda p:-p['resolution_m'])
    (DATA/'imagery.json').write_text(json.dumps({'reviewed':datetime.now(timezone.utc).isoformat(),
        'catalog_url':url,'layers':layers,'rejected':[p for p in results if 'error' in p]},ensure_ascii=False,indent=2),encoding='utf8')
    base='https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/DATA/SOL_01418_01514/'
    name='RAD_RDR_2016_298_19_33_1500_V00'
    label=read(base+name+'.LBL')
    chunk=read(base+name+'.TXT',25000)
    text=chunk.decode('ascii')
    pointer=int(re.search(rb'\^OBS000_TOT_DOSE_E_ELEMENT\s*=\s*\("[^"]+",(\d+) <BYTES>\)',label).group(1))
    value=float(chunk[pointer-1:pointer-1+8])
    assert 'microGray / Hour' in label.decode('ascii') and value > 0
    utc=re.search(r'START_OBS_UTC="([^"]+)"',text).group(1)
    stamp=datetime.strptime(utc,'%Y-%j %H:%M:%S').replace(tzinfo=timezone.utc).isoformat()
    waypoint_url='https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_waypoints.json'
    features=json.loads(read(waypoint_url))['features']
    waypoint=next(f for f in features if f['properties'].get('sol')==1500)
    record={'id':'radiation','point':waypoint['geometry']['coordinates'][:2],'sol':1500,
        'time':stamp,'duration_s':int(re.search(r'OBS_DURATION=(\d+)',text).group(1)),
        'value':value,'unit':'µGy/h','instrument':'Curiosity · RAD E detector',
        'source':base+name+'.TXT','label_url':base+name+'.LBL',
        'dataset':'MSL-M-RAD-3-RDR-V1.0','observation':'OBS000_TOT_DOSE_E_ELEMENT',
        'location_source':waypoint_url,'location':'NASA Sol 1500 rover endpoint; not a time-matched instrument position',
        'coordinate_accuracy':'Same-sol rover waypoint association; exact observation position is unavailable (PDS geometry fields are zero placeholders).',
        'scope':'local archived observation; no regional or global radiation coverage',
        'license':'NASA PDS science data; retain dataset and producer attribution',
        'producer':'RAD team / Southwest Research Institute · NASA PDS PPI',
        'source_excerpt_sha256':hashlib.sha256(chunk).hexdigest()}
    # Preserve the independently sourced MEDA sample.
    observations=json.loads((DATA/'observations.json').read_text(encoding='utf8'))
    observations=[o for o in observations if o['id']!='radiation']+[record]
    (DATA/'observations.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2),encoding='utf8')
    evidence=DATA/'rad-sol1500'
    evidence.mkdir(exist_ok=True)
    (evidence/'source.lbl').write_bytes(label)
    (evidence/'source-first-25000.txt').write_bytes(chunk)
    (evidence/'waypoint.json').write_text(json.dumps(waypoint,indent=2),encoding='utf8')
    print(f'{len(layers)} optical footprints; RAD {value} µGy/h at {stamp}')

if __name__=='__main__':
    main()
