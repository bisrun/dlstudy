

import torch
import torchvision.datasets as dsets
import torchvision.transforms as transforms
import torch.nn.init
from collections import OrderedDict

device = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.manual_seed(777)
if device =='cuda':
    torch.cuda.manual_seed_all(777)


training_epochs = 10
batch_size = 100
test_result = []
train_result =[]
#dataloader
mnist_train = dsets.MNIST(root = 'MNIST_data/',
                          train = True,
                          transform = transforms.ToTensor(),
                          download=True)
mnist_test = dsets.MNIST(root = 'MNIST_data/',
                         train = False,
                         transform = transforms.ToTensor(),
                         download=True)

data_loader = torch.utils.data.DataLoader(dataset = mnist_train,
                                          batch_size =batch_size,
                                          shuffle = True,
                                          drop_last = True)

print("step1")



class CNN_parameter():
    def __init__(self, fn_pool, fn_fcinit, fn_act, fn_optim, lr, casename ):
        self.fn_pool = fn_pool
        self.fn_fcinit= fn_fcinit
        self.fn_act = fn_act
        self.fn_optim = fn_optim
        self.lr = lr
        self.paramter_name = casename


class Training_result():
    def __init__(self, pool_nm, fcinit_nm, act_nm, optim_nm, lr,  epoch, cost, accuracy, casename):
        self.pool_nm = pool_nm
        self.fcinit_nm= fcinit_nm
        self.act_nm = act_nm
        self.optim_nm = optim_nm
        self.lr = lr
        self.epoch = epoch
        self.cost = cost
        self.accuracy = accuracy
        self.casename = casename

class Test_result():
    def __init__(self, pool_nm, fcinit_nm, act_nm, optim_nm, lr,  accuracy, casename):
        self.pool_nm = pool_nm
        self.fcinit_nm= fcinit_nm
        self.act_nm = act_nm
        self.optim_nm = optim_nm
        self.lr = lr
        self.accuracy = accuracy
        self.casename = casename



