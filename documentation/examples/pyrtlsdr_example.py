"""Module for RTL-SDR server operations, including configuration and PSD plotting."""

from matplotlib.pyplot import psd, show, xlabel, ylabel
from rtlsdr import RtlSdr

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.4e6 # 2.4 MHz
sdr.center_freq = 96.3e6 # 96.3 MHz
sdr.gain = 27 # dB

samples = sdr.read_samples(256*1024)
sdr.close()

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')

show()