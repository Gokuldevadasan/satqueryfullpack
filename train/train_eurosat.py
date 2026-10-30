import argparse, json, os
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader, random_split, Subset
from torchvision import datasets, transforms, models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data')
    ap.add_argument('--epochs', type=int, default=5)
    ap.add_argument('--batch', type=int, default=64)
    ap.add_argument('--lr', type=float, default=3e-4)
    ap.add_argument('--limit', type=int, default=0, help='0 = full dataset; useful for a fast demo')
    ap.add_argument('--out', default='models')
    args = ap.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Device:', device)

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_base = datasets.EuroSAT(args.data, transform=train_tf, download=True)
    eval_base = datasets.EuroSAT(args.data, transform=eval_tf, download=False)
    n = len(train_base)
    g = torch.Generator().manual_seed(42)
    indices = torch.randperm(n, generator=g).tolist()
    if args.limit and args.limit < n:
        indices = indices[:args.limit]
        print(f'Using subset: {len(indices)} samples')
    else:
        print(f'Using full EuroSAT RGB dataset: {n} samples')
    val_size = max(1, int(0.15 * len(indices)))
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    train_ds = Subset(train_base, train_indices)
    val_ds = Subset(eval_base, val_indices)

    # EuroSAT is small enough that the same transform pipeline is fine for a demo.
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0, pin_memory=device.type=='cuda')
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=0, pin_memory=device.type=='cuda')

    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, 10)
    model.to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    best = 0.0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        total_loss = total = correct = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
            total_loss += loss.item() * y.size(0)
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)

        model.eval(); vtotal = vcorrect = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                pred = model(x).argmax(1)
                vcorrect += (pred == y).sum().item(); vtotal += y.size(0)
        va = vcorrect / max(vtotal, 1)
        ta = correct / max(total, 1)
        print(f'Epoch {epoch+1}/{args.epochs} loss={total_loss/total:.4f} train_acc={ta:.3f} val_acc={va:.3f}')
        if va > best:
            best = va
            torch.save({'model': model.state_dict(), 'classes': train_base.classes}, out/'eurosat_mobilenet_best.pt')

    # Export ONNX for Raspberry Pi/ONNX Runtime.
    model.eval().cpu()
    dummy = torch.randn(1, 3, 224, 224)
    onnx_path = out/'eurosat_mobilenet.onnx'
    torch.onnx.export(
        model, dummy, onnx_path,
        input_names=['image'], output_names=['logits'],
        dynamic_axes={'image': {0: 'batch'}, 'logits': {0: 'batch'}},
        opset_version=17,
    )
    classes = train_base.classes
    (out/'classes.json').write_text(json.dumps(classes, indent=2))
    print('Saved:', onnx_path)
    print('Best validation accuracy:', best)

if __name__ == '__main__':
    main()
