#!/usr/bin/python

import numpy as np
import json
import time
import sys

import matplotlib.pyplot as plt
from blm_ajm import BLMNII

from sklearn import svm
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import MinMaxScaler

sys.path.append('../../utility')
import yamanishi_data_util as yam

def main():
    classParam = dict(name='blmnii',proba=True)

    if len(sys.argv)!=4:
        print "python blmniisvm_experiment.py [DataSetCode] [evalMode] [PathDirectory]"
        return

    dataset = sys.argv[1]
    evalMode = sys.argv[2]
    generalPath = sys.argv[3]

    dataPath  = generalPath
    outPath = generalPath+"/hasil"

    print "Building Data"
    connMat,comList,proList = yam.loadComProConnMat(dataset,dataPath+"/Adjacency")
    kernel = yam.loadKernel(dataset,dataPath)

    comListIdx = [i for i,_ in enumerate(comList)]
    proListIdx = [i for i,_ in enumerate(proList)]

    nComp = len(comList)
    nProtein = len(proList)

    comSimMat = np.zeros((nComp,nComp), dtype=float)
    proSimMat = np.zeros((nProtein,nProtein), dtype=float)
    for row,i in enumerate(comList):
        for col,j in enumerate(comList):
            comSimMat[row][col] = kernel[(i,j)]

    for row,i in enumerate(proList):
        for col,j in enumerate(proList):
            proSimMat[row][col] = kernel[(i,j)]

    # TO DO: Check eigen value of each matrix and do the following
    #     epsilon = .1;
    # while sum(eig(comp) >= 0) < compLength || isreal(eig(comp))==0
    #     comp = comp + epsilon*eye(compLength);
    # end
    # while sum(eig(target) >= 0) < targetLength || isreal(eig(target))==0
    #     target = target + epsilon*eye(targetLength);
    # endd

    pairData = []
    connList = []
    print "Split Dataset..."
    if evalMode == "loocv":
        nFold = len(comListIdx)
        kSplit = KFold(n_splits=nFold,shuffle=True)
        comSplit = kSplit.split(comListIdx)

        nFold = len(proListIdx)
        kSplit = KFold(n_splits=nFold,shuffle=True)
        proSplit = kSplit.split(proListIdx)

    elif evalMode == "kfold":
        nFold = 10
        kSplit = KFold(n_splits=nFold, shuffle=True)
        comSplit = kSplit.split(comListIdx)
        proSplit = kSplit.split(proListIdx)

    else:
        assert(False)

    predictedData = np.zeros((len(comList),len(proList)),dtype=float)
    splitPred = []
    proTestList = []
    proTrainList = []
    comTestList = []
    comTrainList = []

    for trainIndex, testIndex in proSplit:
        proTestList.append([i for i in testIndex])
        proTrainList.append([i for i in trainIndex])
    for trainIndex, testIndex in comSplit:
        comTestList.append([i for i in testIndex])
        comTrainList.append([i for i in trainIndex])

    predRes = []
    testData = []
    print "Predicting..."
    for ii,i in enumerate(comTestList):
        for jj,j in enumerate(proTestList):
            sys.stdout.write("\r%03d of %03d||%03d of %03d" %
                                (jj+1, len(proTestList), ii+1,len(comTestList),))
            sys.stdout.flush()

            predictor = BLMNII(classParam, connMat, comSimMat, proSimMat,
                            [comTrainList[ii],proTrainList[jj]],[i,j])
            for comp in i:
                for prot in j:
                    predRes.append(predictor.predict([(comp,prot)]))
                    testData.append(connMat[comp][prot])

#####################################################################

    print "\nCalculate Performance"
    key = 'PredictionUsingBLM_NII'
    precision, recall, _ = precision_recall_curve(testData, predRes)
    prAUC = average_precision_score(testData, predRes, average='micro')

    print "Visualiation"
    lineType = 'k-.'

    perf = {'precision': precision, 'recall': recall, 'prAUC': prAUC,
                 'lineType': lineType}
    perf2 = {'prAUC': prAUC, 'nTest': nComp*nProtein}

    with open(outPath+'/'+ dataset +'_'+evalMode+'_perf.json', 'w') as fp:
        json.dump(perf2, fp, indent=2, sort_keys=True)

    plt.clf()
    plt.figure()
    plt.plot(perf['recall'], perf['precision'], perf['lineType'], label= key+' (area = %0.2f)' % perf['prAUC'], lw=2)
    plt.ylim([-0.05, 1.05])
    plt.xlim([-0.05, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.savefig(outPath+'/'+ dataset +'_'+evalMode+'_pr_curve.png', bbox_inches='tight')

if __name__ == '__main__':
    main()
