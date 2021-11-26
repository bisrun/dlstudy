import torch
from mnist import Net
from torchvision import datasets, transforms
import torch
from torchvision import datasets, transforms

#device = 'cuda' if torch.cuda.is_available() else 'cpu'
#cuda = torch.device('cuda')

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

test_loader = torch.utils.data.DataLoader(
    datasets.MNIST('data', train=False, transform=transform))

import torch.nn as nn
model = Net()

#model load
model = torch.load("data/model/model10.m")

def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
#    model.eval()
    test_loss, correct = 0, 0
    total_loop = 0
    with torch.no_grad():
        for X, y in dataloader:
            one_y = model.one_hot_encode(y)
            #, y = X.to(device), y.to(device)
            pred = model.forward_pass(torch.flatten(X))
            test_loss += loss_fn(pred, one_y)
            correct += (pred.max(dim=0)[1] == y).type(torch.float).sum().item()
            #print(correct, test_loss, y, pred.max(dim=0)[1])
            total_loop = total_loop + 1  ;

    test_loss /= num_batches
    test_correct = correct / size
    print(f"Test Error: \n Accuracy: {(100*test_correct):>0.1f}%, Avg loss: {test_loss:>8f}  {correct:>0.3f} {total_loop:>d} \n")

criterion = nn.BCEWithLogitsLoss()
test(test_loader, model, criterion )
print("Done!")

#test



