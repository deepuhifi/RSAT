#! /usr/bin/python

"""
RSAT, a script for partial key exposure attacks on RSA with SAT solvers
Copyright (c) 2012 Constantinos Patsakis, All Right Reserved

Contact Information:
Constantinos Patsakis
kpatsak@gmail.com

This is an updated Modified version of RSAT created to run the RSAT tool with advanced methods and modifications


"""

import gmpy2
import factoring_j
import random 
import math
import argparse
import os 
from subprocess import Popen
import sys
import time
import subprocess
import gc

#turn off warnings
import warnings 
warnings.filterwarnings('ignore')

#Need this in order to remove any possible problems with big keys which demand a lot of recursions.
sys.setrecursionlimit(10000)
time2kill=400
cores=8

def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]
    
def conv2bin(num):
	tmp=bin(num)[2:]
	bin_rep=[]
	for i in tmp:
		bin_rep.append(int(i))
	return bin_rep[::-1]
	

def writeFA(x,y,Cin,S,Cout):
	#write relationships for Sum
	#(x|y|Cin|!s)&(x|!y|!Cin|!s)&(!x|y|!Cin|!s)&(!x|!y|Cin|!s)&(!x|!y|!Cin|s)&(!x|y|Cin|s)&(x|!y|Cin|s)&(x|y|!Cin|s)
	eqs4d.append("%d %d %d -%d 0\n" % (x,y,Cin,S))
	eqs4d.append("%d -%d -%d -%d 0\n" % (x,y,Cin,S))
	eqs4d.append("-%d %d -%d -%d 0\n" % (x,y,Cin,S))
	eqs4d.append("-%d -%d %d -%d 0\n" % (x,y,Cin,S))
	eqs4d.append("-%d -%d -%d %d 0\n" % (x,y,Cin,S))
	eqs4d.append("-%d %d %d %d 0\n" % (x,y,Cin,S))
	eqs4d.append("%d -%d %d %d 0\n" % (x,y,Cin,S))
	eqs4d.append("%d %d -%d %d 0\n" % (x,y,Cin,S))
	#write relationships for Sum
	eqs4d.append("%d %d %d 0\n" % (x,y,-Cout))
	eqs4d.append("%d %d %d 0\n" % (x,Cin,-Cout))
	eqs4d.append("%d %d %d 0\n" % (y,Cin,-Cout))
	eqs4d.append("%d %d %d 0\n" % (-x,-y,Cout))
	eqs4d.append("%d %d %d 0\n" % (-x,-Cin,Cout))
	eqs4d.append("%d %d %d 0\n" % (-y,-Cin,Cout))

def genprime(bits):
	p=1
	if bits<=1000:
		while(gmpy2.is_prime(p)==0):
			p = random.randrange(math.pow(2,bits-1),math.pow(2,bits))
		return p
	else:
		while(gmpy2.is_prime(p)==0):
			p1 = random.randrange(math.pow(2,bits/2-1),math.pow(2,bits/2))
			p2 = random.randrange(math.pow(2,bits/2-1),math.pow(2,bits/2))
			p=p1+2**(bits/2)*p2
		return p	

def subprocess_execute(command, time_out):
    """executing the command with a watchdog"""

    # launching the command
    c = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # now waiting for the command to complete
    t = 0
    while t < time_out and c.poll() is None:
        time.sleep(1)
        t += 1

    # there are two possibilities for the while to have stopped:
    proc_out=[]
    if c.poll() is None:
        # in the case the process did not complete, we kill it
        c.terminate()
        # and fill the return code with some error value
        returncode = -1
    else:                 
        # in the case the process completed normally
        returncode = c.poll()
    for i in c.stdout:
        proc_out.append(i.replace("\n",""))
    return returncode,proc_out

parser = argparse.ArgumentParser(description='Factor an integer using a SAT solver and partial key exposure.')
parser.add_argument('-b', action="store", dest="bits", type=int,
                   help='The number of bits that each prime has. Default is 10.', default=10)
