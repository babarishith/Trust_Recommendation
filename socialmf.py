import numpy as np
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize
from scipy.sparse import coo_matrix, lil_matrix
import warnings
warnings.filterwarnings("error")
from scipy.special import expit as sigmoid

def norm(R):
	for i in xrange(len(R)):
		R[i] = (R[i] - 0.0)/5.0
		# for j in xrange(len(R[i])):
		# 	if R[i][j] > 0:
		# 		R[i][j] = (R[i][j] - 0)/5.0
	return R

def bound(x):
	return sigmoid(x)
	# return 1/(1 + np.exp(-x))

def dbound(x):
	fx = sigmoid(x)
	return fx*(1-fx)

def bou(R):
	for i in xrange(len(R)):
		for j in xrange(len(R[i])):
			a = bound(R[i][j])
			R[i][j] = a
	return R

def get(R):
	for i in xrange(len(R)):
		for j in xrange(len(R[i])):
			if R[i][j] > 0:
				R[i][j] = (R[i][j] * 5.0)
	return R

def mae(U, V, test, u, itm):
	e = 0.0
	ke = 0.0
	for i in test:
		try:
			val = np.dot(U[u[i[0]],:],V[itm[i[1]],:].T)
			val = bound(val) * 5
			# err = np.absolute(val - i[2])
			# e += err*err
			e += np.absolute(val - i[2])

		except KeyError:
			ke += 1
	if ke > 0:
		print "KeyErrors", ke
	# return e, np.sqrt(e/len(test))
	return e, e/len(test)

def rmse(U, V, test, u, itm):
	e = 0.0
	ke = 0.0
	for i in test:
		try:
			val = np.dot(U[u[i[0]],:],V[itm[i[1]],:].T)
			val = bound(val) * 5
			err = np.absolute(val - i[2])
			e += err*err
			# e += np.absolute(val - i[2])

		except KeyError:
			ke += 1
	if ke > 0:
		print "KeyErrors", ke
	return e, np.sqrt(e/len(test))
	# return e, e/len(test)

def matrix_factorize(R, U, V, C, K, steps=800, alpha=0.01, beta=0.0001, gamma=0.0001):
	V = V.T
	Csr = C.tocsr()
	Csc = C.tocsc()
	ne = 0
	pre_e = 10
	for step in xrange(steps):
		ne = 0
		TRU = U - C.dot(U)
		pre_i = -1
		for i,j,val in zip(R.row, R.col, R.data):
			# print "hello", i,j,val
			y = np.dot(U[i,:], V[:,j])
			a = bound(y)
			b = dbound(y)
			eij = (val - a)
			ne += eij * eij
			if pre_i != i:
				pre_u = Csr.getcol(i)
				u_tr = pre_u.T.dot(TRU)
				pre_i = i

			U[i,:] = U[i,:] + alpha * (b * eij * V[:,j] - beta * U[i,:] - beta * TRU[i,:] + beta * u_tr)
			V[:,j] = V[:,j] + alpha * (b * eij * U[i,:] - beta * V[:,j])
			ne += beta * (np.dot(U[i,:],U[i,:]) + np.dot(V[:,j],V[:,j]))
			ne += np.dot(TRU[i,:].T, TRU[i,:])
		ne *= 0.5
		if ne < 0.001:
			break
		else:
			# print ne
			pass
		if step % 10 == 0:
			print step, "iterations done."
			print "process error", ne
			print "calculating MAE"
			global r_test
			t, e = rmse(U, V.T, r_test, ud, itm)
			print "total", t, "RMSE", e
			if pre_e < e:
				print pre_e, e
				break
			pre_e = e

	return U, V.T, ne 


def data(f,sh, ud, itm,flag):
	# print len(f[:,2]), len(f[:,[0]])
	# a = sp.csr_matrix((f[:,2], (f[:,0],f[:,1])), shape=sh)
	a = np.zeros(sh)
	# itm = {}
	# if flag == 0:
	# 	u = {}
	# else:
	u = ud
	itm = itm
	j = 0
	k = 0
	for i in f:
		if u.has_key(i[0]) == False:
			u[i[0]] = j
			j += 1
		if flag == 1:
			if u.has_key(i[1]) == False:
				u[i[1]] = j
				j += 1
			a[u[i[0]]][u[i[1]]] = i[2]
		else:
			if itm.has_key(i[1]) == False:
				itm[i[1]] = k
				k += 1
			a[u[i[0]]][itm[i[1]]] = i[2]
		# print i[2]
		# sys.exit()
	return a, u, itm

