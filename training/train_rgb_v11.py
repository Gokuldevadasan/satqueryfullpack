import argparse
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from training.dataset_rgb import EuroSATRGBDataset
from training.augmentations import rgb_transforms
from training.model_rgb import create_rgb_model
from training.train_spectral import run_epoch
from training.checkpoint import save_checkpoint, load_checkpoint
from training.metrics import classification_metrics, save_metrics
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/EuroSAT"); ap.add_argument("--base-model",default="models/eurosat_mobilenet_best.pt"); ap.add_argument("--epochs",type=int,default=15); ap.add_argument("--batch-size",type=int,default=64); ap.add_argument("--lr",type=float,default=3e-4); ap.add_argument("--workers",type=int,default=0); ap.add_argument("--patience",type=int,default=7); ap.add_argument("--resume"); ap.add_argument("--device",default=None); a=ap.parse_args(); dev=torch.device(a.device or ("cuda" if torch.cuda.is_available() else "cpu")); model=create_rgb_model(pretrained=False).to(dev)
    if a.resume: state=load_checkpoint(a.resume,model,device=dev)
    else: model.load_state_dict(torch.load(a.base_model,map_location=dev).get("model",torch.load(a.base_model,map_location=dev).get("model_state")))
    tr=DataLoader(EuroSATRGBDataset(a.data,"train",rgb_transforms(True)),batch_size=a.batch_size,shuffle=True,num_workers=a.workers); va=DataLoader(EuroSATRGBDataset(a.data,"validation",rgb_transforms(False)),batch_size=a.batch_size,num_workers=a.workers)
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=1e-4); sch=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,"max",patience=2); loss=torch.nn.CrossEntropyLoss(label_smoothing=.1); best=0; stale=0
    for ep in range(a.epochs):
        print(f"Epoch {ep+1}/{a.epochs}"); run_epoch(model,tr,loss,opt,dev,"Train"); vl,acc,ys,ps=run_epoch(model,va,loss,None,dev,"Validation"); sch.step(acc); save_checkpoint("checkpoints/rgb_v11_last.pt",model,opt,sch,ep,best,vars(a))
        if acc>best: best=acc; stale=0; torch.save({"model_state":model.state_dict()},"models/satquery_rgb_v11.pt"); print("✓ NEW BEST MODEL")
        else: stale+=1
        if stale>=a.patience: print("Early stopping triggered."); break
    save_metrics(classification_metrics(ys,ps))
if __name__=="__main__": main()
