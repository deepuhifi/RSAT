This is an ReadMe file to explain the workings of the RSAT tool with some modfication done to work with latest packages.

Tested in Kali Linux 2023.2 WSL

# Requirements

#Install python2

sudo apt-get install python2 

#Install pip2 

curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py

python2 get-pip.py

#Install dependencies for RSAT

python2 -m pip install gymp2 argparse

git clone https://github.com/deepuhifi/RSAT

cd RSAT

python2 rsat_modified.py -b 512 -pq 0.8 -s 13

#This command runs the modified version of rsat tool on ramdom selected 512 bits of input bits with 80% of of the prime number p and q known to the attacker. and calls the benchmark of different solvers to solve RSA-512 