def create_dic(r):
	u = {}
	itm = {}
	j = 0
	k = 0
	for i in r:
		if u.has_key(i[0]) == False:
			u[i[0]] = j
			j += 1
		if itm.has_key(i[1]) == False:
			itm[i[1]] = k
			k += 1
	return u, itm

#data
flag = 1
if flag == 1:
	n_u = 3
	print "for",n_u*1000, "users and", n_u*3000, "items"
	r_data = np.genfromtxt('rating_short_'+ str(n_u)+'_'+ str(3*n_u)+'.txt', dtype=float, delimiter=' ')
	t_data = np.genfromtxt('trust_short_'+ str(n_u)+'_'+ str(3*n_u)+'.txt', dtype=float, delimiter=' ')
else:
	print "For full dataset"
	r_data = np.genfromtxt('dataset/ratings_data.txt', dtype=float, delimiter=' ')
	t_data = np.genfromtxt('dataset/trust_data.txt', dtype=float, delimiter=' ')
# print t_data[0][0]
user = np.unique(np.append(r_data[:,0],[t_data[:,0], t_data[:,1]]))
items = np.unique(r_data[:,1])
# print items
# if 46465 not in user and 46465  in t_data[:,1]:
# 	print "NO"
N = user.shape[0]
M = items.shape[0]
# print "N,M", N,M
# sys.exit()
ud = dict(zip(user, np.arange(N)))
itm = dict(zip(items, np.arange(M)))
# print len(ud), len(itm)
# print ud
# sys.exit()
# i,j,rdata = np.hsplit(r_train, 3)
# i = i.flatten
# j = j.flatten
# rdata = rdata.flatten
# print "one"
r_train, r_test = train_test_split(r_data, test_size=0.1, random_state=42)

# ud, itm = create_dic(r_data)

# R, ud, itm = data(r_train, (n_u * 1000,n_u * 3000), ud, itm, 0)
# C, ud, itm = data(t_data, (n_u * 1000,n_u * 1000), ud, itm, 1)
# print "for",n_u*1000, "users and", n_u*3000, "items"

# M = 49290
# N = 139738
# r_data = np.genfromtxt('dataset/ratings_data.txt', dtype=int, delimiter=' ')
# t_data = np.genfromtxt('dataset/trust_data.txt', dtype=int, delimiter=' ')
# r_train, r_test = train_test_split(r_data, test_size=0.3, random_state=42)

# R = np.array(R)
# i,j,rdata = np.hsplit(r_train, 3)
# i = i.flatten
# j = j.flatten
# rdata = rdata.flatten
r_train[:,2] = norm(r_train[:,2])
# print r_train[:,0][:5]
# sys.exit()
x = r_train[:,0]
y = r_train[:,1]
p = t_data[:,0]
q = t_data[:,1]

# print "ah", itm[19793]
# print x.shape
x = [ud[i] for i in x]
p = [ud[i] for i in p]
q = [ud[i] for i in q]
y = [itm[i] for i in y]

# print "two"

# for k,v in ud.iteritems():
# 	x[x == k] = v
# 	p[p == k] = v
# 	q[q == k] = v
# for k,v in itm.iteritems():
# 	y[y == k] = v
# print np.max(p), np.max(q)
if flag == 1:
	R = coo_matrix((r_train[:,2], (x,y)) , shape = (n_u*1000, n_u*3000)).tocsr().tocoo()
	C = coo_matrix((t_data[:,2], (p,q)) , shape = (n_u*1000, n_u*1000))
else:
	R = coo_matrix((r_train[:,2], (x,y)) , shape = (49291, 139738))
	C = coo_matrix((t_data[:,2], (p,q)) , shape = (49291, 49291))
# R = R.tolil()
# print "three"
# C = C.tolil()
# N = len(R)
# M = len(R[0])
s = R.shape
N = s[0]
M = s[1]

K = 5

U = np.random.rand(N,K)
V = np.random.rand(M,K)


C_norm = normalize(C, norm='l1', axis=1)

print "finished data pre-processing"

nU, nV, em = matrix_factorize(R, U, V, C_norm, K)
# nR = np.dot(nU,nV.T)
# nnR = bou(nR)
# aR = get(nnR)
# print aR

print "process error", em

print "calculating RMSE"

t, e = rmse(nU, nV, r_test, ud, itm)
print "test len", r_test.shape
print "total", t, "RMSE", e