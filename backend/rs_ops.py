from pathlib import Path
import base64, io, math
import cv2
import numpy as np
from PIL import Image
import rasterio


def load_raster(path):
    p = Path(path)
    if p.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
        img = np.array(Image.open(p).convert('RGB'))
        return img.transpose(2,0,1).astype(np.float32), {'count':3, 'height':img.shape[0], 'width':img.shape[1], 'crs':None}
    with rasterio.open(p) as src:
        arr = src.read().astype(np.float32)
        meta = {
            'count': src.count, 'height': src.height, 'width': src.width,
            'crs': str(src.crs) if src.crs else None,
            'bounds': list(src.bounds), 'transform': tuple(src.transform)[:6],
            'dtype': str(src.dtypes[0]),
        }
    return arr, meta


def percentile_norm(b):
    b = np.nan_to_num(b, nan=0.0, posinf=0.0, neginf=0.0)
    lo, hi = np.percentile(b, [2, 98])
    if hi <= lo: return np.zeros_like(b, dtype=np.uint8)
    x = np.clip((b-lo)/(hi-lo), 0, 1)
    return (x*255).astype(np.uint8)


def make_preview(arr):
    if arr.shape[0] == 1:
        g = percentile_norm(arr[0]); rgb = np.stack([g,g,g], axis=-1)
    elif arr.shape[0] >= 3:
        # Default visible order for generic rasters is first three bands.
        rgb = np.stack([percentile_norm(arr[0]), percentile_norm(arr[1]), percentile_norm(arr[2])], axis=-1)
    else:
        rgb = np.stack([percentile_norm(arr[0])]*3, axis=-1)
    return rgb


def preview_jpeg(arr, max_side=900):
    rgb = make_preview(arr)
    h,w = rgb.shape[:2]
    scale = min(1.0, max_side/max(h,w))
    if scale < 1:
        rgb = cv2.resize(rgb, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    ok, enc = cv2.imencode('.jpg', cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    return enc.tobytes()


def save_png(img, path):
    cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if img.ndim==3 else img)


def indices(arr, red_idx=None, green_idx=None, nir_idx=None):
    out={}
    if red_idx is not None and nir_idx is not None and red_idx < arr.shape[0] and nir_idx < arr.shape[0]:
        r,n = arr[red_idx], arr[nir_idx]
        out['ndvi'] = (n-r) / (n+r+1e-6)
    if green_idx is not None and nir_idx is not None and green_idx < arr.shape[0] and nir_idx < arr.shape[0]:
        g,n = arr[green_idx], arr[nir_idx]
        out['ndwi'] = (g-n) / (g+n+1e-6)
    return out


def raster_stats(arr):
    x = arr[np.isfinite(arr)]
    if x.size == 0: return {'mean':0,'std':0,'min':0,'max':0}
    return {'mean':float(np.mean(x)), 'std':float(np.std(x)), 'min':float(np.min(x)), 'max':float(np.max(x))}


def image_features(arr, red=None, green=None, nir=None, sar_band=0):
    ids = indices(arr, red, green, nir)
    feat={}
    if 'ndvi' in ids:
        ndvi=ids['ndvi']; feat['vegetation_fraction']=float(np.mean(ndvi>0.35))
    if 'ndwi' in ids:
        ndwi=ids['ndwi']; feat['water_fraction_optical']=float(np.mean(ndwi>0.25))
    if sar_band is not None and sar_band < arr.shape[0] and arr.shape[0] == 1:
        s=arr[sar_band]
        feat['sar_mean']=float(np.mean(s)); feat['sar_std']=float(np.std(s))
        p20,p80=np.percentile(s,[20,80])
        feat['sar_low_fraction']=float(np.mean(s<=p20)); feat['sar_high_fraction']=float(np.mean(s>=p80))
    return feat, ids


def change_map(arr1, arr2, out_path):
    r1=make_preview(arr1); r2=make_preview(arr2)
    size=(min(r1.shape[1],r2.shape[1]), min(r1.shape[0],r2.shape[0]))
    r1=cv2.resize(r1,size,interpolation=cv2.INTER_AREA); r2=cv2.resize(r2,size,interpolation=cv2.INTER_AREA)
    g1=cv2.cvtColor(r1,cv2.COLOR_RGB2GRAY); g2=cv2.cvtColor(r2,cv2.COLOR_RGB2GRAY)
    diff=cv2.absdiff(g1,g2)
    diff=cv2.GaussianBlur(diff,(5,5),0)
    _,mask=cv2.threshold(diff,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    kernel=np.ones((3,3),np.uint8); mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
    pct=float(np.mean(mask>0)*100)
    heat=cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    overlay=cv2.addWeighted(cv2.cvtColor(r2,cv2.COLOR_RGB2BGR),0.55,heat,0.45,0)
    cv2.imwrite(str(out_path), overlay)
    return pct, str(out_path), {'mean_abs_diff':float(np.mean(diff)), 'threshold_pixels_pct':pct}


def optical_sar_fusion(opt_arr, sar_arr, red=None, green=None, nir=None):
    opt_idx=indices(opt_arr,red,green,nir)
    s=sar_arr[0]
    p20,p80=np.percentile(s,[20,80])
    feat={}
    if 'ndvi' in opt_idx: feat['vegetation_fraction']=float(np.mean(opt_idx['ndvi']>0.35))
    if 'ndwi' in opt_idx: feat['water_fraction_optical']=float(np.mean(opt_idx['ndwi']>0.25))
    feat['sar_mean']=float(np.mean(s)); feat['sar_std']=float(np.std(s))
    feat['sar_low_fraction']=float(np.mean(s<=p20)); feat['sar_high_fraction']=float(np.mean(s>=p80))
    interpretation=[]
    if 'ndwi' in opt_idx and feat['water_fraction_optical']>0.08 and feat['sar_low_fraction']>0.35:
        interpretation.append('water-covered regions are consistent with low optical NDWI and low relative SAR backscatter')
    if 'ndvi' in opt_idx and feat['vegetation_fraction']>0.15:
        interpretation.append('vegetation is indicated by positive NDVI')
    if feat['sar_high_fraction']>0.20 and ('ndvi' not in opt_idx or feat.get('vegetation_fraction',0)<0.25):
        interpretation.append('bright/rough SAR regions may correspond to built-up or other high-backscatter surfaces; sensor-specific calibration is required')
    return feat, interpretation
