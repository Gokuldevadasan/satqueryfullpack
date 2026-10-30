import argparse,time,json
from pathlib import Path
import numpy as np
def bench(path,channels,shape,n=50):
    import onnxruntime as ort
    s=ort.InferenceSession(str(path),providers=["CPUExecutionProvider"]); x=np.random.randn(1,channels,*shape).astype("float32"); name=s.get_inputs()[0].name; [s.run(None,{name:x}) for _ in range(5)]; t=[]
    for _ in range(n): a=time.perf_counter();s.run(None,{name:x});t.append((time.perf_counter()-a)*1000)
    return {"model":str(path),"size_mb":path.stat().st_size/1024**2,"average_latency_ms":float(np.mean(t)),"p50_latency_ms":float(np.percentile(t,50)),"p95_latency_ms":float(np.percentile(t,95))}
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--runs",type=int,default=50);a=ap.parse_args(); results=[]
    for p,c,sh in [(Path("models/satquery_rgb_v11.onnx"),3,(224,224)),(Path("models/satquery_spectral.onnx"),13,(64,64))]:
        if p.exists(): results.append(bench(p,c,sh,a.runs))
    Path("reports/benchmark_results.json").write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
