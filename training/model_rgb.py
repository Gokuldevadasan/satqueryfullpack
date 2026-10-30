from torch import nn
from torchvision import models

def create_rgb_model(num_classes=10, pretrained=True):
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    return model
