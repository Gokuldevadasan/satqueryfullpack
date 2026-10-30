import argparse
from pathlib import Path
import numpy as np
import torch
from training.model_rgb import create_rgb_model
from training.model_spectral import create_spectral_model

def export(model, checkpoint, output, channels):
    state=torch.load(checkpoint,map_location="cpu"); model.load_state_dict(state.get("model_state",state.get("model"))); model.eval(); x=torch.randn(1,channels,224 if channels==3 else 64,224 if channels==3 else 64)
    torch.onnx.export(model,x,output,input_names=["image"],output_names=["logits"],dynamic_axes={"image":{0:"batch"},"logits":{0:"batch"}},opset_version=17)
    import onnxruntime as ort
    diff=np.max(np.abs(model(x).detach().numpy()-ort.InferenceSession(str(output),providers=["CPUExecutionProvider"]).run(None,{"image":x.numpy()})[0])); print(f"{output}: maximum output difference = {diff:.8g}")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--rgb-checkpoint",default="models/satquery_rgb_v11.pt"); ap.add_argument("--spectral-checkpoint",default="models/satquery_spectral_best.pt"); ap.add_argument("--models-dir",default="models"); a=ap.parse_args(); d=Path(a.models_dir)
    if Path(a.rgb_checkpoint).exists(): export(create_rgb_model(pretrained=False),a.rgb_checkpoint,d/"satquery_rgb_v11.onnx",3)
    if Path(a.spectral_checkpoint).exists(): export(create_spectral_model(),a.spectral_checkpoint,d/"satquery_spectral.onnx",13)
