# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 12:02:26 2017

@author: anthony
"""

import rct
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set() # styling
import scipy.signal as sg
import peakutils as pu

#%% Run Variables
# original tests performed on run10 from canyon series
#run = '16';
#series = 'desert'
run = '31';
series = 'anechoic2'
path = 'C:\\Users\\anthony\\Desktop\\e4e\\'+series+'\\' # Inside here should be a RUN_000## folder

# TODO: Use META_DATA file for literals and run variables
Fsx         = 2000000.0       # sampling frequency of input data
F_REAL      = 172950830.0   # REAL COLLAR
F_FAKE      = 172600000.0   # FAKE COLLAR

Fx          = F_REAL        # target collar frequency
Fc          = 172500000.0   # Center frequency
FFT_LENGTH  = 4096
Fsf         = Fsx/FFT_LENGTH # sampling frquency of fft

pW          = 0.02 # pulse width [seconds]
pT          = 1.6 # pulse period [seconds]

xbin        = int( np.round( (Fx - Fc) / Fsx * FFT_LENGTH ) )
refbin      = int( np.round( (F_FAKE - Fc) / Fsx * FFT_LENGTH ) )
raw_files   = rct.getfiles(path,run)

#%%

windows = ['boxcar', 'triang', 'blackman', 'hamming', 'hann', 'bartlett', 
           'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall', 'barthann', 
#           'kaiser (needs beta)', 
#           'gaussian (needs std)', 
#           'general_gaussian (needs power, width)', 
#           'slepian (needs width)', 
#           'chebwin (needs attenuation)
            ]

# Look at one period of the time domain data
x = rct.raw2complex(raw_files[0])
x_slice = x[:int(pT*Fsx)]

f_Pxx = []
for w in windows:
    f_Pxx.append(sg.welch(x,Fsx,window=w,nperseg=FFT_LENGTH,return_onesided=False))
    
[f_Pxx_1,f_Pxx_2] = np.split(np.array(f_Pxx),2)
[w1, w2] = np.split(np.array(windows),2)

plt.figure(1)

ax1 = plt.subplot(1,2,1)
plt.title('Windowing effect on target frequency bin of the FFT 1/2')
plt.axvline(f_Pxx[0][0][xbin], c='c', linestyle='--')
plt.axvline(f_Pxx[0][0][refbin], c='m', linestyle='--')

for f,Pxx in f_Pxx_1:
    plt.semilogy(f,Pxx)

plt.legend(np.concatenate((['Target Bin','Reference Bin'],w1)))
plt.xlim(f_Pxx[0][0][xbin-3],f_Pxx[0][0][xbin+3])

ax2 = plt.subplot(1,2,2, sharex=ax1, sharey=ax1)
plt.title('Windowing effect on target frequency bin of the FFT 2/2')
plt.axvline(f_Pxx[0][0][xbin], c='c', linestyle='--') 
plt.axvline(f_Pxx[0][0][refbin], c='m', linestyle='--')   

for f,Pxx in f_Pxx_2:
    plt.semilogy(f,Pxx)

plt.legend(np.concatenate((['Target Bin','Reference Bin'],w2)))    
plt.xlim(f_Pxx[0][0][xbin-3],f_Pxx[0][0][xbin+3])

#%% Compare window function to uniform in the fft reconstructed time domain
w0 = np.ones(FFT_LENGTH)
w1 = 'barthann'

Pxx0 = rct.fftFromFiles2([raw_files[0]],FFT_LENGTH,xbin,Fsx,w0)
Pxx1 = rct.fftFromFiles2([raw_files[0]],FFT_LENGTH,xbin,Fsx,w1)

ft = np.linspace(1/Fsf,len(Pxx0)/Fsf,len(Pxx0))

plt.figure(2)
ax3 = plt.subplot(1,2,1)
plt.title('Frequency filter signal with a uniform window')
plt.semilogy(ft, abs(Pxx0))

ax4 = plt.subplot(1,2,2, sharex=ax3,sharey=ax3)
plt.title('Frequency filter signal with a {0}'.format(w1))
plt.semilogy(ft, abs(Pxx1))