class CNN(torch.nn.Module):
    def __init__(self, nn_param:CNN_parameter ):
        super(CNN,self).__init__()
        self.keep_prob = 0.5
        #L1 image in shape = (?,28,28,1)
        #    conv -> (?, 28, 28, 6)
        #    pool -> (?, 14, 14, 6)
        self.layer1 = torch.nn.Sequential(
            torch.nn.Conv2d(1, 6, kernel_size=5, stride=1, padding=2),
            nn_param.fn_act[1](),
            nn_param.fn_pool[1](kernel_size=2,stride=2)
        )

        #L2 image in shape = (?, 14,14,6)
        #   conv -> (?,10,10,16)
        #   pool -> (?,5,5,16)
        self.layer2 = torch.nn.Sequential(
            torch.nn.Conv2d(6, 16 , kernel_size=5 ,stride=1, padding=0),
            nn_param.fn_act[1](),
            nn_param.fn_pool[1](kernel_size=2,stride=2)
        )

        #Fully connected Layer 5*5*16
        self.fc1 = torch.nn.Linear(5*5*16, 120, bias=True)
        nn_param.fn_fcinit[1](self.fc1.weight)

        self.layer3 = torch.nn.Sequential(
            self.fc1,
            nn_param.fn_act[1]()
            #,torch.nn.Dropout(p=1-self.keep_prob)
        )
        #Fully connected Layer 120->84
        self.fc2 = torch.nn.Linear(120, 84, bias=True)
        nn_param.fn_fcinit[1](self.fc2.weight)
        self.layer4 = torch.nn.Sequential(
            self.fc2,
            nn_param.fn_act[1]()
        )
        self.fc3 = torch.nn.Linear(84, 10, bias=True)
        nn_param.fn_fcinit[1](self.fc3.weight)

    def forward(self,x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.view(out.size(0), -1)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.fc3(out)
        return out


print("step2")


net_param_pool = OrderedDict([("max",torch.nn.MaxPool2d), ("avg",torch.nn.AvgPool2d)])

net_param_init =OrderedDict()
net_param_init["xavier"]= torch.nn.init.xavier_uniform_
net_param_init["uniform_"]= torch.nn.init.uniform_
net_param_init["kaiming"]= torch.nn.init.kaiming_uniform_

net_param_activate =OrderedDict()
net_param_activate["ReLU"]= torch.nn.ReLU
net_param_activate["Tanh"]= torch.nn.Tanh
net_param_activate["LeakyReLU"]= torch.nn.LeakyReLU
net_param_activate["Sigmoid"]= torch.nn.Sigmoid

net_param_learning_rate=OrderedDict()
net_param_learning_rate["0.1"]= 0.1
net_param_learning_rate["0.01"]= 0.01
net_param_learning_rate["0.001"]= 0.001
net_param_learning_rate["0.0001"]=  0.0001

net_param_optimizer=OrderedDict()
net_param_optimizer["Adam"]= torch.optim.Adam
net_param_optimizer["SGD"]= torch.optim.SGD



net_params = []
for pool_k, pool_v in net_param_pool.items():
    for init_k, init_v,  in net_param_init.items():
        for act_k, act_v in net_param_activate.items():
            for opt_k, opt_v in net_param_optimizer.items():
                for lr_k, lr_v in net_param_learning_rate.items():
                    net_params.append(
                        CNN_parameter((pool_k,pool_v),
                                      (init_k,init_v),
                                      (act_k,act_v),
                                      (opt_k,opt_v),
                                      (lr_k,lr_v),
                                      "[pool={}][init={}][act={}][opt={}][lr={}]".
                                      format(pool_k, init_k, act_k,opt_k, lr_k)))

print("step3")

#start training
def Test_MNIST(model, np):


    with torch.no_grad():
        X_test = mnist_test.test_data.view(len(mnist_test), 1, 28, 28).float().to(device)
        Y_test = mnist_test.test_labels.to(device)

        prediction = model(X_test)
        correct_prediction = torch.argmax(prediction, dim = 1) ==Y_test
        accuracy = correct_prediction.float().mean()
        print(np.paramter_name, "Accuracy : ", accuracy.item())
        test_result.append(Test_result(np.fn_pool[0], np.fn_fcinit[0], np.fn_act[0], np.fn_optim[0], np.lr[0],
                                           accuracy, np.paramter_name))

#training
def training_loop():
    for i, np in enumerate(net_params):
        print(i, np.paramter_name)
        model = CNN(np).to(device)
        criterion = torch.nn.CrossEntropyLoss().to(device)
        optimizer = np.fn_optim[1](model.parameters(), lr=np.lr[1])
        total_batch = len(data_loader)
        print("total batch  ", total_batch)

        for epoch in range(training_epochs):
            avg_cost = 0
            true_count = 0

            for X, Y in data_loader:
                X=X.to(device)
                Y=Y.to(device)

                optimizer.zero_grad()
                hypothesys = model(X)
                cost = criterion(hypothesys, Y)
                cost.backward()
                optimizer.step()
                correct_prediction = torch.argmax(hypothesys, dim = 1) ==Y
                true_count += correct_prediction.float().sum()

                avg_cost += cost / total_batch

            accuracy = true_count/total_batch
            print("epoch={:>4}\tcost={:>.9f}\taccuracy={:>.9f}\ttrue={}".format(
                epoch+1, avg_cost, accuracy, true_count))
            train_result.append(Training_result(np.fn_pool[0], np.fn_fcinit[0], np.fn_act[0], np.fn_optim[0], np.lr[0],
                                                epoch, cost, accuracy, np.paramter_name))
            #train_cnt = len(train_result)

        # test

        model_filepath="model/m{}.m".format(np.paramter_name)
        torch.save(model, model_filepath)
        Test_MNIST(model, np )

    train_file = open("result/train.txt", mode='wt', encoding='utf-8')
    train_file.write("SN,POOL,INIT,ACTIVATE,OPTIM,LR,EPOCH,COST,ACCURACY\n")
    for i, res in enumerate(train_result):
        train_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:.6f}\t{:.6f}\n".format( i, res.pool_nm, res.fcinit_nm, res.act_nm, res.optim_nm,
                                                                   res.lr, res.epoch, res.cost, res.accuracy))
    train_file.close()

    test_file = open("result/test.txt", mode='wt', encoding='utf-8')
    test_file.write("SN,POOL,INIT,ACTIVATE,OPTIM,LR,ACCURACY\n")
    for i, res in enumerate(test_result):
        test_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{:.6f}\n".format( i, res.pool_nm, res.fcinit_nm, res.act_nm, res.optim_nm,
                                                                                res.lr, res.accuracy))
    test_file.close()

training_loop()
