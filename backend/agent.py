from pathlib import Path
import json, time
import numpy as np
from .rs_ops import load_raster, image_features, change_map, optical_sar_fusion

INTENTS = {
    'CHANGE': ['change','changed','difference','before','after','increase','decrease','between two dates','compare'],
    'FUSION': ['sar','optical and sar','both images','cross-modal','radar','backscatter','built-up and water'],
    'CAPTION': ['describe','scene','land-cover','land cover','what is in the image','caption','summarize image'],
}


def route(query, nfiles):
    q=query.lower()
    if nfiles >= 2 and any(k in q for k in INTENTS['CHANGE']): return 'CHANGE'
    if nfiles >= 2 and any(k in q for k in INTENTS['FUSION']): return 'FUSION'
    if any(k in q for k in INTENTS['CAPTION']): return 'CAPTION'
    if nfiles >= 2: return 'CHANGE'
    return 'VQA'


def class_caption(cls, probs, feat):
    text=f"The remote-sensing scene is most consistent with {cls.lower()}."
    if 'vegetation_fraction' in feat: text += f" Estimated vegetation fraction is {feat['vegetation_fraction']*100:.1f}%."
    if 'water_fraction_optical' in feat: text += f" Estimated water fraction is {feat['water_fraction_optical']*100:.1f}%."
    if 'sar_high_fraction' in feat: text += f" The image has {feat['sar_high_fraction']*100:.1f}% high-relative-backscatter pixels."
    return text


def answer_vqa(query, feat, cls):
    q=query.lower()
    if any(k in q for k in ['water','lake','river','flood']):
        if 'water_fraction_optical' in feat:
            frac=feat['water_fraction_optical']
            return (f"Water-like regions are estimated at about {frac*100:.1f}% of the image.", min(0.95,max(0.35, 1-abs(frac-0.5))))
        return (f"The current single-image classifier predicts {cls}; a quantitative water estimate requires optical bands with green and NIR information.", 0.55)
    if any(k in q for k in ['vegetation','forest','crop','green']):
        if 'vegetation_fraction' in feat:
            frac=feat['vegetation_fraction']
            return (f"Vegetation-like pixels are estimated at {frac*100:.1f}%.", min(0.95,0.4+frac))
        return (f"The classifier predicts {cls}, but vegetation fraction needs NIR and red bands.",0.55)
    if any(k in q for k in ['sar','radar','backscatter']):
        if 'sar_mean' in feat:
            return (f"SAR relative-backscatter statistics: mean {feat['sar_mean']:.3f}, standard deviation {feat['sar_std']:.3f}.",0.70)
        return ('This input does not appear to be a single-band SAR raster.',0.55)
    return (f"The remote-sensing classifier's most likely land-cover class is {cls}.",0.62)


def execute(query, files, cfg, out_dir, classifier):
    t0=time.time(); task=route(query,len(files)); trace=[]
    trace.append({'step':'query_route','task':task,'tool':'keyword_agent_router'})
    arrays=[]; metas=[]
    for f in files:
        arr,meta=load_raster(f); arrays.append(arr); metas.append(meta)
    trace.append({'step':'input_validation','tool':'rasterio','files':len(files),'modalities':[m['count'] for m in metas]})

    red=cfg.get('red_band'); green=cfg.get('green_band'); nir=cfg.get('nir_band')
    red = red-1 if isinstance(red,int) and red>0 else red
    green = green-1 if isinstance(green,int) and green>0 else green
    nir = nir-1 if isinstance(nir,int) and nir>0 else nir

    if task in ('CAPTION','VQA'):
        arr=arrays[0]
        feat,_=image_features(arr,red,green,nir,sar_band=0 if arr.shape[0]==1 else None)
        if classifier:
            cls, probs = classifier(arr)
        else:
            cls, probs='unknown',[]
        trace.append({'step':'visual_adaptation','tool':'MobileNetV3-EuroSAT-remote-sensing-finetune','output_class':cls})
        if task=='CAPTION':
            ans=class_caption(cls,probs,feat); conf=0.72 if probs else 0.50
        else:
            ans,conf=answer_vqa(query,feat,cls)
        return {'answer':ans,'task':task,'confidence':round(float(conf),3),'evidence':{'predicted_land_cover':cls,'features':feat,'metadata':metas[0]},'execution_trace':trace,'latency_ms':round((time.time()-t0)*1000,1)}

    if task=='CHANGE':
        out_path=Path(out_dir)/f'change_{int(time.time()*1000)}.jpg'
        pct,map_path,metrics=change_map(arrays[0],arrays[1],out_path)
        trace.append({'step':'change_detection','tool':'optical_difference_otsu','changed_area_percent':round(pct,2)})
        direction='limited visible change' if pct<5 else ('moderate spatial change' if pct<20 else 'substantial spatial change')
        ans=f"The two co-registered images show {direction}, with approximately {pct:.1f}% of pixels flagged by the demo change detector."
        if 'increase' in query.lower() or 'decrease' in query.lower():
            ans += ' Class-specific increase/decrease requires calibrated labels or masks; the current result is an evidence map rather than a categorical land-cover transition label.'
        return {'answer':ans,'task':'CHANGE','confidence':round(max(0.45,min(0.9,0.45+pct/50)),3),'evidence':{'changed_area_percent':pct,'metrics':metrics,'metadata':metas},'visuals':[{'type':'change_map','path':'/'+Path(map_path).name}],'execution_trace':trace,'latency_ms':round((time.time()-t0)*1000,1)}

    # FUSION
    opt,sar=arrays[0],arrays[1]
    feat,interp=optical_sar_fusion(opt,sar,red,green,nir)
    trace.append({'step':'cross_modal_fusion','tool':'optical_indices_plus_SAR_backscatter_statistics'})
    ans=' '.join(interp) if interp else 'The optical and SAR inputs were processed jointly, but the available bands did not provide enough evidence for a strong semantic conclusion.'
    return {'answer':ans,'task':'FUSION','confidence':0.60 if interp else 0.42,'evidence':{'fusion_features':feat,'metadata':metas},'execution_trace':trace,'latency_ms':round((time.time()-t0)*1000,1)}
