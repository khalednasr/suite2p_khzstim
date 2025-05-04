import os
import suite2p
from suite2p import gui

exp = '20250502'
culture = 'culture3'
trial = 'trial0'

trial_subpath = f'{exp}/{culture}/{trial}'

local_data_dir = 'D:\\nextcloud\\work\\data\\calcium'
# local_data_dir = 'D:\\User\\AG_Dean\\Hana_Sheldon'
remote_data_dir = '/home/khzstimpi/data'

trial_dir = os.path.join(local_data_dir,trial_subpath)
if not os.path.exists(os.path.join(trial_dir, 'sample.bin')):
    os.system(f'scp -r khzstimpi@khzstimpi:{remote_data_dir}/{trial_subpath}/* {trial_dir}')

save_path = os.path.join(trial_dir, 'suite2p', 'plane0')
ops = suite2p.default_ops()
ops['data_path'] = [trial_dir]
ops['input_format'] = 'nd2'
ops['do_registration'] = True
# ops['threshold_scaling'] = 2
# ops['high_pass'] = 5

if not os.path.exists(os.path.join(save_path, 'iscell.npy')):
    suite2p.run_s2p(ops=ops)

gui.run(os.path.join(save_path, 'stat.npy'))
