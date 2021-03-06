# predictor_config.py

## Individual predictors
rndlyConfig = dict(name='rndly',weight=0.5,
                   batchSize=5)
kronRLSConfig = dict(name='kronrls',weight=0.6,
                     batchSize=10,maxTrainingDataSize=100,
                     gamma=1.0,threshold=0.1,
                     alphaCompoundKernel=0.5,alphaProteinKernel=0.5,
                     kernelBandwidth=1.0)
blmniiConfig = dict(name='blmnii',weight=0.6,batchSize=1,
                    maxTrainingDataSize=1000,proba=True)

## Common params
predictorConfig = dict()
predictorConfig['maxElapsedTime'] = 7 # in seconds
predictorConfig['methods'] = [kronRLSConfig,blmniiConfig,rndlyConfig]
predictorConfig['trainingDataSources'] = ['drugbank.ca']
