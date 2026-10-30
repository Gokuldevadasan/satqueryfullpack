from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RGB_DATA = ROOT / "data" / "EuroSAT"
SPECTRAL_DATA = ROOT / "data" / "EuroSATallBands"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
CHECKPOINTS = ROOT / "checkpoints"
NUM_CLASSES = 10
SPECTRAL_BANDS = 13
DEFAULT_BAND_MEAN = [0.0] * SPECTRAL_BANDS
DEFAULT_BAND_STD = [1.0] * SPECTRAL_BANDS
