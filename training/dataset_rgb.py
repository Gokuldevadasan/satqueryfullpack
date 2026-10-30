from pathlib import Path
import csv
from PIL import Image
from torch.utils.data import Dataset

class EuroSATRGBDataset(Dataset):
    def __init__(self, root, split="train", transform=None):
        self.root, self.transform = Path(root), transform
        with (self.root / f"{split}.csv").open(newline="") as f: rows = list(csv.DictReader(f))
        self.samples = [(self.root / r["Filename"], int(r["Label"])) for r in rows if r.get("Filename") and r.get("Label") not in (None, "")]
    def __len__(self): return len(self.samples)
    def __getitem__(self, i):
        p, y = self.samples[i]
        with Image.open(p) as im: image = im.convert("RGB")
        return (self.transform(image) if self.transform else image), y
