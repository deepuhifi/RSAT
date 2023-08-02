This is an ReadMe file to explain the workings of the RSAT tool with some modfication done to work with latest packages.

Tested in Kali Linux 2023.2 WSL

#Requirements
# Install python2
sudo apt-get install python2 

# install pip2 
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
python2 get-pip.py

#Install dependencies for RSAT
python2 -m pip install gymp2 argparse

# git clone 

cd RSATv0.2
python2 rsat.py -b 512 -pq 0.2 -s all


