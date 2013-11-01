# query <master> <inputFile> <inds> <outputFile>
# 
# quickly query a data set by averaging together points
# each row is (x,y,z,timeseries)
#

import sys
import os
from numpy import *
from scipy.linalg import *
from scipy.io import * 
from pyspark import SparkContext
import logging

if len(sys.argv) < 4:
  print >> sys.stderr, \
  "(query) usage: query <master> <inputFile> <inds> <outputFile>"
  exit(-1)

def parseVector(line):
	vec = [float(x) for x in line.split(' ')]
	ts = array(vec[3:]) # get tseries
	k = int(vec[0]) + int((vec[1] - 1)*1212) # constant is the max value along second (?) dimension
	#kraw = (int(vec[0]),int(vec[1]))
	meanVal = mean(ts)
	ts = (ts - meanVal) / (meanVal + 0.1) # convert to dff
	return (k,ts)

# parse inputs
sc = SparkContext(sys.argv[1], "query")
inputFile = str(sys.argv[2])
indsFile = str(sys.argv[3])
outputFile = str(sys.argv[4]) + "-query"
logging.basicConfig(filename=outputFile+'-stdout.log',level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')

logging.info("(query) loading data")
data = sc.textFile(inputFile).map(parseVector).cache() # the data

inds = loadmat(indsFile)['inds'][0]

#print(data.filter(lambda (k,kraw,x) : kraw[0]==1).map(lambda (k,kraw,x) : kraw[1]).collect())
#print(data.filter(lambda (k,kraw,x) : kraw[1]==1).map(lambda (k,kraw,x) : kraw[0]).collect())

#for i in range(0,len(inds)) :
#	print(data.filter(lambda (k,kraw,x) : k in inds[i]).map(lambda (k,kraw,x) : kraw).collect())

if len(inds) == 1 :
	indsTmp = inds[0]
	n = len(indsTmp)
	ts = data.filter(lambda (k,x) : k in indsTmp).map(lambda (k,x) : x).reduce(lambda x,y :x+y) / n
	savemat(outputFile+"-ts.mat",mdict={'ts':ts},oned_as='column',do_compression='true')
else :
	nInds = len(inds)
	ts = zeros((len(data.first()[1]),nInds))
	for i in range(0,nInds) :
		indsTmp = inds[i]
		n = len(indsTmp)
		ts[:,i] = data.filter(lambda (k,x) : k in indsTmp).map(lambda (k,x) : x).reduce(lambda x,y :x+y) / n
	savemat(outputFile+"-ts.mat",mdict={'ts':ts},oned_as='column',do_compression='true')




