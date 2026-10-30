import argparse,json
from pathlib import Path
from collections import Counter
from tqdm import tqdm

def validate(root, expected_bands):
    root=Path(root); files=[p for p in root.rglob("*") if p.suffix.lower() in {".jpg",".jpeg",".png",".tif",".tiff"}]; issues=[]; seen=set()
    for p in tqdm(files,desc=f"Validating {root.name}"):
        rel=str(p.relative_to(root))
        if rel in seen: issues.append({"path":rel,"issue":"duplicate_path"})
        seen.add(rel)
        try:
            import numpy as np
            if p.suffix.lower() in {".tif",".tiff"}:
                import rasterio
                with rasterio.open(p) as d: arr=d.read(); channels=d.count
            else:
                from PIL import Image
                with Image.open(p) as im: arr=np.asarray(im); channels=arr.shape[-1] if arr.ndim==3 else 1
            if channels != expected_bands: issues.append({"path":rel,"issue":"incorrect_channels","actual":channels,"expected":expected_bands})
            if not np.isfinite(arr).all(): issues.append({"path":rel,"issue":"nan_or_infinity"})
            if not p.parent.name: issues.append({"path":rel,"issue":"missing_label"})
        except Exception as e: issues.append({"path":rel,"issue":"corrupted","error":str(e)})
    return {"root":str(root),"checked":len(files),"valid":len(files)-len({x['path'] for x in issues}),"issues":issues}
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--rgb",default="data/EuroSAT"); ap.add_argument("--spectral",default="data/EuroSATallBands"); ap.add_argument("--output",default="reports/dataset_validation.json"); a=ap.parse_args()
    out={"rgb":validate(a.rgb,3),"spectral":validate(a.spectral,13)}; Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2)); print(json.dumps({k:{x:v for x,v in r.items() if x!='issues'} for k,r in out.items()},indent=2))