parser.add_argument('-ps', action="store", dest="ps", type=float,
                   help='The percent of bits of p from which I start to know. Default is 0.', default=0)
parser.add_argument('-pe', action="store", dest="pe", type=float,
                   help='The percent of bits of p to which I stop to know. Default is 0.', default=0)
parser.add_argument('-qs', action="store", dest="qs", type=float,
                   help='The percent of bits of q from which I start to know. Default is 0.', default=0)
parser.add_argument('-qe', action="store", dest="qe", type=float,
                   help='The percent of bits of q to which I stop to know. Default is 0.', default=0)
parser.add_argument('-ds', action="store", dest="ds", type=float,
                   help='The percent of bits of d from which I start to know. Default is 0.', default=0)
parser.add_argument('-de', action="store", dest="de", type=float,
                   help='The percent of bits of d to which I stop to know. Default is 0.', default=0)
parser.add_argument('-pq', action="store", dest="pq", type=float,
                   help='The percent of random bits of p and q that are known.', default=0)
parser.add_argument('-dpq', action="store", dest="dpq", type=float,
                   help='The percent of random bits of d, p and q that are known.', default=0)
parser.add_argument('-nop', action="store_true", dest="nop", 
                   help='Do not use any bit of p.', default=False)
parser.add_argument('-noq', action="store_true", dest="noq", 
                   help='Do not use any bit of q.', default=False)
parser.add_argument('-nod', action="store_true", dest="nod", 
                   help='Do not use any bit of d.', default=False)
parser.add_argument('-cnf3', action="store_true", dest="cr_cnf3", 
                   help='Use 3 CNF for the main part.', default=False)                   
parser.add_argument('-del', action="store_true", dest="deltmp", 
                   help='Delete temporary files.', default=False)                   
parser.add_argument('-o', action="store", dest="out_file", 
                   help='Output file.', default="output.out")
parser.add_argument('-c', action="store", dest="original_cnf", 
                   help='Original CNF file.', default="original_cnf.dimacs")
parser.add_argument('-n', action="store", dest="new_cnf_file", 
                   help='New CNF file.', default="new_cnf.dimacs")
parser.add_argument('-t', action="store", dest="t", type=int,
                   help='Number of test to execute, good for probabilistic mode. Default is 1.', default=1)
parser.add_argument('-s', action="store", dest="s", type=int,
                   help='SAT solver to use 0 for minisat, 1 for clasp. Default is 0.', default=0)

results = parser.parse_args()

prime_bits=results.bits
dpq=results.dpq
pq=results.pq
out_file=results.out_file
original_cnf=results.original_cnf
new_cnf_file=results.new_cnf_file
cr_cnf3=results.cr_cnf3
delete_tmp=results.deltmp
nod=results.nod
t=results.t
sat_solver=results.s
keepFiles=results.deltmp
if dpq==0 and pq==0:
	ps=results.ps
	qs=results.qs
	pe=results.pe
	qe=results.qe
	ds=results.ds
	de=results.de
	if results.noq==True:
		qs=0
		qe=0
	if results.nop==True:
		ps=0
		pe=0

random.seed()
#generate random prime numbers and n
foundP=False

if nod==True:
    p=genprime(prime_bits)
    q=genprime(prime_bits)
else:
	p=genprime(prime_bits)
	while ((p-1)%3==0): 
		p=genprime(prime_bits)
	q=1
	foundq=False
	while (not foundq): 
		q=genprime(prime_bits)
		if (q-1)%3!=0:
			foundq=True
				
n=p*q
p=min(p,q)
q=n/p

len_n=n.bit_length()

print ("Generating problem for factoring %d...\n" % n)

if cr_cnf3==True:
	init_model=factoring_j.generate_instance2(n,"3cnf")
else:
	init_model=factoring_j.generate_instance2(n,"op")

fout = open(original_cnf, 'w')
fout.write(init_model)
fout.close()

