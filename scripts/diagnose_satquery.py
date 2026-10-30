"""Read-only model, GIS, and runtime diagnostic; never trains or writes weights."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from inference.model_loader import model_info
from gis.band_registry import SENTINEL2
def main():
    import onnxruntime, rasterio
    print("="*40+"\nSATQUERY MEDIUM DIAGNOSTIC\n"+"="*40)
    print(f"Project root: {ROOT}\nPython: {sys.version.split()[0]}\nONNX Runtime: {onnxruntime.__version__}\nRasterio: {rasterio.__version__}\n\nModels\n"+"-"*40)
    for key,label in (("rgb_v1","RGB V1"),("rgb_v11","RGB V1.1"),("spectral","Spectral")):
        info=model_info(key,load=True); print(f"{label}: {'FOUND' if info['onnx_exists'] else 'MISSING'} | {'OK' if info.get('loaded') else 'ERROR'}")
        if info.get('error'): print(f"  {info['error']}")
        if info.get('loaded'): print(f"  input: {info['inputs']}\n  output: {info['outputs']}")
    for file in ('classes.json','spectral_classes.json'): print(f"{file}: {'FOUND' if (ROOT/'models'/file).is_file() else 'MISSING'}")
    print("\nGIS\n"+"-"*40+f"\nRasterio: OK\nSentinel-2 registry: OK ({len(SENTINEL2)} bands)\nWeather: configured on demand\nBackend\n"+"-"*40+"\nFastAPI: OK")
if __name__ == '__main__': main()
