from pathlib import Path
import csv
import numpy as np
import torch
from torch.utils.data import Dataset

class EuroSATSpectralDataset(Dataset):
    """13-band GeoTIFF dataset; spatial augmentation is shared by every band."""
    def __init__(self, root, split="train", mean=None, std=None, size=64, augment=False):
        self.root, self.size, self.augment = Path(root), size, augment
        self.mean = np.asarray(mean if mean is not None else [0.] * 13, dtype=np.float32)[:, None, None]
        self.std = np.maximum(np.asarray(std if std is not None else [1.] * 13, dtype=np.float32)[:, None, None], 1e-6)
        with (self.root / f"{split}.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        self.samples = [(self.root / r["Filename"], int(r["Label"])) for r in rows if r.get("Filename") and r.get("Label") not in (None, "")]
    def __len__(self): return len(self.samples)
    def __getitem__(self, index):
        path, label = self.samples[index]
        import rasterio
        with rasterio.open(path) as ds:
            arr = ds.read(out_shape=(ds.count, self.size, self.size), resampling=rasterio.enums.Resampling.bilinear).astype(np.float32)
        if arr.shape[0] != 13: raise ValueError(f"Expected 13 bands, got {arr.shape[0]}: {path}")
        arr = (arr - self.mean) / self.std
        if self.augment:
            if np.random.rand() < .5: arr = arr[:, :, ::-1].copy()
            if np.random.rand() < .5: arr = arr[:, ::-1, :].copy()
        return torch.from_numpy(arr), label
