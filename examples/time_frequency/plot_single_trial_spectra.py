"""
======================================
Investigate Single Trial Power Spectra
======================================

In this example we will look at single trial spectra and then
compute average spectra to identify channels and
frequencies of interest for subsequent TFR analyses.
"""

# Authors: Denis Engemann <d.engemann@fz-juelich.de>
#
# License: BSD (3-clause)

print __doc__

import numpy as np
import scipy
from scipy import fftpack

import mne
from mne import fiff
from mne.datasets import sample
from mne.time_frequency import compute_epochs_psd
import matplotlib.pyplot as plt
###############################################################################
# Set parameters
data_path = sample.data_path()
raw_fname = data_path + '/MEG/sample/sample_audvis_raw.fif'
event_fname = data_path + '/MEG/sample/sample_audvis_raw-eve.fif'

# Setup for reading the raw data
raw = fiff.Raw(raw_fname, preload=True)
events = mne.read_events(event_fname)

tmin, tmax, event_id = -1, 1, 1
include = []
raw.info['bads'] += ['MEG 2443']  # bads

# picks MEG gradiometers
picks = fiff.pick_types(raw.info, meg='grad', eeg=False, eog=True,
                        stim=False, include=include, exclude='bads')

epochs = mne.Epochs(raw, events, event_id, tmin, tmax, picks=picks,
                    baseline=(None, 0), reject=dict(grad=4000e-13, eog=150e-6))


# setup generator
NFFT = 256  # the FFT size (NFFT). Ideally a power of 2
n_jobs = 2
generate_psd = compute_epochs_psd(epochs, fmin=2, fmax=200, NFFT=NFFT,
                                  n_jobs=n_jobs, proj=True, verbose=False)

# accumulate psds and save psds from first trial separately
average_psds, max_trial = None, 20
for ii, (psds, freqs) in enumerate(generate_psd):
    if ii > max_trial:
        break
    # use dB and
    psds = 10 * np.log10(psds)  # compute it here to avoid artifacts
    if ii == 0:
        average_psds = np.empty_like(psds)
        first_psds =  psds
    average_psds += psds
average_psds = average_psds / max_trial


fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True, figsize=(10, 5))

fig.suptitle('Single trial power', fontsize=12)

freq_mask = freqs < 150
freqs = freqs[freq_mask]

ax1.set_title('single trial', fontsize=10)
ax1.imshow(first_psds[:, freq_mask].T, aspect='auto', origin='lower')
ax1.set_yticks(np.arange(0, len(freqs), 10))
ax1.set_yticklabels(freqs[::10].round(1))
ax1.set_ylabel('Frequency (Hz)')

ax2.set_title('averaged over trials', fontsize=10)
ax2.imshow(average_psds[:, freq_mask].T, aspect='auto', origin='lower')
ax2.set_xticks(np.arange(0, len(picks), 30))
ax2.set_xticklabels(picks[::30])
ax2.set_xlabel('MEG channel index (Gradiomemters)')

mne.viz.tight_layout()
plt.show()

# In the second image we clearly observe certain channel groups exposing
# stronger power than others. Second, in comparison to the single
# trial image we can see the frequency extent slightly growing for these
# channels which might indicate oscillatory responses.
# The ``plot_time_frequency.py`` example investigates one of the channels
# around index 140.
# Finally, also note the power line artifacts across all channels.
