import numpy as np  
import sys,os
sys.path.insert(0, '/home/jiangzhiqi/Documents/caffe/python')
import caffe  

def merge_bn(net, nob):
    '''
    merge the batchnorm, scale layer weights to the conv layer, to  improve the performance
    mean = mean * scaleFacotr
    var = var * scaleFacotr
    rstd = 1. / sqrt(var + eps)
    w = w * rstd * scale
    b = (b - mean) * rstd * scale + shift
    '''
    for key in net.params.iterkeys():
        if type(net.params[key]) is caffe._caffe.BlobVec:
            if key.startswith("bn") or key.startswith("scale"):
                continue
            else:
                conv = net.params[key]
                if not (key.startswith("res") or "conv1"==key):
                    for i, w in enumerate(conv):
                        nob.params[key][i].data[...] = w.data
                else:
                    bn = net.params[key.replace("res", "bn")]
                    scale = net.params[key.replace("res", "scale")]
                    if "conv1"==key:
                        bn=net.params["bn_"+key]
                        scale=net.params["scale_"+key]
                    wt = conv[0].data
                    channels = wt.shape[0]
                    bias = np.zeros(wt.shape[0])
                    if len(conv) > 1:
                        bias = conv[1].data
                    mean = bn[0].data
                    var = bn[1].data
                    scalef = bn[2].data
                    scales = scale[0].data
                    shift = scale[1].data

                    if scalef != 0:
                        scalef = 1. / scalef
                    mean = mean * scalef
                    var = var * scalef
                    rstd = 1. / np.sqrt(var + 1e-5)
                    rstd1 = rstd.reshape((channels,1,1,1))
                    scales1 = scales.reshape((channels,1,1,1))
                    wt = wt * rstd1 * scales1
                    bias = (bias - mean) * rstd * scales + shift
                    
                    nob.params[key][0].data[...] = wt
                    nob.params[key][1].data[...] = bias
  

def merge_bn_file(train_proto,train_model,deploy_proto,save_model):
    net = caffe.Net(train_proto, train_model, caffe.TRAIN)  
    net_deploy = caffe.Net(deploy_proto, caffe.TEST)  

    merge_bn(net, net_deploy)
    net_deploy.save(save_model)


def main(argv):
    train_proto = './debug/ResNet-50-deploy.prototxt'  
    train_model = './debug/20000.caffemodel'

    deploy_proto = './debug/deploy.prototxt'  
    save_model = './debug/20000_merge.caffemodel'

    merge_bn_file(train_proto,train_model,deploy_proto,save_model)

if __name__ == "__main__":
    import sys
    main(sys.argv)

