import numpy as np
import os, re, sys
from sklearn import metrics
sys.path.insert(0, '/'.join(os.getcwd().split('/')[:-4]))
import myAUC

dirnum = int(os.getcwd().split('/')[-1])-1
prop = os.getcwd().split('/')[-2]

seed0 = 1000001 + 100*dirnum
np.random.seed(seed0)

code_path = '../../../../../Code/EMDD/EMDD'
Datapath = '../../../../../Data/Delicious'

trfile = '%s/train-data.dat' %Datapath
if prop != '1':
	trlblfile = '%s/train-label%s.dat' %(Datapath,prop)
else:
	trlblfile = '%s/train-label.dat' %(Datapath)
tfile = '%s/test-data.dat' %Datapath
tlblfile = '%s/test-label.dat' %Datapath
vfile = '%s/valid-data.dat' %Datapath
vlblfile = '%s/valid-label.dat' %Datapath
vocabfile = '%s/vocabs.txt' %Datapath
tslblfile = '%s/test-sentlabel.dat' %Datapath


resfile = 'results.txt'
fpres = open(resfile, 'w')
fpres.write('roc roc_sent roc_macro roc_sent_macro fprAUC traintime\n')
fpres.close()


# only keep labeled docs
os.system('mkdir -p dir')
fpdoc_in = open(trfile)
fpdoc_out = open('dir/train-data.dat','w')
fplbl_in = open(trlblfile)
fplbl_out = open('dir/train-label.dat','w')
while True:
	docln = fpdoc_in.readline()
	lblln = fplbl_in.readline()
	if len(docln)==0:
		break
	l0 = int(lblln.split(' ')[0])
	if l0 == -1:
		continue
	fpdoc_out.write(docln)
	fplbl_out.write(lblln)
trfile = 'dir/train-data.dat'
trlblfile = 'dir/train-label.dat'
fpdoc_in.close()
fpdoc_out.close()
fplbl_in.close()
fplbl_out.close()


trlbl = np.loadtxt(trlblfile)
tlbl = np.loadtxt(tlblfile)
(Dtr, C) = trlbl.shape
Dt = tlbl.shape[0]
N = len(open(vocabfile).readlines())

tlbl = np.loadtxt(tlblfile)


# total number of sentences
Sd_total = 0
fp = open(tfile)
while True:
	ln = fp.readline()
	if len(ln)==0:
		break
	sd = re.findall('^<([0-9]*)>', ln)[0]
	Sd_total += int(sd)

slbl_gt = open(tslblfile).readlines()
gt_sent2 = np.zeros((Sd_total,C))
cnt = 0
cnt_lbld = 0
slbld_list = []
for d in range(len(slbl_gt)):
	sents_gt = re.findall('<(.*?)>',slbl_gt[d])
	for sent in sents_gt:
		temp = np.array([float(x) for x in sent.split()])
		if temp[0] == -1:
			cnt += 1
			continue
		gt_sent2[cnt_lbld,:] = temp.copy()
		slbld_list.append(cnt)
		cnt_lbld += 1
		cnt += 1
gt_sent = gt_sent2[:cnt_lbld,:].copy()

			
fp = open('settings.txt', 'w')
fp.write('C %d\nD %d\nN %d\nmaxiter %d\nconverged %f' %(C,Dtr,N,20,5e-3))
fp.close()

# train
seed = np.random.randint(seed0)
cmdtxt = '%s %d train %s %s settings.txt random dir' %(code_path, seed, trfile, trlblfile)
os.system(cmdtxt)

trtime = np.loadtxt('dir/likelihood.dat')[-1,3]
model_h = np.loadtxt('dir/final.h')
model_s = np.loadtxt('dir/final.s')


# do class prediction
hTs = np.zeros(C)
for c in range(C):
	hTs[c] = np.sum((model_h[:,c]*model_s[:,c])**2)

b_sent = np.zeros((cnt_lbld,C))
scnt = 0
scnt_lbld = 0
b = np.zeros(tlbl.shape)
fp = open(tfile)
d = 0
while True:
	ln = fp.readline()
	if len(ln)==0:
		break
	sents = re.findall('<[0-9]*?>([0-9 ]*)',ln)
	Sd = len(sents)-1
	py = np.zeros((Sd,C))
	for c in range(C):	
		logpy = 0.0;
		for s,sent in enumerate(sents[1:]):
			temp = hTs[c]
			temp += np.sum([(1-2*model_h[int(n),c])*model_s[int(n),c]**2 for n in sent.split()])
			#for n in sent.split():
			#	temp += (1-2*model_h[c,int(n)])*model_s[c,int(n)]**2
			py[s,c] = np.exp(-temp)

		b[d,c] = np.max(py[:,c])
	for s in range(Sd):
		if scnt not in slbld_list:
			scnt += 1
			continue
		b_sent[scnt_lbld,:] = py[s,:]
		scnt_lbld += 1
		scnt += 1
	d += 1
fp.close()

(roc, roc_macro) = myAUC.compute_auc(b, tlbl)
(roc_sent, roc_sent_macro) = myAUC.compute_auc(b_sent, gt_sent)

# ThFprAUC for documents with no labels
nolbld = np.where(np.sum(tlbl,1)==0)[0]
if len(nolbld) > 0:
	TH = np.linspace(0,1,20)
	fpr = np.zeros(len(TH))
	for t,th in enumerate(TH):
		pred = np.round(b[nolbld] > th)
		tn = np.sum((1-pred) == 1)
		fp = np.sum(pred == 1)
		fpr[t] = fp/float(fp+tn)
	fprAUC = metrics.auc(TH,fpr)
else:
	fprAUC = 0



fpres = open(resfile, 'a')
fpres.write('%f %f %f %f %f %f\n' %(roc, roc_sent, roc_macro, roc_sent_macro, fprAUC, trtime))
fpres.close()
	

os.system('rm -r dir')
os.system('rm settings.txt')

