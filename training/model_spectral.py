"""Small 13-band MobileNetV3 classifier suitable for CPU edge inference."""
from pathlib import Path
import torch
from torch import nn
from torchvision import models

def create_spectral_model(num_classes=10, pretrained=False):
    weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    model = models.mobilenet_v3_small(weights=weights)
    old = model.features[0][0]
    conv = nn.Conv2d(13, old.out_channels, old.kernel_size, old.stride, old.padding, bias=False)
    with torch.no_grad():
        if pretrained:
            conv.weight.copy_(old.weight.mean(dim=1, keepdim=True).repeat(1, 13, 1, 1) / 13.0 * 3.0)
    model.features[0][0] = conv
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    return model

def model_summary(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"parameters": total, "trainable_parameters": trainable, "estimated_fp32_mb": round(total * 4 / 1024**2, 2)}

if __name__ == "__main__":
    print(model_summary(create_spectral_model()))
