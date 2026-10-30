from torchvision import transforms

def rgb_transforms(train=False):
    ops = [transforms.Resize((224, 224))]
    if train: ops += [transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(), transforms.RandomRotation(10)]
    return transforms.Compose(ops + [transforms.ToTensor(), transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
