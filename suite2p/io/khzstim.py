import numpy as np
import pyqtgraph as pg
import os
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

plt.rcParams.update({'font.size': 18})

class KHZStimDataAnalysis:
    def __init__(self, stats_file, subsampling_factor=32, sampling_rate=400000, buffer_size=16384,
              electrode_spacing=10E-3, amplifier_gain_level=1, vref=10):
        stats_file = Path(stats_file)

        trial_dir = stats_file.parent.parent.parent
        sample_file = trial_dir / 'sample.bin'
        settings_file = trial_dir / 'settings.npz'

        print(f'Loading khz stimulation data from {trial_dir}...')
    
        sample_data = np.fromfile(sample_file, dtype=np.uint16)
        settings = np.load(settings_file) if os.path.exists(settings_file) else {}
    
        sample_data = sample_data[buffer_size*2:]

        if subsampling_factor > 1:
            sample_data = sample_data[::subsampling_factor]
            sampling_rate = sampling_rate / subsampling_factor
    
        adc_voltages = - \
            ((((sample_data & 4095).astype(np.float32)-2048)/2048) * vref)
        applied_efield = (
            adc_voltages / self.get_amplifier_gain(amplifier_gain_level)) / electrode_spacing
        din0 = (sample_data & (1 << 13)) >> 13
        # din1 = (sample_data & (1 << 14)) >> 14

        efield_times = np.arange(0, len(applied_efield), dtype=np.float32) / sampling_rate

        frame_indices = np.where(np.diff(din0) == 1)[0]
        frame_times = efield_times[frame_indices]
        frame_rate = 1.0/np.median(np.diff(frame_times))

        mod_period = 1.0/settings['mod_frequency']        
        mod_periods_per_block = int(np.ceil(settings['block_duration']/mod_period))
    
        t = float(settings['nostim_pre_post_duration'])
        pulse_times = []
        for phase in settings['phases']:
            t_pulse = t + (mod_periods_per_block-1) * mod_period + mod_period*phase/360
            pulse_times.append(t_pulse)
            t += mod_periods_per_block * mod_period + settings['nostim_interblock_duration']
        pulse_times = np.array(pulse_times)

        pulse_frames = np.array([int(np.argmin(np.abs(frame_times-t))) for t in pulse_times])

        for key in settings.keys():
            setattr(self, key, settings[key])
        
        self.efield = applied_efield
        self.efield_times = efield_times
        self.efield_sampling_rate = sampling_rate
        self.frame_times = frame_times
        self.frame_rate = frame_rate
        self.pulse_frames = pulse_frames
        print('Done')
    
    def get_amplifier_gain(self, level):
        gains = [1, 5, 10, 50, 100, 200]
        return gains[level-1]

    def plot_stim(self, tracebox):
        for frame_index, phase, pamp in zip(self.pulse_frames, self.phases, self.pamps):
            # tracebox.addItem(pg.InfiniteLine(frame_index, label=f'phi={phase}\namp={int(pamp)}', pen=(255,0,0,125)))
            tracebox.addItem(pg.InfiniteLine(frame_index, pen=(255,0,0,125)))
        
    def plot_analysis(self, graphics_layout, selected, f, fneu, spikes):
        # selected = [0, 49, 3, 24, 81, 35, 7]
        data = spikes[selected]
        
        window_length_post_pulse = 3
        window_length_pre_pulse = 3
        
        frames_post_pulse = int(np.ceil(window_length_post_pulse*self.frame_rate))
        frames_pre_pulse = int(np.ceil(window_length_pre_pulse*self.frame_rate))

        
        pulse_windows = []
        for index in self.pulse_frames:
            window = data[:, index-frames_pre_pulse : index+frames_post_pulse]
            pulse_windows.append(window)
        pulse_windows = np.array(pulse_windows)

        unique_phases = np.unique(self.phases)
        unique_pamps = np.unique(self.pamps)

        pamp = unique_pamps[-1]            
        
        graphics_layout.clear()
        for i in range(data.shape[0]):
            p = graphics_layout.addPlot(row=i, col=0)
            if i==0:
                p.addLegend()
                
            p.addItem(pg.InfiniteLine(frames_pre_pulse, pen=pg.mkPen(color=(255,0,255,200), width=2)))
            
            for j, phase in enumerate(unique_phases):
                phase_reponse = pulse_windows[(self.phases==phase)&(self.pamps==pamp), i]
                print(phase_reponse.shape)

                avg = phase_reponse.mean(axis=0)
                color = pg.intColor(j)
                p.plot(avg, pen=pg.mkPen(color=color, width=2), name = f'Phase = {int(180-phase)}')

        # print(selected)
        
        # plt.figure()
        # nrows = int(np.ceil(data.shape[0]/2))
        # for i in range(data.shape[0]):
        #     ax = plt.subplot(nrows, 2, i+1)
        #     for j, phase in enumerate(unique_phases):
        #         phase_reponse = pulse_windows[(self.phases==phase)&(self.pamps==pamp), i]

        #         avg = phase_reponse.mean(axis=0)
        #         t = np.arange(len(avg))/self.frame_rate - window_length_pre_pulse
        #         plt.plot(t, avg, label = 'Pulse at peak' if phase==180 else 'Pulse at trough', linewidth=2)

        #     # plt.ylim((0, 500))
        #     # ax.axis('off')
        #     plt.box(False)
        #     ax.get_yaxis().set_visible(False)
        #     plt.xlabel('Time relative to pulse (s)')
        #     if i==0:
        #         plt.legend()
        #     if i < data.shape[0]-2:
        #         ax.get_xaxis().set_visible(False)
                
        # plt.show()
        
        
        
