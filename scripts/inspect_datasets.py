import argparse, json
from collections import Counter
from pathlib import Path

def inspect(root):
    root=Path(root); files=[p for p in root.rglob("*") if p.suffix.lower() in {".jpg",".jpeg",".png",".tif",".tiff"}]
    classes=sorted({p.parent.name for p in files}); dims=Counter(); bands=Counter(); corrupt=[]
    for p in files:
        try:
            if p.suffix.lower() in {".tif",".tiff"}:
                import rasterio
                with rasterio.open(p) as d: dims[(d.width,d.height)]+=1; bands[d.count]+=1
            else:
                from PIL import Image
                with Image.open(p) as im: dims[im.size]+=1; bands[len(im.getbands())]+=1
        except Exception as e: corrupt.append({"path":str(p),"error":str(e)})
    counts=Counter(p.parent.name for p in files); values=list(counts.values())
    return {"root":str(root),"files":len(files),"classes":classes,"samples_per_class":dict(counts),"dimensions":{str(k):v for k,v in dims.items()},"channel_or_band_counts":dict(bands),"contains_13_bands":13 in bands,"corrupted_files":corrupt,"missing_files":[],"class_imbalance_ratio":max(values)/min(values) if values else None}
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--rgb",default="data/EuroSAT"); ap.add_argument("--spectral",default="data/EuroSATallBands"); a=ap.parse_args()
    print(json.dumps({"rgb":inspect(a.rgb),"spectral":inspect(a.spectral)},indent=2))
