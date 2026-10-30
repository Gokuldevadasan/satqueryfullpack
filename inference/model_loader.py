"""Cached ONNX Runtime discovery/loading with actionable diagnostics."""
from functools import lru_cache
from .model_router import MODELS

def model_record(key):
    path=MODELS[key].resolve(); data=path.with_name(path.name+".data")
    return {"path":str(path),"onnx_exists":path.is_file(),"external_data_exists":data.is_file(),"external_data_path":str(data)}

@lru_cache(maxsize=3)
def load_session(key):
    import onnxruntime as ort
    record=model_record(key)
    if not record["onnx_exists"]: raise FileNotFoundError(f"{key} ONNX model is missing: {record['path']}")
    try: return ort.InferenceSession(record["path"],providers=["CPUExecutionProvider"])
    except Exception as exc: raise RuntimeError(f"Unable to load {key} ONNX model at {record['path']}: {exc}") from exc

def model_info(key,load=False):
    result=model_record(key); result["available"]=result["onnx_exists"]
    if load and result["available"]:
        try:
            session=load_session(key); result.update(loaded=True,inputs=[{"name":x.name,"shape":x.shape,"type":x.type} for x in session.get_inputs()],outputs=[{"name":x.name,"shape":x.shape,"type":x.type} for x in session.get_outputs()])
        except Exception as exc: result.update(loaded=False,error=str(exc))
    return result
