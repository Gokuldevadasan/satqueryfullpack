import argparse
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from training.dataset_spectral import EuroSATSpectralDataset
from training.model_spectral import create_spectral_model
from training.metrics import classification_metrics, save_metrics
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--checkpoint',default='models/satquery_spectral_best.pt');ap.add_argument('--data',default='data/EuroSATallBands');ap.add_argument('--batch-size',type=int,default=64);ap.add_argument('--device',default='cpu');a=ap.parse_args()
    model=create_spectral_model();state=torch.load(a.checkpoint,map_location=a.device);model.load_state_dict(state.get('model_state',state.get('model')));model.to(a.device).eval();ys=[];ps=[]
    with torch.no_grad():
        for x,y in DataLoader(EuroSATSpectralDataset(a.data,'test'),batch_size=a.batch_size): ys+=y.tolist();ps+=model(x.to(a.device)).argmax(1).cpu().tolist()
    m=classification_metrics(ys,ps);save_metrics(m);print(m)
if __name__=='__main__':main()
