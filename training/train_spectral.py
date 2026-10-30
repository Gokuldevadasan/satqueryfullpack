import argparse, time
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from training.dataset_spectral import EuroSATSpectralDataset
from training.model_spectral import create_spectral_model, model_summary
from training.checkpoint import save_checkpoint, load_checkpoint
from training.metrics import classification_metrics, save_metrics

def run_epoch(model, loader, criterion, optimizer, device, title):
    train=optimizer is not None; model.train(train); total=correct=0; loss_sum=0; ys=[]; ps=[]; start=time.time()
    bar=tqdm(loader,desc=title,unit="batch")
    for x,y in bar:
        x,y=x.to(device),y.to(device)
        with torch.set_grad_enabled(train):
            logits=model(x); loss=criterion(logits,y)
            if train: optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
        n=y.size(0); total+=n; loss_sum+=loss.item()*n; pred=logits.argmax(1); correct+=(pred==y).sum().item(); ys+=y.cpu().tolist(); ps+=pred.cpu().tolist()
        bar.set_postfix(loss=f"{loss_sum/total:.4f}",acc=f"{100*correct/total:.2f}%",lr=(optimizer.param_groups[0]['lr'] if train else '-'),samples_s=f"{total/max(time.time()-start,.01):.0f}")
    return loss_sum/max(total,1),correct/max(total,1),ys,ps
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/EuroSATallBands"); ap.add_argument("--epochs",type=int,default=30); ap.add_argument("--batch-size",type=int,default=64); ap.add_argument("--lr",type=float,default=.001); ap.add_argument("--workers",type=int,default=0); ap.add_argument("--patience",type=int,default=7); ap.add_argument("--resume"); ap.add_argument("--output-dir",default="models"); ap.add_argument("--device",default=None); a=ap.parse_args()
    device=torch.device(a.device or ("cuda" if torch.cuda.is_available() else "cpu")); model=create_spectral_model().to(device); print("Device:",device,model_summary(model))
    tr=DataLoader(EuroSATSpectralDataset(a.data,"train",augment=True),batch_size=a.batch_size,shuffle=True,num_workers=a.workers,pin_memory=device.type=="cuda"); va=DataLoader(EuroSATSpectralDataset(a.data,"validation"),batch_size=a.batch_size,num_workers=a.workers)
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=1e-4); sch=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,mode="max",patience=2,factor=.5); crit=torch.nn.CrossEntropyLoss(); best=0.; begin=0; cfg=vars(a)
    if a.resume:
        s=load_checkpoint(a.resume,model,opt,sch,device); begin=s["epoch"]+1; best=s.get("best_accuracy",0.)
    ck=Path("checkpoints"); out=Path(a.output_dir); ck.mkdir(exist_ok=True); out.mkdir(exist_ok=True); stale=0
    for epoch in range(begin,a.epochs):
        print(f"Epoch {epoch+1}/{a.epochs}"); tl,ta,_,_=run_epoch(model,tr,crit,opt,device,"Train"); vl,acc,ys,ps=run_epoch(model,va,crit,None,device,"Validation"); sch.step(acc); print(f"Val Loss: {vl:.4f}  Val Acc: {acc:.2%}")
        save_checkpoint(ck/"spectral_last.pt",model,opt,sch,epoch,best,cfg)
        if acc>best:
            best=acc; stale=0; save_checkpoint(ck/"spectral_best.pt",model,opt,sch,epoch,best,cfg); torch.save({"model_state":model.state_dict(),"classes":[]},out/"satquery_spectral_best.pt"); print("✓ NEW BEST MODEL")
        else: stale+=1
        if stale>=a.patience: print(f"Early stopping triggered.\nBest epoch: {epoch-stale+1}\nBest validation accuracy: {best:.2%}"); break
    save_metrics(classification_metrics(ys,ps),"reports/training_results.json")
if __name__=="__main__": main()
