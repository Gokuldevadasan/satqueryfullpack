from pathlib import Path
import json, tempfile, shutil, uuid, os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .agent import execute
from .rs_ops import load_raster
from inference.predictor import analyze as medium_analyze
from inference.model_router import available_models, MODELS
from inference.model_loader import model_info as runtime_model_info

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
MAX_UPLOAD_BYTES=int(os.getenv('SATQUERY_MAX_UPLOAD_BYTES', str(100 * 1024 * 1024)))

app=FastAPI(title='SatQuery AI Medium Backend', version='0.2.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/outputs', StaticFiles(directory=str(OUT)), name='outputs')

@app.on_event("startup")
def report_models():
    print(f"[SatQuery] Project root: {ROOT}")
    print(f"[SatQuery] Models directory: {ROOT / 'models'}")
    for key, label in (("rgb_v1", "RGB V1"), ("rgb_v11", "RGB V1.1 ONNX"), ("spectral", "Spectral ONNX")):
        info=runtime_model_info(key, load=True)
        print(f"[SatQuery] {label}: {'FOUND' if info['onnx_exists'] else 'MISSING'}")
        print(f"[SatQuery] {label} DATA: {'FOUND' if info['external_data_exists'] else 'MISSING'}")
        if info.get('error'): print(f"[SatQuery] ERROR loading {label}: {info['error']}")


def classifier(arr):
    from inference.rgb_inference import predict_rgb

    result = predict_rgb(None, arr)
    if result is None:
        return 'model_not_loaded', []
    return result['label'], [item['confidence'] for item in result['top_predictions']]


def temp_file(upload):
    suffix=Path(upload.filename or '').suffix.lower()
    if not suffix:
        suffix = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/tiff': '.tif',
        }.get(upload.content_type or '', '')
    if suffix not in {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}:
        raise HTTPException(status_code=415, detail='Unsupported image type.')
    p=OUT/f'{uuid.uuid4().hex}{suffix}'
    return p

@app.get('/health')
def health():
    models=available_models()
    loaded={key:runtime_model_info(key,load=True) for key in models}
    return {
        'status':'ok',
        'satquery_version':'Medium',
        'backend':'FastAPI',
        'backend_id':'satquery-ai-medium',
        'backend_build':'medium-analysis-v2',
        'models_loaded':any(model['available'] for model in models.values()),
        'models':models,
        'rgb_model_available':bool(loaded['rgb_v11'].get('loaded') or loaded['rgb_v1'].get('loaded')),
        'spectral_model_available':bool(loaded['spectral'].get('loaded')),
        'gis_available':True,
        'weather_available':True,
    }

@app.get('/model-info')
def model_info():
    import onnxruntime as ort
    return {
        'satquery_version':'Medium',
        'models':{key:runtime_model_info(key,load=True) for key in MODELS},
        'classes':{'rgb':'models/classes.json','spectral':'models/spectral_classes.json'},
        'onnxruntime_version':ort.__version__,
        'deployment':'ONNX Runtime CPU',
    }

@app.post('/analyze')
async def analyze_upload(image: UploadFile = File(...)):
    """Analyze RGB images and GeoTIFFs through the SatQuery Medium pipeline."""
    path=temp_file(image)
    try:
        total=0
        with path.open('wb') as f:
            while chunk := await image.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES: raise HTTPException(status_code=413, detail=f'Upload exceeds {MAX_UPLOAD_BYTES} byte limit.')
                f.write(chunk)
        result = medium_analyze(path)
        result['input']['filename'] = image.filename or path.name
        return result
    finally:
        path.unlink(missing_ok=True)

@app.post('/api/query')
async def query(query: str = Form(...), metadata_json: str = Form('{}'), files: list[UploadFile] = File(...)):
    cfg=json.loads(metadata_json or '{}')
    saved=[]
    for up in files:
        p=temp_file(up)
        with p.open('wb') as f:
            shutil.copyfileobj(up.file, f)
        saved.append(p)
    try:
        result=execute(query,saved,cfg,OUT,classifier)
        # Make browser-friendly URLs for generated evidence.
        if 'visuals' in result:
            for v in result['visuals']:
                v['url']='/outputs/'+Path(v['path']).name
                v.pop('path',None)
        return result
    finally:
        for p in saved:
            try: p.unlink()
            except: pass

@app.get('/api/capabilities')
def capabilities():
    return {
        'single_image':['VQA','captioning/scene description'],
        'multi_image':['bi-temporal change detection','optical-SAR fusion'],
        'accepted':['GeoTIFF','TIFF','PNG','JPEG'],
        'edge':'Raspberry Pi + CPU ONNX Runtime'
    }
