import numpy as np

DEFAULT_BANDS={"blue":1,"green":2,"red":3,"nir":7,"swir":11} # zero-indexed Sentinel-2 order in common EuroSAT TIFFs
def _ratio(a,b):
    a=np.ma.asarray(a,dtype=np.float32); b=np.ma.asarray(b,dtype=np.float32)
    valid=~(np.ma.getmaskarray(a)|np.ma.getmaskarray(b)) & (np.abs(a+b)>1e-8)
    numerator=a.filled(np.nan)-b.filled(np.nan); denominator=a.filled(np.nan)+b.filled(np.nan)
    out=np.full(numerator.shape,np.nan,dtype=np.float32)
    return np.divide(numerator,denominator,out=out,where=valid).astype(np.float32)
def summary(array, threshold=0.0):
    valid=np.asarray(array)[np.isfinite(array)]
    if not valid.size: return {"valid_pixel_count":0,"mean":None,"min":None,"max":None,"median":None,"percentage_above_threshold":None}
    return {"valid_pixel_count":int(valid.size),"mean":float(np.mean(valid)),"min":float(np.min(valid)),"max":float(np.max(valid)),"median":float(np.median(valid)),"percentage_above_threshold":float(np.mean(valid>threshold)*100)}
def ndvi(data, bands=None, threshold=0.2):
    b={**DEFAULT_BANDS,**(bands or {})}; a=_ratio(data[b["nir"]].astype(np.float32),data[b["red"]].astype(np.float32)); return a,summary(a,threshold)
def ndwi(data, bands=None, threshold=0.0):
    b={**DEFAULT_BANDS,**(bands or {})}; a=_ratio(data[b["green"]].astype(np.float32),data[b["nir"]].astype(np.float32)); return a,summary(a,threshold)
def ndbi(data, bands=None, threshold=0.0):
    b={**DEFAULT_BANDS,**(bands or {})}; a=_ratio(data[b["swir"]].astype(np.float32),data[b["nir"]].astype(np.float32)); return a,summary(a,threshold)
