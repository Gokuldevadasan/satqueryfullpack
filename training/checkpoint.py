from pathlib import Path
import torch

def save_checkpoint(path, model, optimizer, scheduler, epoch, best_accuracy, config):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict() if scheduler else None, "epoch": epoch, "best_accuracy": best_accuracy, "config": config}, path)

def load_checkpoint(path, model, optimizer=None, scheduler=None, device="cpu"):
    state = torch.load(path, map_location=device)
    model.load_state_dict(state.get("model_state", state.get("model")))
    if optimizer and state.get("optimizer_state"): optimizer.load_state_dict(state["optimizer_state"])
    if scheduler and state.get("scheduler_state"): scheduler.load_state_dict(state["scheduler_state"])
    return state
