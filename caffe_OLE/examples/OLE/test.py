import glob
import sys
import os
from collections import OrderedDict
import time
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from utils import sample_points

# add caffe to path
sys.path.append('../../python')

import caffe
caffe.set_mode_gpu() #for cpu mode do 'caffe.set_mode_cpu()'

from caffe import layers as L

base_dir = os.getcwd()
sys.path.append(base_dir)

"""This code should replicate, using Caffe, the results obtained with the Numpy
only implementation of OLE:

D = 3
N = 50
C = 3 # classes
lambda_ = 1/np.float(C)
reg = 0
learning_rate = 0.001
y = np.random.randint(C,size=C*N)
y[0:N]=0
y[N:2*N]=1
y[2*N:]= 2

T = np.eye(D)

F = sample_points(N,C,D)

iters = 1000

for it in xrange(iters):

    obj, dT, dF = lowrank_loss(T, F, y, regT=reg, lambda_=lambda_, eigThd=1e-6)
    
    # print 'norm(grad(T))', np.linalg.norm(dT)
    if it==0:
            print 'initial: ', obj
    T -= learning_rate*dT

mF = F.dot(T) # mapped F

if 1:
 fig = plt.figure()
 ax = fig.add_subplot(111, projection='3d')
 ax.scatter(mF[:,0],mF[:,1],mF[:,2],c=y,depthshade=False, cmap='brg')

"""


################################################################################
# AUX FUNCTIONS

def example_network(batch_size, fname='network.prototxt'):
    n = caffe.NetSpec()

    n.data, n.label = L.DummyData(shape=[dict(dim=[batch_size, 3]),
                                         dict(dim=[batch_size])],
                                  transform_param=dict(scale=1.0/255.0),
                                  ntop=2)

    n.affine = L.InnerProduct(n.data, num_output=3)
    n.lowrank = L.Python(n.affine, n.label,
                          python_param=dict(
                                          module='LowRankLoss',
                                          layer='LowRankLossLayer'),
                                          ntop=1,)
                                          #param_str='{ "param_name": param_value }'),

    f =  open(fname, 'w')
    f.write(str(n.to_proto()))
    f.close()





################################################################################
# MAIN

# create network
fname = 'network.prototxt'
N = 50 # points per calss
batch_size = N*3
C = 3 # number of classes
D = 3 # dimension


# load network
net = caffe.Net(fname, caffe.TRAIN)
 


# initialize labels

y = np.random.randint(C,size=C*N)
y[0:N]=0
y[N:2*N]=1
y[2*N:]= 2

net.blobs['label'].data[...] = y

# initalize data
X = sample_points(N,C,D)
net.blobs['data'].data[...] = X

# initialize T
T = np.eye(D)
net.params['affine'][0].data[...] = T # corresponds to weights (T)


# solve
learning_rate = 0.001

for it in xrange(10000):
    # step forward
    net.forward()

    # reset gradients (?)
    net.params['affine'][0].diff[...] = np.zeros_like(net.params['affine'][0].diff)
    
    # step backward
    net.backward()


    # print net.blobs['affine'].diff

    print 'norm(grad(T))', np.linalg.norm(net.params['affine'][0].diff)

    net.params['affine'][0].data[...] -= learning_rate * net.params['affine'][0].diff

    print 'norm(T)', np.linalg.norm(net.params['affine'][0].data[...])

    print 'obj', net.blobs['lowrank'].data


mX = net.blobs['affine'].data


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(mX[:,0],mX[:,1],mX[:,2],c=y,depthshade=False, cmap='brg')

# plt.show()
plt.savefig('test.png', bbox_inches='tight')

os.system('open test.png')