print ("Please wait calculating...")

for tst in range(t): #repeat the tests t times...
	list2save=[]
	eqs=0
	with open(original_cnf, 'r') as f:
		#find how many variables and equations we have on the original file
		#dimacs has it in the first line
		tmp = f.readline()
		tmp_split=tmp.split()
		variables=int(tmp_split[2])
		eqs=int(tmp_split[3])
		#now find how many variables are kept for each prime
		tmp = f.readline()
		tmp_split=tmp.split()
		tmp_diff=tmp_split[5]
		tmp_bnds=tmp_diff.split("-")
		prime_vars=int(tmp_bnds[1])-int(tmp_bnds[0])+1
	
	original_variables=variables

	if (os.path.exists(new_cnf_file)):
		os.unlink(new_cnf_file)
	fout = open(new_cnf_file, 'w')
	fin = open(original_cnf, 'r')


	#list2save.append("c ---n to factor %d----\n" % n)
	p_lst=[]
	q_lst=[]

	for i in range(prime_vars):
		p_lst.append(i+1)
		q_lst.append(i+prime_vars+1)

	list2save.append("%d 0\n" % p_lst[0])
	list2save.append("%d 0\n" % q_lst[0])

	list2save.append("%d 0\n" % p_lst[prime_bits-1])
	list2save.append("%d 0\n" % q_lst[prime_bits-1])

	#sometimes the encoding has one more bit, which of course is 0
	if prime_vars>prime_bits:
		list2save.append("-%d 0\n" % p_lst[prime_bits])
		list2save.append("-%d 0\n" % q_lst[prime_bits])

	i=0
	for line in fin:
		i+=1
		if i>1:#write everything except the first line
			list2save.append(line)
	fin.close()
	eqs4d=[]
	variables+=1
	eqs+=1
	
	#list2save.append("c carry0 is set to false\n")
	eqs4d.append("-%d 0\n" %(variables)) #carry0 =false=0

	#keep this variable because we will need it in other places as well
	false_var=variables
	s_lst=[]
	#fix s representation
	for i in range(prime_vars):
		a= i+1
		b= i+1+prime_vars
		if  i==0: 
			Cin=variables
		else:
			Cin=variables+i*2
		s=variables+i*2+1;	s_lst.append(s)
		nc=variables+i*2+2
		writeFA(a,b,Cin,s,nc); 	eqs+=14

	#since the sum might be one bit longer, I have to append the last carry to the list of s
	s_lst.append(nc)
	#we will need 2*s which is s with 0 appended in the beginning so...
	#prepend false_var to the list...
	s_lst.insert(0,false_var)
	variables+=2*(i+1)
	variables+=1
	true_var=variables
	#list2save.append("c ---storing 3d----\n")
	#list2save.append("c d is odd so first bit is set to true\n")
	eqs4d.append("%d 0\n" %(variables)) #d0 =true=1
	eqs+=1

	#store 3*d
	#remember 3d=2d+d
	triple_d=[]
	d=[]
	for i in range(len_n+1):
		if i==0:
			a=true_var;	d.append(a)
			b=false_var
			Cin=false_var
			nc=false_var
			s=true_var;	triple_d.append(s)
			#nothing to store in the file
		elif i==1:
			a=variables+1;	d.append(a)
			b=true_var
			Cin=false_var
			nc=variables+2
			s=variables+3;	triple_d.append(s)
		elif i==2:
			a=variables+3*(i-1)+1;	d.append(a)
			b=variables+1
			Cin=variables+2
			nc=variables+3*(i-1)+2
			s=variables+3*(i-1)+3;	triple_d.append(s)
		elif i==len_n+1:
			a=variables+3*(i-1)+1;	d.append(a)
			b=false_var
			Cin=variables+3*(i-1)-1
			nc=variables+3*(i-1)+2
			s=variables+3*(i-1)+3;	triple_d.append(s); triple_d.append(nc)

		else:
			a=variables+3*(i-1)+1;	d.append(a)
			b=variables+3*(i-2)+1
			Cin=variables+3*(i-1)-1
			nc=variables+3*(i-1)+2
			s=variables+3*(i-1)+3;	triple_d.append(s)

		writeFA(a,b,Cin,s,nc);	eqs+=14

	variables+=(len_n-1)*4+3

	#we have that:
	#3d-2(n-S+1)=1
	#3d-2n+2S-2=1
	#3d+2S=2n+3

	#compute 3d+2s
	#let's see who has the biggest lenght
	max_len=max(len(s_lst),len(triple_d))

	#pad s_lst with zeros, aka false...
	for i in range(max_len-len(s_lst)):
		s_lst.append(false_var)

	#pad triple_d with zeros, aka false...
	for i in range(max_len-len(triple_d)):
		triple_d.append(false_var)
	#now add the padded 2s+3d...
	lhs_lst=[]
	#list2save.append("c equations for 3d+2s\n")
	for i in range(max_len):
		a=s_lst[i]
		b=triple_d[i]
		if  i==0: 
			Cin=false_var
		else:
			Cin=variables+i*2
		s=variables+i*2+1;	lhs_lst.append(s)
		nc=variables+i*2+2
		writeFA(a,b,Cin,s,nc);	eqs+=14

	lhs_lst.append(nc)
	variables+=max_len*2

	#convert 2n+3 to binary and store it to a list
	rhs=2*n+3
	rhs_lst=conv2bin(rhs)

	#now pad rhs and lhs
	max_len=max(len(rhs_lst),len(lhs_lst))

	#pad rhs_lst with zeros...
	for i in range(max_len-len(rhs_lst)):
		rhs_lst.append(0)

	#pad lhs_lst with zeros, aka false...
	for i in range(max_len-len(lhs_lst)):
		lhs_lst.append(false_var)

	for i in range(max_len):
		if rhs_lst[i]==1:
			eqs4d.append("%d 0\n" % (lhs_lst[i]))
		else :
			eqs4d.append("-%d 0\n" % (lhs_lst[i]))
		eqs+=1

	fi=(p-1)*(q-1)
	dapprox=gmpy2.invert(3,fi)
	dapprox_lst=conv2bin(dapprox)
	dapprox_lst[0]=1 #fix first bit

	#pad d and dapprox_lst
	max_len=max(len(dapprox_lst),len(d))

	for i in range(max_len-len(dapprox_lst)):
		dapprox_lst.append(0)
	for i in range(max_len-len(d)):
		d.append(false_var)
	diff=max_len-(2+(len_n+1)/2)

	truep=conv2bin(p)
	trueq=conv2bin(q)

	bits_known=0

	if pq==0 and dpq==0:
		#the non probabilistic mode...
		for i in range(int(ps*len(truep)),int(pe*len(truep))):
			bits_known+=1
			if truep[i]==1:
				list2save.append("%d 0\n" % (p_lst[i]))
			else:
				list2save.append("-%d 0\n" % (p_lst[i]))
			eqs+=1

		for i in range(int(qs*len(trueq)),int(qe*len(trueq))):
			bits_known+=1
			if trueq[i]==1:
				list2save.append("%d 0\n" % (q_lst[i]))
			else:
				list2save.append("-%d 0\n" % (q_lst[i]))
			eqs+=1
	
	if pq>0:
		if pq>1:
			pq=pq/100
		rand_table=[]
		for i in range(prime_bits):
			rand_table.append("p"+str(i))
			rand_table.append("q"+str(i))
		random.shuffle(rand_table)
		known_bits_p=[]
		known_bits_q=[]
		known_bits_d=[]
		
		#we know the LSB of p & q
		known_bits_p.append(0)
		known_bits_q.append(0)
		plb=int(gmpy2.sqrt(n/2))
		qlb=int(gmpy2.sqrt(n))
		qub=int(gmpy2.sqrt(n))
		cplb=conv2bin(plb)
		cqlb=conv2bin(qlb)
		cqub=conv2bin(qub)
		ex=0
		if len(cplb)==prime_bits:
			i=prime_bits-1
			while cplb[i]==1:
				known_bits_p.append(i)
				i-=1
				ex+=1

		i=prime_bits-2
		while cqlb[i]==0:
			known_bits_p.append(i)
			i-=1
			ex+=1

		i=prime_bits-1
		while cqlb[i]==1:
			known_bits_q.append(i)
			i-=1
			ex+=1
			
		i=prime_bits-2
		while cqub[i]==0:
			known_bits_p.append(i)
			i-=1
			ex+=1
		
		for i in range(int(2*prime_bits*pq)):
			if rand_table[i][:1]=="p":
				known_bits_p.append(int(rand_table[i][1:]))
			if rand_table[i][:1]=="q":
				known_bits_q.append(int(rand_table[i][1:]))
		
		joint_lst=known_bits_p+known_bits_q
		joint_lst=uniq(joint_lst)
        
        #Srarting from LSB, if I know either p or q, I know the other as well
		cnt=0
		cloop=True
		if nod==True:
			while cloop:
				if cnt in known_bits_p or cnt in known_bits_q:	
					known_bits_p.append(cnt)
					known_bits_q.append(cnt)
					cnt+=1
				else:
					cloop=False
		else:
			while cloop:
				if (cnt in known_bits_p) or (cnt in known_bits_q):
					known_bits_p.append(cnt)
					known_bits_q.append(cnt)
					known_bits_d.append(cnt)
					#from heninger's \tau(k) 
					known_bits_d.append(cnt+1)
					cnt+=1
				elif (cnt in known_bits_d and cnt+1 in known_bits_p and cnt+1 in known_bits_q):
					known_bits_p.append(cnt)
					known_bits_q.append(cnt)
					known_bits_d.append(cnt)
					#from heninger's \tau(k) 
					known_bits_d.append(cnt+1)
				else:
					cloop=False
		cnt=prime_bits-1
		
		#do the same for MSB...
		#cloop=True
		#while cloop:
		#	if cnt in known_bits_p or cnt in known_bits_q:	
		#		known_bits_p.append(cnt)
		#		known_bits_q.append(cnt)
		#		cnt-=1
		#	else:
		#		cloop=False
		
		known_bits_p.append(prime_bits-1)
		known_bits_q.append(prime_bits-1)
		
		
		known_bits_p=uniq(known_bits_p)
		known_bits_q=uniq(known_bits_q)
		
		for i in known_bits_p:		
			bits_known+=1
			if truep[i]==1:
				list2save.append("%d 0\n" % (p_lst[i]))
			else:
				list2save.append("-%d 0\n" % (p_lst[i]))
			eqs+=1

		for i in known_bits_q:		
			bits_known+=1
			if trueq[i]==1:
				list2save.append("%d 0\n" % (q_lst[i]))
			else:
				list2save.append("-%d 0\n" % (q_lst[i]))
			eqs+=1
			
		if nod==False:
			#the upper half of d is known...
			for i in range(len(d)/2,len(d)-1):
				known_bits_d.append(i)
			#the LSB is known
			known_bits_d.append(0)
		else:
				known_bits_d=[]
				
		for i in known_bits_d:		
			bits_known+=1
			if dapprox_lst[i]==1:
				eqs4d.append("%d 0\n" % (d[i]))
			else:
				eqs4d.append("-%d 0\n" % (d[i]))
			eqs+=1
		
	
	if dpq>0:
		if dpq>1:
			dpq=dpq/100
		rand_table=[]
		for i in range(prime_bits):
			rand_table.append("p"+str(i))
			rand_table.append("q"+str(i))
		for i in range(2*prime_bits):
			rand_table.append("d"+str(i))
		random.shuffle(rand_table)
		
		known_bits_p=[]
		known_bits_q=[]
		known_bits_d=[]
		
		for i in range(int(len(rand_table)*dpq)):
			if rand_table[i][:1]=="p":
				known_bits_p.append(int(rand_table[i][1:]))
			if rand_table[i][:1]=="q":
				known_bits_q.append(int(rand_table[i][1:]))
			if rand_table[i][:1]=="d":
				known_bits_d.append(int(rand_table[i][1:]))

		#we know the LSB of p, q & d
		known_bits_p.append(0)
		known_bits_q.append(0)
		known_bits_d.append(0)
		known_bits_d.append(len(d)-1)
		
		plb=int(gmpy.sqrt(n/2))
		qlb=int(gmpy.sqrt(n))
		qub=int(gmpy.sqrt(n))
		cplb=conv2bin(plb)
		cqlb=conv2bin(qlb)
		cqub=conv2bin(qub)
		ex=0
		if len(cplb)==prime_bits:
			i=prime_bits-1
			while cplb[i]==1:
				known_bits_p.append(i)
				i-=1
				ex+=1

		i=prime_bits-2
		while cqlb[i]==0:
			known_bits_p.append(i)
			i-=1
			ex+=1

		i=prime_bits-1
		while cqlb[i]==1:
			known_bits_q.append(i)
			i-=1
			ex+=1
			
		i=prime_bits-2
		while cqub[i]==0:
			known_bits_p.append(i)
			i-=1
			ex+=1

		joint_lst=known_bits_p+known_bits_q
		joint_lst=uniq(joint_lst)
        
        	#Srarting from LSB, if I know either p or q, I know the other as well
		cnt=0
		cloop=True
		
		while cloop:
			if (cnt in known_bits_p) or (cnt in known_bits_q) or (cnt in known_bits_d)  or cnt+1 in known_bits_d:	
				known_bits_p.append(cnt)
				known_bits_q.append(cnt)
				known_bits_d.append(cnt)
				#from heninger's \tau(k)
				cnt+=1
			else:
				cloop=False
	
		known_bits_d=uniq(known_bits_d)
		cnt=prime_bits-1
		
		#do the same for MSB...
		cloop=True
		while cloop:
			if cnt in known_bits_p or cnt in known_bits_q:	
				known_bits_p.append(cnt)
				known_bits_q.append(cnt)
				cnt-=1
			else:
				cloop=False
		
		known_bits_p=uniq(known_bits_p)
		known_bits_q=uniq(known_bits_q)
		known_bits_d=uniq(known_bits_d)
		
		for i in known_bits_p:		
			bits_known+=1
			if truep[i]==1:
				list2save.append("%d 0\n" % (p_lst[i]))
			else:
				list2save.append("-%d 0\n" % (p_lst[i]))
			eqs+=1

		for i in known_bits_q:		
			bits_known+=1
			if trueq[i]==1:
				list2save.append("%d 0\n" % (q_lst[i]))
			else:
				list2save.append("-%d 0\n" % (q_lst[i]))
			eqs+=1
		
		if nod==False:
			#the upper half of d is known...
			for i in range(len(d)/2,len(d)-1):
				known_bits_d.append(i)
				
		for i in known_bits_d:		
			bits_known+=1
			if dapprox_lst[i]==1:
				list2save.append("%d 0\n" % (d[i]))
			else:
				list2save.append("-%d 0\n" % (d[i]))
			eqs+=1
	
	if nod==False:
		list2save+=eqs4d
	else:
		variables=original_variables
	d_lst=d
	
	list2save=uniq(list2save)	
	eqs=len(list2save)-1

	list2save.insert(0,"p cnf %d %d\n" %(variables,eqs))
	for i in list2save:
		fout.write(i)
	fout.close()

	#needed to free resources if we are working with large output...
	if prime_bits>=512:
		print ("Let me catch my breath here, too many bits...\n")
		ps = Popen(["sleep", "3"])
		os.waitpid(ps.pid, 0)
		print ("To infinity and beyond! :)\n")
		
	#free some memory
	del list2save
	del eqs4d
	gc.collect()
	
	print ("Preprocessing...") 
	#now lets simplify the system
	
	ps = subprocess.Popen(["./minisat2.2","-dimacs=solve.cnf", "new_cnf.dimacs"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	os.waitpid(ps.pid, 0)
	os.remove("new_cnf.dimacs")
	
	print ("Solving...") 
	#solve the problem
	#with minisat
	if sat_solver==0:
		rtn,out=subprocess_execute(["./minisat2.2", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[3]
			ram=out[-4].split()[3]
			print (ram+" MB",ntime+ " seconds")
	#with picosat
	elif sat_solver==1:
		rtn,out=subprocess_execute(["./picosat", "solve.cnf", "-n", "-v"],time2kill)
		if len(out)>0:
			ram=out[-2].split()[1]
			ntime=out[-1].split()[1]
			print ram+" MB",ntime+ " seconds"
	#with glucose
	elif sat_solver==2:
		rtn,out=subprocess_execute(["./glucose", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-2].split()[4]
			print ntime+ " seconds"
	#with glueminisat
  	elif sat_solver==3:
		rtn,out=subprocess_execute(["./glueminisat", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[3]
			ram=out[-4].split()[3]
			print ram+" MB",ntime+ " seconds"
	#with mxc-sat09
  	elif sat_solver==4:
		rtn,out=subprocess_execute(["./mxc-sat09", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-2].split()[1].replace("s","")
			print ntime+ " seconds"
  	#with lr_gl_shr
  	elif sat_solver==5:
		rtn,out=subprocess_execute(["./lr_gl_shr", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ram=out[-4].split()[3]
			ntime=out[-3].split()[3]
			print ram+" MB",ntime+ " seconds"
  	#with precosat
  	elif sat_solver==6:
		rtn,out=subprocess_execute(["./precosat", "solve.cnf", "-n", "-v"],time2kill)
		if len(out)>0:
			ram=out[-1].split()[3]
			ntime=out[-1].split()[1]
			print ram+" MB",ntime+ " seconds"
  	#with ebminisat
  	elif sat_solver==7:
		rtn,out=subprocess_execute(["./ebminisat", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[4]
			ram=out[-4].split()[4]
			print ram+" MB",ntime+ " seconds"
    #with Spear-32_121
	elif sat_solver==8:
		rtn,out=subprocess_execute(["./Spear-32_121", "--dimacs", "solve.cnf", "--time"],time2kill)
		if len(out)>0:
			ntime=out[-1].split()[2]
			print ntime+ " seconds"
	#with clasp2
	elif sat_solver==9:
		rtn,out=subprocess_execute(["./clasp2", "solve.cnf", "-q", "m0"],time2kill)
		if len(out)>0:
			ntime= out[-1].split()[4].replace("s","")
			print ntime+ " seconds"
	elif sat_solver==10:
		str_cores= "--threads=%d"%cores
		rtn,out=subprocess_execute(["./cryptominisat-snt-st", str_cores, "--greedyunbound", "solve.cnf", "output.out"],time2kill)
		if len(out)>0:
		#rtn,out=subprocess_execute(["./forl-drup", "-t=8", "--greedyunbound", "solve.cnf", "output.out"],time2kill)
			print out[-3].split()[5]+" seconds"
	elif sat_solver==11:
		str_cores= "-ncores=%d"%cores
		rtn,out=subprocess_execute(["./manysat2.0", str_cores, "-verb=0", "-no-luby","-rinc=1.5","-phase-saving=0","-rnd-freq=0.02","solve.cnf"],time2kill)
		if len(out)>0:
		#-no-luby -rinc=1.5 -phase-saving=0 -rnd-freq=0.02
			#ntime= float(out[-2].split()[3])/cores
			#print "%0.4f seconds" % ntime
			print "exit code %d"%rtn
			for ln in out:
				print ln
	elif sat_solver==12:
		os.system("./splitter solve.cnf out.txt -threads=8 -verb=0 -no-luby -rinc=1.5 -phase-saving=0 -rnd-freq=0.02")
	elif sat_solver==13:
		rtn,out=subprocess_execute(["./minisat2.2", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[3]
			ram=out[-4].split()[3]
			print "\n MiniSAT Solver benchmark: \t"
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./picosat", "solve.cnf", "-n", "-v"],time2kill)
		if len(out)>0:
			ram=out[-2].split()[1]
			ntime=out[-1].split()[1]
			print "\n PicoSAT Solver benchmark: "
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./glucose", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-2].split()[4]
			print "\n Glucose Solver benchmark: "
			print ntime+ " seconds"
		rtn,out=subprocess_execute(["./glueminisat", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[3]
			ram=out[-4].split()[3]
			print "\n Glue MiniSAT Solver benchmark: "
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./lr_gl_shr", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ram=out[-4].split()[3]
			ntime=out[-3].split()[3]
			print "\n lr_gl_shr Solver benchmark: "
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./precosat", "solve.cnf", "-n", "-v"],time2kill)
		if len(out)>0:
			ram=out[-1].split()[3]
			ntime=out[-1].split()[1]
			print "\n Precosat Solver benchmark: "
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./ebminisat", "solve.cnf", out_file],time2kill)
		if len(out)>0:
			ntime=out[-3].split()[4]
			ram=out[-4].split()[4]
			print "\n ebminisat Solver benchmark: "
			print ram+" MB",ntime+ " seconds"
		rtn,out=subprocess_execute(["./Spear-32_121", "--dimacs", "solve.cnf", "--time"],time2kill)
		if len(out)>0:
			ntime=out[-1].split()[2]
			print "\n Spear Solver benchmark: "
			print ntime+ " seconds"
		rtn,out=subprocess_execute(["./clasp2", "solve.cnf", "-q", "m0"],time2kill)
		if len(out)>0:
			ntime= out[-1].split()[4].replace("s","")
			print "\n Clasp2 Solver benchmark: "
			print ntime+ " seconds"
		str_cores= "--threads=%d"%cores
		rtn,out=subprocess_execute(["./cryptominisat-snt-st", str_cores, "--greedyunbound", "solve.cnf", "output.out"],time2kill)
		if len(out)>0:
		#rtn,out=subprocess_execute(["./forl-drup", "-t=8", "--greedyunbound", "solve.cnf", "output.out"],time2kill)
			print "\n Cryptominisat Solver benchmark: "
			print out[-3].split()[5]+" seconds"

		str_cores= "-ncores=%d"%cores
		rtn,out=subprocess_execute(["./manysat2.0", str_cores, "-verb=0", "solve.cnf", "output.out"],time2kill)
		if len(out)>0:
		#-no-luby -rinc=1.5 -phase-saving=0 -rnd-freq=0.02
			#ntime= float(out[-2].split()[3])
			#print "%0.4f seconds" % ntime
			print "\n Manysat2.0 Solver benchmark: "
			print "Run the tool explicitily for results \n exit code %d"%rtn
			for ln in out:
				print ln
		#print "\n Splitter Solver benchmark: "
		#os.system("./splitter solve.cnf out.txt -threads=8 -verb=0 -no-luby -rinc=1.5 -phase-saving=0 -rnd-freq=0.02")
		
	merged_known_bits=known_bits_p+known_bits_q
	merged_known_bits=uniq(merged_known_bits)
	#dist_bits=len(merged_known_bits)-ex
	#print "Percent of total distinct bits known: %.3f" % (100*(1.0*dist_bits/prime_bits))

	if os.path.isfile("output.out"):
		os.remove("output.out")#might not exist depending on the solver...
	os.remove("solve.cnf")
	
os.remove(original_cnf)
