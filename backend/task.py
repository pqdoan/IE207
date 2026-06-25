"""demoflwr: A Flower / PyTorch app."""

import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
import torch.nn.functional as F
import torch.optim as optim

class ImprovedCNN(nn.Module):
    def __init__(self, num_classes=12):
        super().__init__()
        # Conv block 1
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        # Conv block 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        # Conv block 3
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        # Fully connected layers
        self.fc1 = nn.Linear(128*8*8, 256)  # 64x64 -> 32 ->16 ->8 after pooling
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)

        self.pool = nn.MaxPool2d(2, 2)
    
    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class SimpleCNN(nn.Module):
    def __init__(self, num_classes=12, num_filters_conv1=32, num_filters_conv2=64, fc1_neurons=128, image_size=64):
        super().__init__()
        self.conv_layer1 = nn.Sequential(
            nn.Conv2d(1, num_filters_conv1, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        image_size = image_size // 2
        self.conv_layer2 = nn.Sequential(
            nn.Conv2d(num_filters_conv1, num_filters_conv2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        image_size = image_size // 2
        
        self.fc_layers = nn.Sequential(
            nn.Linear(image_size * image_size * num_filters_conv2, fc1_neurons),
            nn.ReLU(),
            nn.Linear(fc1_neurons, num_classes)
        )

    def forward(self, x):
        x = self.conv_layer1(x)
        x = self.conv_layer2(x)
        x = x.view(x.size(0), -1) # Flatten the output for the linear layers
        x = self.fc_layers(x)
        return x
    
def train(model, trainLoader, epochs, lr, device):
    model.to(device)
    lossFn = torch.nn.CrossEntropyLoss().to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    # optimizer = optim.Adam(model.parameters(), lr=0.001)
    model.train()
    for epoch in range(epochs):
        for inputs, lables in trainLoader:
            inputs, lables = inputs.to(device), lables.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = lossFn(outputs, lables)
            loss.backward()
            optimizer.step()


def test(model, testLoader, device):
    model.eval()
    loss_fn = torch.nn.CrossEntropyLoss()
    correct, running_loss, total_test = 0, 0.0, 0

    with torch.no_grad():
        for inputs, lables in testLoader:
            inputs, lables = inputs.to(device), lables.to(device)
            outputs = model(inputs)
            loss = loss_fn(outputs, lables)
            running_loss += loss.item() * inputs.size(0)
            predicted = torch.argmax(outputs, 1)
            total_test += lables.size(0)
            correct += (predicted == lables).sum().item()

    test_loss = running_loss / len(testLoader.dataset)
    test_accuracy = 100 * correct / total_test

    return test_loss, test_accuracy

class MappedDataset(torch.utils.data.Dataset):
    def __init__(self, subset, label_map):
        self.subset = subset
        self.label_map = label_map

    def __len__(self):
        return len(self.subset)
    
    def __getitem__(self, idx):
        x, y = self.subset[idx]
        # Nếu nhãn có trong map thì đổi, ngược lại giữ nguyên
        y = self.label_map.get(y, y)
        return x, y


def load_data(id, randomseed):

    transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((64,64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])
    
    if(id == 1):
        dataset = torchvision.datasets.ImageFolder(root='../client1', transform=transform)
    elif(id == 2):
        dataset = torchvision.datasets.ImageFolder(root='../client2', transform=transform)
    elif(id == 3):
        dataset = torchvision.datasets.ImageFolder(root='../client3', transform=transform)
    elif(id == 4):
        dataset = torchvision.datasets.ImageFolder(root='../client4', transform=transform)
    else:
        raise ValueError("Invalid client ID.")

    train_ratio = 0.8
    size = len(dataset)
    train_size = int(train_ratio * size)
    test_size = size - train_size

    generator = torch.Generator().manual_seed(randomseed)
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size], generator=generator)

    train_dataset, test_dataset = mappingLable(id, train_dataset, test_dataset)

    batch_size = 32
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader

def mappingLable(id, train, test):
    #Mapped Lables
    lable_map1 = {0: 0, 1: 1, 2: 2, 3: 3}
    lable_map2 = {0: 4, 1: 5, 2: 6, 3: 7}
    lable_map3 = {0: 8, 1: 9}
    lable_map4 = {0: 10, 1: 11}

    if id == 1:
        trainset = MappedDataset(train, label_map=lable_map1)
        testset = MappedDataset(test, label_map=lable_map1)
    elif id == 2:
        trainset = MappedDataset(train, label_map=lable_map2)
        testset = MappedDataset(test, label_map=lable_map2)
    elif id == 3:
        trainset = MappedDataset(train, label_map=lable_map3)
        testset = MappedDataset(test, label_map=lable_map3)
    elif id == 4:
        trainset = MappedDataset(train, label_map=lable_map4)
        testset = MappedDataset(test, label_map=lable_map4)

    return trainset, testset












