"""Export archived seed-100 scientific plots and verified bilingual reports.

Run with the atsc Python interpreter. This script never launches SUMO or training.
Use --refresh to update figures 01/02/03/04/07 and authorized report captions from
the completed isolated action audit, preserving evaluation scorecards and 05/06.
The original creation mode refuses existing outputs.
"""

import sys
if '--refresh' in sys.argv:
 from seed100_analysis_refresh import main
 main()
 raise SystemExit(0)

from pathlib import Path
import csv,json,hashlib,statistics,math,re,ast,zipfile
import numpy as np
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import os
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
out=Path('results/comparison_result/drl_seed100_comprehensive_report_en.md')
vi_out=out.with_name('drl_seed100_comprehensive_report_vi.md')
plotdir=Path('results/seed100/plots/detailed_analysis')
if vi_out.exists() or plotdir.exists():raise FileExistsError('New bilingual report or detailed_analysis directory already exists')
if out.exists():raise FileExistsError(out)
source_names=['DRL/gym_env.py','DRL/core/environment.py','DRL/train_multiscenario.py','DRL/evaluate.py','DRL/metrics.py','run_pipeline_seed100.py','DRL/configs/traci.yaml','DRL/requirements.txt']
history_names=['results/comparison_result/v1_baseline_drl_summary_107_710.md','results/comparison_result/drl_seed107_report.md','results/comparison_result/drl_seed710_report.md']
files=set(Path(p) for p in source_names+history_names)
for directory in ['results/seed100','evaluation/seed100','runs/ppo_seed100']:
 files.update(p for p in Path(directory).rglob('*') if p.is_file())
files.update([Path('models/seed100/training_metadata.json'),Path('results/comparison_result/drl_seed100_v2_report.md')])
files.update(Path(f'results/seed{s}/summary_final.csv') for s in (107,710))
files.update(Path('results/comparison_result').glob('*.md'))
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
sources={p:Path(p).read_text(encoding='utf-8-sig') for p in source_names+history_names}
meta=json.loads(Path('models/seed100/training_metadata.json').read_text())
tim=json.loads(Path('results/seed100/pipeline_timings.json').read_text())
pre=json.loads(Path('results/seed100/preflight_check.json').read_text())
cfg=yaml.safe_load(sources['DRL/configs/traci.yaml'])
runconfig=json.loads(Path('results/seed100/run_config.json').read_text())
SC=('low','medium','high','imbalance');MS=('fixed_time','rule_based','drl_ppo','drl_ppo_final')
MT=('queue_length','waiting_time','average_speed','arrived_count','vehicles_in_network')
names=dict(zip(MS,('Fixed-Time','Rule-Based','PPO best','PPO final')))
def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def f(v):
 v=float(v)
 assert math.isfinite(v)
 return f'{v:.6f}'
summary={(r['method'],r['scenario']):r for r in read('results/seed100/summary_final.csv')}
episodes={};RAW={};checks=0
for method in MS:
 groups={}
 if method in MS[:2]:
  supplied=[]
  for p in Path(f'evaluation/seed100/baselines/{method}').rglob('metrics_*.csv'):
   rows=read(p);groups[rows[0]['scenario'],int(rows[0]['seed'])]=rows
  for p in Path(f'evaluation/seed100/baselines/{method}').rglob('episode_*.csv'):supplied+=read(p)
 else:
  folder='best' if method=='drl_ppo' else 'final'
  for r in read(f'evaluation/seed100/{folder}/metrics.csv'):groups.setdefault((r['scenario'],int(r['seed'])),[]).append(r)
  supplied=read(f'evaluation/seed100/{folder}/episodes.csv')
  read(f'evaluation/seed100/{folder}/summary.csv')
 supplied={(r['scenario'],int(r['seed'])):r for r in supplied}
 assert set(groups)=={(s,k) for s in SC for k in (101,102,103)}
 for (s,k),rows in groups.items():
  assert len(rows)==720 and all(abs(float(r['simulation_time'])-5*(i+1))<1e-8 for i,r in enumerate(rows))
  vals={m:sum(float(r[m]) for r in rows) if m=='arrived_count' else statistics.fmean(float(r[m]) for r in rows) for m in MT}
  for m in MT:
   assert math.isclose(vals[m],float(supplied[s,k][m]),rel_tol=1e-10,abs_tol=1e-8)
   checks+=1
  episodes[method,s,k]=vals
  RAW[method,s,k]=rows
 for s in SC:
  for m in MT:
   vals=[episodes[method,s,k][m] for k in (101,102,103)]
   for suffix,value in [('mean',statistics.fmean(vals)),('std',statistics.stdev(vals))]:
    assert math.isclose(value,float(summary[method,s][m+'_'+suffix]),rel_tol=1e-10,abs_tol=1e-8)
    checks+=1
def monitor(p):
 with Path(p).open(encoding='utf-8') as stream:
  next(stream);return list(csv.DictReader(stream))
tr=monitor('runs/ppo_seed100/train.monitor.csv')
vr=monitor('evaluation/seed100/validation/episodes.monitor.csv')
resets=[json.loads(l) for l in Path('runs/ppo_seed100/training_episodes.jsonl').read_text().splitlines()]
assert len(tr)==meta['completed_training_episodes']==836
assert all(int(r['l'])==720 and 1000<=int(r['sumo_seed'])<=999999 for r in tr)
for i in range(0,836,4):assert {r['scenario'] for r in resets[i:i+4]}==set(SC)
with np.load('evaluation/seed100/validation/evaluations.npz') as z:
 steps=z['timesteps'].copy();rewards=z['results'].copy();lengths=z['ep_lengths'].copy()
assert rewards.shape==(20,4) and len(vr)==80 and np.all(lengths==720)
for i in range(20):
 assert [r['scenario'] for r in vr[4*i:4*i+4]]==list(SC)
 assert all(int(r['sumo_seed'])==999 for r in vr[4*i:4*i+4])
 np.testing.assert_allclose([float(r['r']) for r in vr[4*i:4*i+4]],rewards[i],atol=1e-5)
means=rewards.mean(axis=1);best=int(np.argmax(means));bs=int(steps[best])
for rel,expected in [('best_model/best_model.zip',bs),('ppo_seed100_final.zip',meta['actual_timesteps'])]:
 p=Path('models/seed100')/rel
 with zipfile.ZipFile(p) as z: assert json.loads(z.read('data'))['num_timesteps']==expected
eventfiles=list(Path('runs/ppo_seed100').rglob('events.out.tfevents.*'));assert len(eventfiles)==1
ea=EventAccumulator(str(eventfiles[0]),size_guidance={'scalars':0});ea.Reload()
tags=['rollout/ep_len_mean','eval/mean_ep_length','train/policy_gradient_loss','train/loss','rollout/ep_rew_mean','eval/mean_reward','time/fps','train/explained_variance','train/approx_kl','train/clip_fraction','train/entropy_loss','train/value_loss','train/learning_rate']
ts={t:ea.Scalars(t) for t in tags}
assert all(math.isfinite(e.value) for a in ts.values() for e in a)
np.testing.assert_allclose([e.value for e in ts['eval/mean_reward']],means,rtol=1e-6)
old={k:{(r['method'],r['scenario']):r for r in read(f'results/seed{k}/summary_final.csv')} for k in (107,710)}
def avg(m,s,k):return float(summary[m,s][k+'_mean'])
def std(m,s,k):return float(summary[m,s][k+'_std'])
def imp(p,b,k):return 100*(p-b)/b if k in ('average_speed','arrived_count') else 100*(b-p)/b
def near(t,s):return min(ts[t],key=lambda e:abs(e.step-s))


# Scientific figures use archived observations only; no project entry point is imported.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PIL import Image
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                     'axes.labelsize':10,'legend.fontsize':9,'savefig.dpi':300})
plotdir.mkdir(parents=True)
COLORS={'fixed_time':'#737b85','rule_based':'#e58d2c','drl_ppo':'#157f99','drl_ppo_final':'#9562a6'}
LABEL={'queue_length':'Queue (vehicles)','waiting_time':'Waiting (s)',
       'average_speed':'Speed (m/s)','arrived_count':'Arrivals (vehicles)',
       'vehicles_in_network':'Network vehicles'}
PLOTS=[
'01_learning_curves_reward_and_val.png',
'02_tensorboard_losses_and_diagnostics.png',
'03_action_decision_and_override_matrix.png',
'04_timeseries_3600s_all_scenarios.png',
'05_per_seed_breakdown_101_102_103.png',
'06_ppo_best_vs_final_stability.png',
'07_v1_to_v2_progression_comparison.png']
def save(fig,index):
 fig.savefig(plotdir/PLOTS[index],dpi=300,facecolor='white')
 plt.close(fig)
 print('Created '+PLOTS[index],flush=True)
def xy(tag):
 return np.array([e.step for e in ts[tag]]),np.array([e.value for e in ts[tag]])
def ema(values,alpha=0.10):
 a=[float(values[0])]
 for v in values[1:]:a.append(alpha*float(v)+(1-alpha)*a[-1])
 return a
def learning_axis(ax):
 ax.set_xlim(0,meta['actual_timesteps'])
 ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1000:g}k'))
 ax.set_xlabel('Training decision steps');ax.grid(alpha=.22)
fig,axs=plt.subplots(1,2,figsize=(15,5),layout='constrained')
x,y=xy('rollout/ep_rew_mean')
axs[0].plot(x,y,color=COLORS['drl_ppo'],alpha=.25,label='Raw: 100-episode moving mean')
axs[0].plot(x,ema(y),color=COLORS['drl_ppo'],lw=2,label='EMA on logged series (alpha=0.10)')
axs[0].set_title('A. Training return');axs[0].set_ylabel('Episode reward');axs[0].legend(loc='lower right')
axs[1].plot(steps,means,'o-',color=COLORS['drl_ppo'],ms=4,label='Validation: four scenarios, seed 999')
axs[1].scatter([bs],[means[best]],s=200,marker='*',color='#d64d45',zorder=5)
axs[1].annotate(f'Best model: {bs:,} steps\nMean reward: {means[best]:.6f}',(bs,means[best]),
                xytext=(-75,-67),textcoords='offset points',arrowprops={'arrowstyle':'->'},fontsize=10)
axs[1].set_title('B. Independent validation selection');axs[1].set_ylabel('Mean episode reward')
axs[1].legend(loc='lower right')
for ax in axs:learning_axis(ax)
fig.suptitle('V2 seed 100: training and validation are distinct selection signals',fontsize=15)
save(fig,0)
fig,axs=plt.subplots(3,3,figsize=(17,12),layout='constrained')
diag=['train/explained_variance','train/value_loss','train/policy_gradient_loss',
      'train/loss','train/entropy_loss','train/approx_kl',
      'train/clip_fraction','train/learning_rate','time/fps']
for ax,t in zip(axs.flat,diag):
 x,y=xy(t);ax.plot(x,y,lw=1,color=COLORS['drl_ppo']);learning_axis(ax)
 ax.set_title(t)
 if t=='train/approx_kl':
  ax.axhline(.02,ls='--',color='#d64d45',lw=1,label='target_kl = 0.02');ax.legend()
 if t=='train/value_loss':
  ev=near(t,218000)
  ax.annotate(f'Local spike: {ev.step:,}\n{ev.value:.3f} (not global max)',
      (ev.step,ev.value),xytext=(32,50),textcoords='offset points',
      arrowprops={'arrowstyle':'->'},fontsize=9)
 if t=='time/fps':ax.set_ylabel('RL decisions / wall second')
 if t=='train/learning_rate':ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
fig.suptitle('V2 seed 100: logged PPO diagnostics (unmodified scalar values)',fontsize=16)
save(fig,1)
action_columns={'requested_action','executed_action','override_reason','phase_id','green_elapsed'}
available=set(RAW['drl_ppo','low',101][0])
assert not (action_columns & available),'Behavior columns now exist: implement measured panels before proceeding'
fig,axs=plt.subplots(1,3,figsize=(17,5.4),layout='constrained')
texts=[
('A. Decision and override matrix',
 'NOT ESTIMABLE FROM ARCHIVED DATA\n\nRequested and executed actions,\nand override reasons were not saved.\n\nCounts and percentages cannot\nbe reconstructed from traffic metrics.'),
('B. Executed KEEP / SWITCH by scenario',
 'NOT ESTIMABLE FROM ARCHIVED DATA\n\nThe four-scenario action distribution\nrequires executed_action events.\n\nNo zero counts or synthetic\npercentages are substituted.'),
('C. Green duration at phase change',
 'NOT ESTIMABLE FROM ARCHIVED DATA\n\nNeither green_elapsed nor phase_id\nis present in archived metrics.csv.\n\nThe consecutive-phase fallback\nis therefore also unavailable.')]
for ax,(title,body) in zip(axs,texts):
 ax.set_title(title,pad=15);ax.set_xticks([]);ax.set_yticks([])
 ax.set_facecolor('#f4f6f8')
 ax.text(.5,.53,body,ha='center',va='center',transform=ax.transAxes,fontsize=11,linespacing=1.55)
 for spine in ax.spines.values():spine.set_color('#cad0d6')
fig.suptitle('Behavior audit: the runtime info exists, but the evaluator did not persist it',fontsize=16)
save(fig,2)
fig,axs=plt.subplots(5,4,figsize=(22,19),layout='constrained')
for j,s in enumerate(SC):
 for i,k in enumerate(MT):
  ax=axs[i,j]
  for m in MS[:3]:
   data=np.array([[float(r[k]) for r in RAW[m,s,seed]] for seed in (101,102,103)])
   if k=='arrived_count':data=np.cumsum(data,axis=1)
   ax.plot(np.arange(5,3601,5),data.mean(axis=0),lw=1.05,color=COLORS[m],label=names[m])
  ax.set_xlim(0,3600);ax.set_xticks([0,900,1800,2700,3600]);ax.grid(alpha=.2)
  if i==0:ax.set_title(s.title(),fontsize=15)
  if j==0:ax.set_ylabel('Cumulative arrivals' if k=='arrived_count' else LABEL[k])
  if i==4:ax.set_xlabel('Simulation time (s)')
fig.legend([plt.Line2D([],[],color=COLORS[m],lw=2) for m in MS[:3]],
           [names[m] for m in MS[:3]],loc='outside lower center',ncol=3,fontsize=13)
fig.suptitle('Post-step traffic trajectories: mean of held-out seeds 101, 102, 103\n'
             'Samples start at 5 s; arrivals are cumulative, other metrics are snapshots',fontsize=18)
save(fig,3)
fig,axs=plt.subplots(3,2,figsize=(15,12),layout='constrained')
for j,s in enumerate(('high','imbalance')):
 for i,k in enumerate(('waiting_time','queue_length','average_speed')):
  ax=axs[i,j];x=np.arange(3);width=.19
  for z,m in enumerate(MS):
   ax.bar(x+(z-1.5)*width,[episodes[m,s,seed][k] for seed in (101,102,103)],
          width,color=COLORS[m],label=names[m])
  ax.set_xticks(x,['Seed 101','Seed 102','Seed 103']);ax.set_ylabel(LABEL[k]);ax.grid(axis='y',alpha=.2)
  if i==0:ax.set_title(s.title(),fontsize=15)
fig.legend([plt.Rectangle((0,0),1,1,color=COLORS[m]) for m in MS],
           [names[m] for m in MS],loc='outside lower center',ncol=4,fontsize=12)
fig.suptitle('Individual held-out seeds: episode-level results, no seed pooling',fontsize=16)
save(fig,4)
fig,axs=plt.subplots(5,2,figsize=(16,18),layout='constrained')
for i,k in enumerate(MT):
 x=np.arange(4)
 for z,m in enumerate(MS[2:]):
  ax=axs[i,0]
  ax.bar(x+(z-.5)*.32,[avg(m,s,k) for s in SC],.32,
         yerr=[std(m,s,k) for s in SC],capsize=4,color=COLORS[m],label=names[m])
  axs[i,1].bar(x+(z-.5)*.32,[100*std(m,s,k)/abs(avg(m,s,k)) for s in SC],
                .32,color=COLORS[m],label=names[m])
 axs[i,0].set_ylabel(LABEL[k]);axs[i,1].set_ylabel('CV (%)')
 for ax in axs[i]:ax.set_xticks(x,[s.title() for s in SC]);ax.grid(axis='y',alpha=.2)
axs[0,0].set_title('Episode mean ± sample standard deviation (ddof=1)')
axs[0,1].set_title('Coefficient of variation = 100 × Std / |Mean|')
axs[0,0].legend()
fig.suptitle('Selected versus final model: variability across three held-out seeds',fontsize=16)
save(fig,5)
fig,axs=plt.subplots(2,2,figsize=(15,11),layout='constrained')
progress_names=['107 / 500k','107 / 800k','710 / 600k','100 / best']
for ax,s in zip(axs.flat,SC):
 vals=[float(old[107]['drl_ppo',s]['waiting_time']),float(old[710]['drl_ppo',s]['waiting_time']),
       avg('drl_ppo',s,'waiting_time')]
 ax.bar([1,2,3],vals,color=['#b3b8bd','#9562a6',COLORS['drl_ppo']],width=.62)
 ax.errorbar([3],[vals[-1]],yerr=[std('drl_ppo',s,'waiting_time')],fmt='none',color='black',capsize=5)
 ceiling=max(vals)*1.25
 ax.set_ylim(0,ceiling);ax.set_xlim(-.6,3.6)
 ax.set_xticks(range(4),progress_names);ax.set_ylabel('Mean waiting (s)')
 ax.set_title(s.title(),fontsize=14);ax.grid(axis='y',alpha=.2)
 ax.text(0,ceiling*.14,'No evaluation\navailable',ha='center',color='#666',fontsize=10)
 for x,b in zip((1,2),vals[:2]):
  delta=100*(b-vals[-1])/b
  ax.text(x,b+ceiling*.03,f'{b:.2f}\nV2 reduction: {delta:.2f}%',ha='center',fontsize=9)
 ax.text(3,vals[-1]+std('drl_ppo',s,'waiting_time')+ceiling*.03,f'{vals[-1]:.2f}',ha='center',fontsize=10)
fig.suptitle('Historical PPO waiting: V1 single runs versus V2 three-seed mean\n'
             'Descriptive comparison; timing, traffic seeds and sampling changed',fontsize=15)
save(fig,6)


# Both language editions share the same verified numerical tables.
historical_tb={}
for seed,folder in ((107,'ppo_overnight'),(710,'ppo_seed710')):
 paths=list(Path('runs',folder).rglob('events.out.tfevents.*'))
 assert len(paths)==1
 before[paths[0]]=hashlib.sha256(paths[0].read_bytes()).hexdigest()
 accumulator=EventAccumulator(str(paths[0]),size_guidance={'scalars':0})
 accumulator.Reload()
 historical_tb[seed]={t:accumulator.Scalars(t) for t in
                     ('train/explained_variance','train/value_loss','train/approx_kl','train/entropy_loss')}
logs=Path('results/seed100/subprocess.log').read_text(encoding='utf-8',errors='replace')
assert 'junction collision' in logs and 'emergency braking' in logs
EN=[];VI=[];gold=[]
VI_CELLS={
 'Observation':'Quan sát',
 '6D aggregate raw state':'Trạng thái gộp 6D chưa chuẩn hóa',
 '12D NS/EW directional state; float32, clipped [0,1]':'Trạng thái định hướng NS/EW 12D; float32, cắt [0,1]',
 'Reward':'Hàm thưởng',
 'Adaptive min / max green':'Xanh tối thiểu / tối đa của bộ điều khiển thích nghi',
 '30 / 75 s for both PPO and Rule-Based':'30 / 75 s cho cả PPO và Rule-Based',
 '15 / 75 s for both PPO and Rule-Based':'15 / 75 s cho cả PPO và Rule-Based',
 'Yellow / all-red':'Vàng / toàn đỏ',
 '3 / 3 s effective; all-red YAML threshold was 0':'Thực tế 3 / 3 s; ngưỡng toàn đỏ YAML cũ bằng 0',
 '3 / 3 s configured and effective':'3 / 3 s trong cấu hình và khi thực thi',
 'Simulation / decision / horizon':'Bước mô phỏng / quyết định / chân trời',
 '0.1 / 5 / 3600 s; 720 decisions per episode':'0.1 / 5 / 3600 s; 720 quyết định mỗi episode',
 'Actor / critic hidden layers':'Lớp ẩn actor / critic',
 '[64,64] each; Tanh':'Mỗi nhánh [64,64]; Tanh',
 '[128,128] each; Tanh':'Mỗi nhánh [128,128]; Tanh',
 'Rollout / batch / epochs':'Rollout / minibatch / số epoch',
 'Learning rate':'Tốc độ học',
 'Fixed 0.0003':'Cố định 0.0003',
 'Linear 0.0003 to 0.00001':'Giảm tuyến tính 0.0003 đến 0.00001',
 'Gamma / GAE / clip':'Gamma / GAE / hệ số clip',
 'Entropy / value / max gradient':'Hệ số entropy / value / gradient tối đa',
 'KL / normalized advantages':'KL / chuẩn hóa advantage',
 'No target KL; enabled advantages':'Không đặt ngưỡng KL; có chuẩn hóa advantage',
 'target_kl=0.02; enabled advantages':'target_kl=0.02; có chuẩn hóa advantage',
 'Scenario sampling':'Lấy mẫu kịch bản',
 'Independent random episode draws':'Chọn ngẫu nhiên độc lập từng episode',
 'Shuffled balanced four-episode cycles':'Chu kỳ bốn episode cân bằng, được xáo trộn',
 'Train / validation / test seeds':'Seed train / validation / test',
 'Policy 107/710; traffic evaluation seed remapped':'Policy 107/710; seed lưu lượng đánh giá bị sinh lại',
 'Policy 100; train 1000..999999; validation 999; test 101,102,103':'Policy 100; train 1000..999999; validation 999; test 101,102,103',
 'Checkpoint selection':'Chọn checkpoint',
 'Final; periodic saves without independent ranking':'Dùng bản cuối; lưu định kỳ nhưng chưa xếp hạng độc lập',
 'Four-scenario validation every 28800 steps; best and final tested':'Validation bốn kịch bản mỗi 28800 bước; kiểm thử best và final',
 'Arrivals':'Số xe hoàn thành hành trình',
 'Intermediate substeps omitted by RB/PPO; PPO averaged cumulative snapshots':'RB/PPO bỏ sót substep trung gian; PPO lấy trung bình snapshot tích lũy',
 'All 0.1 s arrivals accumulated; interval counts summed per episode':'Cộng đủ arrivals mỗi 0.1 s; cộng các khoảng trong toàn episode',
 'Speed / sampling':'Tốc độ / lấy mẫu',
 'FT whole network; adaptive incoming; sampling mismatch':'FT đo toàn mạng; bộ thích nghi đo làn vào; lệch thời điểm lấy mẫu',
 'Vehicle-weighted eight incoming lanes; post-step 5..3600 s':'Tám làn vào có trọng số số xe; sau bước tại 5..3600 s',
 'W_NS / 1500; missing lane waiting contributes 0':'W_NS / 1500; waiting làn bị thiếu đóng góp 0',
 'W_EW / 1500; missing lane waiting contributes 0':'W_EW / 1500; waiting làn bị thiếu đóng góp 0',
 'sum(n_i v_i)/(13.9 sum(n_i)); empty axis = 1':'sum(n_i v_i)/(13.9 sum(n_i)); trục trống = 1',
 '1 when phase_id is 0 or 1; otherwise 0':'1 nếu phase_id thuộc 0,1; trường hợp khác 0',
 '1 when phase_id is 4 or 5; otherwise 0':'1 nếu phase_id thuộc 4,5; trường hợp khác 0',
 '1 if outside transition and green_elapsed >= 15 s; otherwise 0':'1 nếu ngoài pha chuyển và green_elapsed >= 15 s; trường hợp khác 0',
 'disabled':'Tắt',
 '0.02 / enabled':'0.02 / bật',
 'disabled / -1':'Tắt / -1',
 'Default implementation; no custom kwargs':'Bộ đệm mặc định; không có kwargs tùy biến',
 'checkpoint / validation period':'Chu kỳ checkpoint / validation',
 '28800 decision steps; four deterministic validation episodes':'28800 bước quyết định; bốn episode validation tất định',
 'requested / actual total_timesteps':'total_timesteps yêu cầu / thực tế',
 '100 episodes':'100 episode',
 'rollout buffer':'Bộ đệm rollout',
 'Not evaluated':'Chưa có đánh giá',
 'Fixed-Time':'Fixed-Time',
 '12 episodes':'12 episode',
 'GPU training + validation':'Huấn luyện GPU và validation',
 'All stages and overhead':'Tất cả giai đoạn và chi phí phụ',
 'time/fps first / mean / last':'time/fps đầu / trung bình / cuối',
 'Cumulative decision-step throughput':'Thông lượng bước quyết định tích lũy',
 'Best evaluation wall ms / decision':'Đánh giá best: ms thực / quyết định',
 'Final evaluation wall ms / decision':'Đánh giá final: ms thực / quyết định',
 'Includes SUMO, TraCI, reset and startup; 8640 decisions':'Gồm SUMO, TraCI, reset và khởi động; 8640 quyết định',
 'Pure policy-inference latency':'Độ trễ suy luận policy thuần',
 'Not instrumented':'Chưa có phép đo',
 'No per-predict CUDA-synchronized timer in archived evaluator':'Evaluator đã lưu chưa đo riêng predict có đồng bộ CUDA',
 'Decision interval':'Khoảng quyết định',
 '5 s simulated':'5 s mô phỏng',
 'Not a measured real-world latency guarantee':'Chưa phải bảo đảm độ trễ thực địa đã đo',
}
def add(en='',vi=None):
 for dest,value in ((EN,en),(VI,en if vi is None else vi)):
  dest.extend(str(value).strip('\n').split('\n') if value else [''])
 add_blank = bool(en)
 if add_blank:
  EN.append('');VI.append('')
def table(headers,rows,vi_headers=None):
 rows=[list(map(str,row)) for row in rows]
 assert all(len(row)==len(headers) for row in rows)
 for dest,hh in ((EN,headers),(VI,vi_headers or headers)):
  dest.append('| '+' | '.join(hh)+' |')
  dest.append('| '+' | '.join('---' for _ in hh)+' |')
  for row in rows:
   rendered=[VI_CELLS.get(cell,cell) for cell in row] if dest is VI else row
   line='| '+' | '.join(rendered)+' |'
   assert line.count('|')==len(hh)+1
   gold.append((dest is VI,line));dest.append(line)
  dest.append('')
def image_at(index,en,vi):
 link='../seed100/plots/detailed_analysis/'+PLOTS[index]
 add('!['+en+']('+link+')','!['+vi+']('+link+')')
def ms(m,s,k):return f(avg(m,s,k))+' ± '+f(std(m,s,k))
def winning(s,k):
 vals=[avg(m,s,k) for m in MS]
 optimum=max(vals) if k in ('average_speed','arrived_count') else min(vals)
 return ', '.join(names[m] for m,v in zip(MS,vals) if math.isclose(v,optimum,rel_tol=1e-10,abs_tol=1e-10))
add('# DRL V2 Seed 100: Comprehensive Technical Report',
    '# DRL V2 Seed 100: Báo cáo kỹ thuật tổng hợp chuyên sâu')
add('Prepared 24 November 2026. Retrospective analysis of existing source, TensorBoard, Monitor, NPZ and CSV artifacts. No SUMO simulation, training or model evaluation was executed for this analysis.',
    'Ngày lập: 24/11/2026. Phân tích hồi cứu từ mã nguồn, TensorBoard, Monitor, NPZ và CSV có sẵn. Không chạy mô phỏng SUMO, huấn luyện hoặc đánh giá mô hình mới trong quá trình lập báo cáo.')
add('## 1. Model Development and Iterative Evolution: V1 to V2',
    '## 1. Quá trình phát triển và tiến hóa mô hình: V1 đến V2')
add('### 1.1 Experimental motivation and evidence boundaries',
    '### 1.1 Động cơ nâng cấp và giới hạn bằng chứng')
h710=100*(float(old[710]['drl_ppo','high']['waiting_time'])/float(old[710]['rule_based','high']['waiting_time'])-1)
i710=100*(float(old[710]['drl_ppo','imbalance']['waiting_time'])/float(old[710]['rule_based','imbalance']['waiting_time'])-1)
h107=100*(1-float(old[107]['drl_ppo','high']['waiting_time'])/float(old[107]['rule_based','high']['waiting_time']))
add(f'V1 used six aggregate raw observations, reward -(Q + 0.1W), 30 s minimum green and final-checkpoint evaluation without independent validation selection. Seed 710 waiting exceeded its recorded Rule-Based reference by {h710:.6f}% on High and {i710:.6f}% on Imbalance. Seed 107 was different: its High waiting was {h107:.6f}% lower than its historical Rule-Based reference. Both V1 runs struggled on Imbalance; the claim that both failed on High is unsupported.',
    f'V1 sử dụng sáu đặc trưng quan sát gộp chưa chuẩn hóa, reward -(Q + 0.1W), thời gian xanh tối thiểu 30 s và đánh giá checkpoint cuối, chưa chọn mô hình qua validation độc lập. Waiting của seed 710 cao hơn Rule-Based lịch sử {h710:.6f}% ở High và {i710:.6f}% ở Imbalance. Seed 107 khác biệt: waiting ở High thấp hơn Rule-Based lịch sử {h107:.6f}%. Cả hai lần chạy V1 đều yếu ở Imbalance; nhận định cả hai đều thua ở High không được dữ liệu ủng hộ.')
add('A 500k seed-107 checkpoint exists, but no checkpoint-specific evaluation table was found. A claimed 28.7% deterioration from 500k to 800k cannot be verified and is not reported as a measured finding. Likewise, unmatched traffic seeds are demonstrated for V1, whereas actual overlap of training and test traffic seeds is not demonstrated.',
    'Có checkpoint seed 107 tại 500k, nhưng không tìm thấy bảng đánh giá tương ứng. Không thể kiểm chứng nhận định hiệu năng giảm 28,7% từ 500k lên 800k, nên không trình bày như kết quả đo được. V1 đã được xác nhận lệch seed lưu lượng giữa các phương pháp; chưa có bằng chứng trực tiếp về trùng seed giữa tập huấn luyện và kiểm thử.')
add('### 1.2 Root-cause audit and architectural changes',
    '### 1.2 Kiểm toán nguyên nhân và thay đổi kiến trúc')
add('Four engineering weaknesses motivated V2: unscaled value targets and raw features; loss of NS/EW information; lack of independently ranked checkpoints; and inconsistent seed, arrival, speed and sampling definitions. These are plausible mechanisms and measured protocol defects, not separate causal effects established by ablation.',
    'Bốn điểm yếu kỹ thuật thúc đẩy V2: value target và đặc trưng thô có thang đo lớn; mất thông tin NS/EW; chưa xếp hạng checkpoint bằng validation độc lập; và bất đồng nhất seed, arrivals, phạm vi speed, thời điểm lấy mẫu. Đây là cơ chế có cơ sở và lỗi giao thức đã xác nhận, chưa phải tác động nhân quả riêng lẻ được chứng minh qua ablation.')
table(['Component','V1: seeds 107 / 710','V2: seed 100'],[
['Observation','6D aggregate raw state','12D NS/EW directional state; float32, clipped [0,1]'],
['Reward','-(Q + 0.1W)','clip(-(Q_NS+Q_EW+0.05(W_NS+W_EW)+0.02(Q_NS-Q_EW)^2)/100,-10,0)'],
['Adaptive min / max green','30 / 75 s for both PPO and Rule-Based','15 / 75 s for both PPO and Rule-Based'],
['Yellow / all-red','3 / 3 s effective; all-red YAML threshold was 0','3 / 3 s configured and effective'],
['Simulation / decision / horizon','0.1 / 5 / 3600 s','0.1 / 5 / 3600 s; 720 decisions per episode'],
['Actor / critic hidden layers','[64,64] each; Tanh','[128,128] each; Tanh'],
['Rollout / batch / epochs','2048 / 64 / 10','2880 / 96 / 5'],
['Learning rate','Fixed 0.0003','Linear 0.0003 to 0.00001'],
['Gamma / GAE / clip','0.99 / 0.95 / 0.2','0.99 / 0.95 / 0.2'],
['Entropy / value / max gradient','0 / 0.5 / 0.5','0.01 / 0.5 / 0.5'],
['KL / normalized advantages','No target KL; enabled advantages','target_kl=0.02; enabled advantages'],
['Scenario sampling','Independent random episode draws','Shuffled balanced four-episode cycles'],
['Train / validation / test seeds','Policy 107/710; traffic evaluation seed remapped','Policy 100; train 1000..999999; validation 999; test 101,102,103'],
['Checkpoint selection','Final; periodic saves without independent ranking','Four-scenario validation every 28800 steps; best and final tested'],
['Arrivals','Intermediate substeps omitted by RB/PPO; PPO averaged cumulative snapshots','All 0.1 s arrivals accumulated; interval counts summed per episode'],
['Speed / sampling','FT whole network; adaptive incoming; sampling mismatch','Vehicle-weighted eight incoming lanes; post-step 5..3600 s'],
],['Thành phần','V1: seed 107 / 710','V2: seed 100'])
add('The archived audit says both V1 adaptive methods used min_green=30 s. Thus 30 versus 15 s is an inter-version timing change, not a demonstrated V1 Rule-Based/PPO mismatch. All-red must be interpreted using the actual SUMO phase program rather than the former YAML value alone.',
    'Audit lịch sử ghi nhận cả hai phương pháp thích nghi V1 cùng dùng min_green=30 s. Vì vậy, 30 so với 15 s là thay đổi giữa hai phiên bản, không phải bằng chứng Rule-Based/PPO V1 dùng ngưỡng khác nhau. Thời gian toàn đỏ cần đối chiếu chương trình pha SUMO thực tế, không chỉ giá trị YAML cũ.')
table(['Run','Mean explained variance','Last explained variance','Mean value loss','Last value loss'],[
[str(seed),f(statistics.fmean(e.value for e in historical_tb[seed]['train/explained_variance'])),
 f(historical_tb[seed]['train/explained_variance'][-1].value),
 f(statistics.fmean(e.value for e in historical_tb[seed]['train/value_loss'])),
 f(historical_tb[seed]['train/value_loss'][-1].value)] for seed in (107,710)]+[
['100',f(statistics.fmean(e.value for e in ts['train/explained_variance'])),
 f(ts['train/explained_variance'][-1].value),
 f(statistics.fmean(e.value for e in ts['train/value_loss'])),f(ts['train/value_loss'][-1].value)]],
 ['Lần chạy','Explained variance trung bình','Explained variance cuối','Value loss trung bình','Value loss cuối'])
add('V2 ends at explained_variance=0.970996, versus low V1 average explained variance. Mean-to-final is not an identical endpoint comparison, so the table provides both. The reward-scale change makes absolute value-loss ratios unsuitable as a direct measure of algorithmic improvement.',
    'V2 kết thúc ở explained_variance=0.970996, trong khi explained variance trung bình của V1 thấp. So sánh trung bình với giá trị cuối không tương đương cùng mốc; bảng cung cấp cả hai. Do reward đã đổi thang đo, không dùng tỷ số value loss tuyệt đối để định lượng mức tiến bộ thuật toán.')
add('The selected V2 checkpoint improves all five Imbalance means against contemporary Rule-Based. Validation selection limits exposure to late drift on that scenario; it does not eliminate over-adaptation or guarantee the strongest checkpoint on every test scenario.',
    'Checkpoint V2 được chọn cải thiện cả năm chỉ số trung bình Imbalance so với Rule-Based cùng giao thức. Chọn bằng validation giúp hạn chế ảnh hưởng dao động cuối kỳ ở kịch bản này; không loại bỏ hoàn toàn over-adaptation và không bảo đảm checkpoint tốt nhất trên mọi kịch bản kiểm thử.')

add('## 2. Methodology, Technology and Data Preprocessing',
    '## 2. Phương pháp luận, công nghệ và tiền xử lý dữ liệu')
add('### 2.1 Execution stack and signal constraints',
    '### 2.1 Nền tảng thực thi và ràng buộc tín hiệu')
add(f'The experiment uses SUMO 1.28.0 and TraCI, a Gymnasium wrapper, Stable-Baselines3 PPO and PyTorch CUDA. Recorded GPU: NVIDIA {meta["gpu"]}. Package versions below come from the saved run manifest, not assumptions about the current installation.',
    f'Thực nghiệm sử dụng SUMO 1.28.0 và TraCI, môi trường Gymnasium, PPO của Stable-Baselines3 và PyTorch CUDA. GPU được ghi nhận: NVIDIA {meta["gpu"]}. Phiên bản thư viện dưới đây lấy từ manifest của lần chạy, không suy ra từ môi trường hiện tại.')
table(['Package','Recorded version'],list(runconfig['versions'].items()),['Thư viện','Phiên bản đã ghi nhận'])
table(['Configuration','Value'],[(k,str(cfg[k])) for k in ('simulation_step','decision_interval','min_green','max_green','yellow_time','all_red_time','gui')],
      ['Cấu hình','Giá trị'])
add('Discrete(2) actions encode KEEP=0 and SWITCH=1. SignalController blocks premature switches and enforces maximum green at 0.1 s boundaries; transitions execute yellow and all-red. Requests during transitions are NOOP, and startup-phase requests can be held. Green elapsed is simulation seconds. The phase mask, startup stage and transition guards matter beyond the binary action. Fixed-Time keeps 51 s green per axis in a 114 s cycle, inside the same 15–75 s envelope; its 5 s cadence is measurement, not adaptive control.',
    'Không gian Discrete(2) mã hóa KEEP=0 và SWITCH=1. SignalController chặn chuyển sớm, ép chuyển khi đạt xanh tối đa tại biên 0,1 s; quá trình chuyển giữ pha vàng và toàn đỏ. Yêu cầu trong pha chuyển là NOOP; yêu cầu tại pha khởi động có thể bị giữ lại. Green elapsed tính bằng giây mô phỏng. Mặt nạ tín hiệu, pha khởi động và khóa chuyển tiếp bổ sung ràng buộc cho action nhị phân. Fixed-Time giữ xanh 51 s mỗi trục trong chu kỳ 114 s, thuộc khoảng 15–75 s; nhịp 5 s chỉ để đo lường.')
add('### 2.2 Directional 12D representation',
    '### 2.2 Biểu diễn 12D theo hướng')
add('NS lanes: N_in_0, N_in_1, S_in_0, S_in_1. EW lanes: E_in_0, E_in_1, W_in_0, W_in_1. Queue, vehicle count and current waiting are summed per axis. Weighted speed uses lane vehicle counts. Every output is clipped to [0,1] and stored as float32.',
    'Làn NS: N_in_0, N_in_1, S_in_0, S_in_1. Làn EW: E_in_0, E_in_1, W_in_0, W_in_1. Hàng chờ, số xe và current waiting cộng theo trục. Tốc độ dùng trọng số số xe trên làn. Toàn bộ đầu ra được cắt về [0,1] và lưu float32.')
table(['Index','Feature','Preprocessing before final clipping'],[
[0,'queue_ns_norm','Q_NS / 60'],[1,'queue_ew_norm','Q_EW / 60'],
[2,'veh_ns_norm','N_NS / 80'],[3,'veh_ew_norm','N_EW / 80'],
[4,'wait_ns_norm','W_NS / 1500; missing lane waiting contributes 0'],
[5,'wait_ew_norm','W_EW / 1500; missing lane waiting contributes 0'],
[6,'speed_ns_norm','sum(n_i v_i)/(13.9 sum(n_i)); empty axis = 1'],
[7,'speed_ew_norm','sum(n_i v_i)/(13.9 sum(n_i)); empty axis = 1'],
[8,'is_ns_green','1 when phase_id is 0 or 1; otherwise 0'],
[9,'is_ew_green','1 when phase_id is 4 or 5; otherwise 0'],
[10,'green_elapsed_norm','green_elapsed / 75'],
[11,'can_switch','1 if outside transition and green_elapsed >= 15 s; otherwise 0']],
['Vị trí','Đặc trưng','Tiền xử lý trước phép cắt cuối'])
add('At queue>60, vehicles>80 or waiting>1500 s per axis the corresponding feature saturates; larger overloads become indistinguishable in that dimension. Empty-axis observation speed is 1, while an entirely empty incoming region contributes a reported traffic speed of 0. Feature normalization and traffic-metric definitions serve different purposes.',
    'Khi queue>60, vehicles>80 hoặc waiting>1500 s mỗi trục, đặc trưng tương ứng bão hòa; mức quá tải lớn hơn không còn phân biệt được ở chiều đó. Tốc độ quan sát của trục trống bằng 1, nhưng chỉ số tốc độ giao thông của vùng incoming hoàn toàn trống bằng 0. Chuẩn hóa đặc trưng và định nghĩa metric có vai trò khác nhau.')
add('### 2.3 Reward shaping and PPO settings','### 2.3 Thiết kế hàm thưởng và cấu hình PPO')
add(r'$$r_t=\operatorname{clip}\left(-\frac{Q_{NS}+Q_{EW}+0.05(W_{NS}+W_{EW})+0.02(Q_{NS}-Q_{EW})^2}{100},-10,0\right).$$')
add('The queue term penalizes halted vehicles; weighted current waiting emphasizes prolonged stops; the squared NS/EW difference discourages unequal queues. Division by 100 reduces target scale and clipping bounds severe penalties. Equal queues are not always demand-proportional service, so the balance term is a design trade-off. Reward is a post-interval snapshot, with no explicit collision, arrival or switching term.',
    'Thành phần queue phạt số xe dừng; current waiting có trọng số nhấn mạnh các lần dừng kéo dài; chênh lệch NS/EW bình phương phạt lệch hàng chờ. Chia 100 giảm thang đo value target, cắt ngưỡng giới hạn hình phạt cực đoan. Hàng chờ bằng nhau không luôn đồng nghĩa phân bổ xanh theo nhu cầu; hệ số cân bằng là một đánh đổi thiết kế. Reward lấy snapshot cuối khoảng, chưa có thành phần phạt va chạm, thưởng arrivals hoặc phạt chuyển pha riêng.')
table(['PPO setting','Actual implementation'],[
['policy / device / seed','MlpPolicy / cuda / 100'],
['learning_rate','1e-5 + (3e-4 - 1e-5) * clip(progress_remaining,0,1)'],
['n_steps / batch_size / n_epochs','2880 / 96 / 5'],
['gamma / gae_lambda','0.99 / 0.95'],
['clip_range / value clipping','0.2 / disabled'],
['ent_coef / vf_coef / max_grad_norm','0.01 / 0.5 / 0.5'],
['target_kl / normalize_advantage','0.02 / enabled'],
['net_arch / activation','pi=[128,128], vf=[128,128] / Tanh'],
['use_sde / sde_sample_freq','disabled / -1'],
['stats_window_size','100 episodes'],
['rollout buffer','Default implementation; no custom kwargs'],
['checkpoint / validation period','28800 decision steps; four deterministic validation episodes'],
['requested / actual total_timesteps',str(meta['requested_timesteps'])+' / '+str(meta['actual_timesteps'])]],
['Tham số PPO','Cấu hình thực tế'])
add('### 2.4 Seed isolation and measurement protocol','### 2.4 Tách biệt seed và giao thức đo lường')
add('Training uses NumPy default_rng(100), shuffling each four-scenario cycle and drawing traffic seeds in [1000,999999]. The 836 completed episodes confirm 209 occurrences of every scenario and four-scenario coverage in each rollout. Training traffic seeds can repeat within that range, but cannot equal 101/102/103/999. Validation reuses 999 on each scenario, and selects by maximum four-scenario mean reward; held-out 101–103 never select the checkpoint.',
    'Huấn luyện dùng NumPy default_rng(100), xáo trộn từng chu kỳ bốn kịch bản và sinh seed lưu lượng trong [1000,999999]. Có 836 episode hoàn tất, xác nhận mỗi kịch bản xuất hiện 209 lần và mỗi rollout phủ đủ bốn kịch bản. Seed huấn luyện có thể lặp trong dải đó nhưng không thể trùng 101/102/103/999. Validation dùng lại 999 cho từng kịch bản, chọn theo reward trung bình bốn kịch bản lớn nhất; seed kiểm thử 101–103 không tham gia chọn checkpoint.')
add('Every evaluated episode contains 720 post-step samples at t=5,10,...,3600 s. Queue, summed lane waiting, vehicle-weighted speed on the same eight incoming lanes, and network occupancy are time means. Arrivals accumulate all 50 substeps per decision and are summed over the episode. Waiting is not mean per-vehicle trip delay; network occupancy is a mean, not terminal backlog. Matching traffic seeds and route inputs aligns the stochastic setup, while controller-dependent insertion and trajectories can still differ.',
    'Mỗi episode đánh giá có 720 mẫu sau bước tại t=5,10,...,3600 s. Queue, tổng waiting theo làn, tốc độ có trọng số trên cùng tám làn vào và số xe toàn mạng được lấy trung bình theo thời gian. Arrivals cộng đủ 50 substep mỗi quyết định và cộng tiếp toàn episode. Waiting không phải delay hành trình trung bình mỗi xe; occupancy là trung bình, không phải xe tồn đọng cuối kỳ. Cùng seed và đầu vào route đồng bộ thiết lập ngẫu nhiên, nhưng controller vẫn có thể làm khác thời điểm chèn xe và quỹ đạo.')


add('## 3. Training Process and Convergence Diagnostics: Seed 100',
    '## 3. Quá trình huấn luyện và phân tích hội tụ: Seed 100')
add(f'The requested {meta["requested_timesteps"]:,} steps expanded to {meta["actual_timesteps"]:,} complete rollout steps: {meta["expected_rollouts"]} rollouts and {len(tr)} completed 720-decision episodes. A rollout is exactly one balanced four-scenario cycle. Preflight separately completed 5760 steps; those trials are excluded from production results.',
    f'Ngân sách yêu cầu {meta["requested_timesteps"]:,} bước được thu trọn rollout thành {meta["actual_timesteps"]:,} bước: {meta["expected_rollouts"]} rollout và {len(tr)} episode hoàn tất, mỗi episode 720 quyết định. Một rollout tương ứng đúng một chu kỳ cân bằng bốn kịch bản. Preflight riêng hoàn tất 5760 bước; kết quả thử đó không được gộp vào thực nghiệm chính.')
add('### 3.1 Learning trajectory and validation selection','### 3.1 Diễn biến học và chọn mô hình qua validation')
image_at(0,'Training reward and independent validation reward','Reward huấn luyện và reward validation độc lập')
add(f'The first logged training return is {f(ts["rollout/ep_rew_mean"][0].value)} at step {ts["rollout/ep_rew_mean"][0].step:,}, and the last is {f(ts["rollout/ep_rew_mean"][-1].value)} at {ts["rollout/ep_rew_mean"][-1].step:,}. Raw rollout return is already SB3’s moving episode mean; the additional EMA (alpha=0.10) is display-only and is never used for checkpoint selection.',
    f'Return huấn luyện đầu tiên được log là {f(ts["rollout/ep_rew_mean"][0].value)} tại bước {ts["rollout/ep_rew_mean"][0].step:,}; giá trị cuối là {f(ts["rollout/ep_rew_mean"][-1].value)} tại {ts["rollout/ep_rew_mean"][-1].step:,}. Rollout return gốc đã là trung bình episode theo cửa sổ của SB3; EMA bổ sung (alpha=0,10) chỉ phục vụ hiển thị, không dùng chọn checkpoint.')
table(['Validation step','Four-scenario mean return','Scenario population Std'],[
 [str(int(s)),f(m),f(np.std(r,ddof=0))] for s,m,r in zip(steps,means,rewards)],
 ['Bước validation','Return trung bình bốn kịch bản','Std tổng thể giữa bốn kịch bản'])
add(f'Best validation is {f(means[best])} at **{bs:,} steps**, independently confirmed from best_model.zip. The last scheduled validation occurs at {int(steps[-1]):,}, with return {f(means[-1])}; there is no validation checkpoint at 601,920. Validation Std above is between four different scenarios, not held-out-seed uncertainty. The final model is separately tested on 101–103.',
    f'Validation tốt nhất đạt {f(means[best])} tại **{bs:,} bước**, được đối chiếu độc lập với best_model.zip. Validation theo lịch cuối diễn ra tại {int(steps[-1]):,}, return {f(means[-1])}; không có lượt validation tại 601.920 bước. Std ở bảng trên phản ánh khác biệt giữa bốn kịch bản, không phải bất định giữa seed kiểm thử. Mô hình cuối được kiểm thử riêng trên 101–103.')
table(['Requested milestone','Nearest rollout step','Training reward','Explained variance','Value loss','Approx KL','Clip fraction'],[
 [str(s),str(near('rollout/ep_rew_mean',s).step),
  *[f(near(t,s).value) for t in ('rollout/ep_rew_mean','train/explained_variance','train/value_loss','train/approx_kl','train/clip_fraction')]]
 for s in (150000,218000,316800,601920)],
 ['Mốc yêu cầu','Bước rollout gần nhất','Reward huấn luyện','Explained variance','Value loss','Approx KL','Clip fraction'])
add('The series improves rapidly toward 150k, then spends most later training near a plateau. At a requested milestone each column uses that tag’s nearest available event; early train/* and rollout/* logging can differ by one rollout. Higher rolling training reward does not necessarily imply higher validation reward because demand composition and evaluation traffic differ.',
    'Chuỗi cải thiện nhanh trước khoảng 150k, sau đó phần lớn giai đoạn cuối dao động quanh vùng ổn định. Với mỗi mốc yêu cầu, từng cột dùng event gần nhất của tag tương ứng; thời điểm log train/* và rollout/* đầu kỳ có thể lệch một rollout. Reward trung bình huấn luyện cao hơn không tất yếu cho reward validation cao hơn vì thành phần lưu lượng và episode khác nhau.')
add('### 3.2 Critic quality and PPO update diagnostics','### 3.2 Chất lượng Critic và độ ổn định cập nhật PPO')
image_at(1,'Nine TensorBoard loss and update diagnostics','Chín chỉ số loss và chẩn đoán cập nhật từ TensorBoard')
table(['Scalar','First step:value','Min step:value','Max step:value','Mean','Last step:value'],[
 [t,f'{a[0].step}:{a[0].value:.9g}',
  f'{min(a,key=lambda e:e.value).step}:{min(a,key=lambda e:e.value).value:.9g}',
  f'{max(a,key=lambda e:e.value).step}:{max(a,key=lambda e:e.value).value:.9g}',
  f'{statistics.fmean(e.value for e in a):.9g}',f'{a[-1].step}:{a[-1].value:.9g}'] for t,a in ts.items()],
 ['Scalar','Đầu step:value','Min step:value','Max step:value','Trung bình','Cuối step:value'])
spike=near('train/value_loss',218000)
add(f'The local value-loss spike is at {spike.step:,}: loss={f(spike.value)}, explained_variance={f(near("train/explained_variance",spike.step).value)}, approx_kl={f(near("train/approx_kl",spike.step).value)} and clip_fraction={f(near("train/clip_fraction",spike.step).value)}. The initial value loss {f(ts["train/value_loss"][0].value)} is the global maximum, so the 218k event is a local spike. Return composition and bootstrapping are plausible contributors; logs do not establish its exact cause or traffic scenario.',
    f'Gai value loss cục bộ xuất hiện tại {spike.step:,}: loss={f(spike.value)}, explained_variance={f(near("train/explained_variance",spike.step).value)}, approx_kl={f(near("train/approx_kl",spike.step).value)} và clip_fraction={f(near("train/clip_fraction",spike.step).value)}. Value loss đầu kỳ {f(ts["train/value_loss"][0].value)} mới là cực đại toàn chuỗi, nên sự kiện 218k là gai cục bộ. Thành phần return và bootstrapping có thể góp phần; log không xác định được nguyên nhân hoặc kịch bản cụ thể.')
add(f'Explained variance recovers and ends at {f(ts["train/explained_variance"][-1].value)}. Logged approximate KL stays below the 0.02 reference; late clip fractions approach zero. These show small measured updates, not proof of optimal control. Entropy loss is negative entropy: movement toward zero indicates a more concentrated policy. The schedule specifies 0.0003 to 0.00001, while the final logged learning rate is {ts["train/learning_rate"][-1].value:.12f}; rollout logging can expose the preceding optimization value.',
    f'Explained variance phục hồi và kết thúc ở {f(ts["train/explained_variance"][-1].value)}. Approximate KL đã log nằm dưới ngưỡng tham chiếu 0,02; clip fraction cuối tiến gần 0. Điều này cho thấy cập nhật đo được nhỏ, không chứng minh điều khiển tối ưu. Entropy loss là âm entropy: tiến gần 0 nghĩa là policy tập trung hơn. Schedule đặt từ 0,0003 đến 0,00001, nhưng learning rate cuối được log là {ts["train/learning_rate"][-1].value:.12f}; cơ chế log theo rollout có thể phản ánh giá trị của lượt tối ưu trước.')
fps=ts['time/fps'];first8=next(e.step for e in fps if e.value==8)
add(f'FPS starts at {fps[0].value:g}, first reaches 8 at step {first8:,}, and ends at {fps[-1].value:g}. Thus “8 to 10 FPS” omits the initial 6-FPS record. FPS here means cumulative RL decision interactions per wall-clock second, not 0.1 s SUMO substeps or rendered frames. The 720-step rollout/eval episode lengths agree with archived Monitor data.',
    f'FPS bắt đầu ở {fps[0].value:g}, lần đầu đạt 8 tại bước {first8:,} và kết thúc ở {fps[-1].value:g}. Vì vậy, mô tả “8 lên 10 FPS” bỏ qua bản ghi đầu 6 FPS. FPS ở đây là tốc độ tương tác quyết định RL tích lũy theo giây thực, không phải substep SUMO 0,1 s hoặc khung hình. Độ dài episode rollout/eval 720 bước khớp Monitor đã lưu.')
add('### 3.3 Decision behavior: observability limitation','### 3.3 Hành vi ra quyết định: giới hạn dữ liệu được lưu')
image_at(2,'Action and green-duration analysis unavailable in archived records',
         'Không đủ dữ liệu lưu trữ để phân tích action và thời lượng xanh')
add('Environment.step returns requested_action, executed_action, override_reason, phase_id, green_elapsed and automatic_events at runtime. However, evaluate.py persists only METRICS plus method/scenario/seed/time. Archived best metrics.csv therefore lacks every behavioral field. Figure 03 explicitly marks all three requested panels as not estimable; it is not a measured heatmap, action histogram or duration distribution. Traffic flow cannot uniquely identify requested actions.',
    'Environment.step trả requested_action, executed_action, override_reason, phase_id, green_elapsed và automatic_events khi chạy. Tuy nhiên, evaluate.py chỉ lưu METRICS cùng method/scenario/seed/time. Do đó metrics.csv của mô hình best thiếu toàn bộ trường hành vi. Hình 03 đánh dấu rõ cả ba khung không thể ước lượng; đây không phải heatmap, histogram action hoặc phân bố thời lượng đã đo. Lưu lượng không xác định duy nhất action AI đã yêu cầu.')
add('Even if only phase IDs had been saved, five-second phase runs would give approximate, censored durations and could miss intermediate yellow/all-red events. Exact future behavior audits should persist pre-decision state and timestamped controller events, including transition NOOP and startup overrides. No new evaluation was run and no historical CSV was modified to fill these gaps.',
    'Ngay cả khi có phase ID, chuỗi pha mỗi 5 giây cũng chỉ cho thời lượng xấp xỉ, có thể bị cắt ở biên và bỏ sót vàng/toàn đỏ trung gian. Audit hành vi chính xác về sau cần lưu state trước quyết định và sự kiện controller có timestamp, gồm NOOP trong chuyển pha và khóa pha khởi động. Không chạy đánh giá mới hoặc sửa CSV lịch sử để lấp phần thiếu này.')

add('## 4. Evaluation Scorecards and Scenario Analysis',
    '## 4. Hệ thống bảng đánh giá và phân tích theo kịch bản')
add('### 4.1 Table 1: multi-seed mean ± sample Std','### 4.1 Bảng 1: trung bình đa seed ± độ lệch chuẩn mẫu')
add('Each cell aggregates three episode-level results with ddof=1. Queue, waiting and mean network occupancy are lower-is-better; speed and episode arrivals are higher-is-better. Winners are descriptive means, with exact ties retained. Units: queue/network vehicles, waiting seconds, speed m/s, arrivals vehicles per episode.',
    'Mỗi ô tổng hợp ba kết quả theo episode với ddof=1. Queue, waiting và occupancy trung bình càng thấp càng tốt; tốc độ và tổng arrivals càng cao càng tốt. Phương pháp tốt nhất dựa trên trung bình mô tả, giữ các trường hợp bằng nhau. Đơn vị: queue/network là xe, waiting là giây, tốc độ m/s, arrivals là xe/episode.')
table(['Scenario','Metric','Fixed-Time','Rule-Based','PPO best','PPO final','Best mean'],[
 [s,k,*[ms(m,s,k) for m in MS],winning(s,k)] for s in SC for k in MT],
 ['Kịch bản','Chỉ số','Fixed-Time','Rule-Based','PPO best','PPO final','Trung bình tốt nhất'])
add('![Existing baseline comparison](../seed100/plots/seed100_baseline_comparison.png)',
    '![Biểu đồ so sánh baseline có sẵn](../seed100/plots/seed100_baseline_comparison.png)')
add('### 4.2 Table 2: improvement percentages','### 4.2 Bảng 2: tỷ lệ cải thiện')
add('For queue/wait/network: improvement=100(B-P)/B. For speed/arrivals: improvement=100(P-B)/B. P is PPO best and B the named baseline. Positive means favorable; negative means worse. Percentages are calculated from unrounded means.',
    'Với queue/wait/network: cải thiện=100(B-P)/B. Với tốc độ/arrivals: cải thiện=100(P-B)/B. P là PPO best, B là baseline tương ứng. Dấu dương nghĩa là tốt hơn; dấu âm là kém hơn. Tỷ lệ tính từ trung bình chưa làm tròn.')
table(['Scenario','Metric','PPO best vs Fixed-Time (%)','PPO best vs Rule-Based (%)'],[
 [s,k,f(imp(avg('drl_ppo',s,k),avg('fixed_time',s,k),k)),
      f(imp(avg('drl_ppo',s,k),avg('rule_based',s,k),k))] for s in SC for k in MT],
 ['Kịch bản','Chỉ số','PPO best so với Fixed-Time (%)','PPO best so với Rule-Based (%)'])
add('### 4.3 Table 3: every held-out seed and episode','### 4.3 Bảng 3: từng seed kiểm thử và từng episode')
for seed in (101,102,103):
 add(f'#### Seed {seed}')
 table(['Scenario','Method','Queue','Waiting (s)','Speed (m/s)','Arrivals','Network vehicles'],[
  [s,names[m],*[f(episodes[m,s,seed][k]) for k in MT]] for s in SC for m in MS],
  ['Kịch bản','Phương pháp','Hàng chờ','Waiting (s)','Tốc độ (m/s)','Arrivals','Xe toàn mạng'])
image_at(4,'Separate held-out seeds: High and Imbalance','Từng seed kiểm thử riêng biệt: High và Imbalance')
add('Difficulty must be conditioned on traffic scenario and controller. The waiting-based rankings below directly test the proposed 102 > 101 > 103 ordering instead of assuming it universally. They describe realized congestion, not independently measured offered demand.',
    'Độ khó cần gắn với kịch bản và controller. Thứ tự theo waiting dưới đây trực tiếp kiểm tra giả thuyết 102 > 101 > 103, không mặc định đúng với mọi trường hợp. Đây là xếp hạng ùn tắc thực tế, không phải phép đo độc lập về nhu cầu đầu vào.')
table(['Scenario','Method','Descending waiting: seed:value'],[
 [s,names[m],'; '.join(f'{seed}:{f(episodes[m,s,seed]["waiting_time"])}'
  for seed in sorted((101,102,103),key=lambda seed:episodes[m,s,seed]['waiting_time'],reverse=True))]
 for s in SC for m in MS],
 ['Kịch bản','Phương pháp','Waiting giảm dần: seed:giá trị'])
add('### 4.4 Table 4: runtime, throughput and inference evidence',
    '### 4.4 Bảng 4: thời gian chạy, thông lượng và bằng chứng độ trễ suy luận')
ft=sum(v for k,v in tim.items() if k.startswith('fixed_time_'))
rb=sum(v for k,v in tim.items() if k.startswith('rule_based_'))
table(['Stage','Wall seconds','Wall hours','Scope'],[
 ['Fixed-Time',f(ft),f(ft/3600),'12 episodes'],
 ['Rule-Based',f(rb),f(rb/3600),'12 episodes'],
 *[[k,f(tim[k]),f(tim[k]/3600),'GPU training + validation' if k=='drl_training' else '12 episodes']
   for k in ('drl_training','drl_evaluation_best','drl_evaluation_final')],
 ['total_pipeline',f(tim['total_pipeline']),f(tim['total_pipeline']/3600),'All stages and overhead']],
 ['Giai đoạn','Thời gian thực (s)','Thời gian thực (giờ)','Phạm vi'])
table(['Timing indicator','Value','Interpretation'],[
 ['time/fps first / mean / last',f'{fps[0].value:g} / {statistics.fmean(e.value for e in fps):.6f} / {fps[-1].value:g}','Cumulative decision-step throughput'],
 ['Best evaluation wall ms / decision',f(tim['drl_evaluation_best']/8640*1000),'Includes SUMO, TraCI, reset and startup; 8640 decisions'],
 ['Final evaluation wall ms / decision',f(tim['drl_evaluation_final']/8640*1000),'Includes SUMO, TraCI, reset and startup; 8640 decisions'],
 ['Pure policy-inference latency','Not instrumented','No per-predict CUDA-synchronized timer in archived evaluator'],
 ['Decision interval','5 s simulated','Not a measured real-world latency guarantee']],
 ['Chỉ số thời gian','Giá trị','Diễn giải'])
add('The wall-time-per-decision proxy is not neural-network inference time. Startup, SUMO stepping, TraCI communication and file output are included. It cannot establish a hard real-time deployment deadline; deployment needs isolated synchronized prediction timing and tail-latency measurement.',
    'Thời gian thực chia cho số quyết định không phải thời gian suy luận mạng. Chỉ số này bao gồm khởi động, stepping SUMO, trao đổi TraCI và ghi file. Không thể dùng để bảo đảm hạn chót thời gian thực; triển khai cần đo predict riêng có đồng bộ và đo độ trễ đuôi phân bố.')
add('### 4.5 Temporal dynamics, stability and scenario mechanisms',
    '### 4.5 Diễn biến theo thời gian, độ ổn định và cơ chế theo kịch bản')
image_at(3,'Five traffic metrics over 3600 seconds, averaged across three seeds',
         'Năm chỉ số giao thông trong 3600 giây, trung bình ba seed')
add('Figure 04 averages aligned post-step samples at each timestamp; no t=0 observation is invented. Its arrivals row is the cumulative sum of interval arrivals, averaged across seeds. The other rows retain snapshot meanings. Cumulative arrivals are a plotting transformation, not a change to the verified episode metric.',
    'Hình 04 lấy trung bình mẫu sau bước đã căn cùng timestamp; không tạo mẫu giả tại t=0. Hàng arrivals là tổng tích lũy arrivals theo khoảng, sau đó trung bình giữa seed. Các hàng khác giữ ý nghĩa snapshot. Tích lũy arrivals chỉ là phép biến đổi để vẽ, không thay định nghĩa metric episode đã kiểm chứng.')
image_at(5,'Selected versus final: means, sample standard deviations and coefficients of variation',
         'Best so với final: trung bình, độ lệch chuẩn mẫu và hệ số biến thiên')
table(['Scenario','Metric','Best mean ± Std','Final mean ± Std','Best CV (%)','Final CV (%)'],[
 [s,k,ms('drl_ppo',s,k),ms('drl_ppo_final',s,k),
  f(100*std('drl_ppo',s,k)/abs(avg('drl_ppo',s,k))),
  f(100*std('drl_ppo_final',s,k)/abs(avg('drl_ppo_final',s,k)))]
 for s in SC for k in MT],
 ['Kịch bản','Chỉ số','Best TB ± Std','Final TB ± Std','CV best (%)','CV final (%)'])
add('Low and Medium produce identical best/final episode summaries. Imbalance selected waiting is 350.303009 ± 23.177922 s, versus final 387.294722 ± 131.940310 s: validation selection helps both mean and dispersion there. High reverses that comparison: final 386.548426 ± 29.624104 s is better than selected 395.157037 ± 44.472238 s. Independent selection is useful, but the single-seed validation objective does not rank all test outcomes optimally.',
    'Low và Medium cho bảng episode best/final giống nhau. Waiting Imbalance của best là 350.303009 ± 23.177922 s, so với final 387.294722 ± 131.940310 s: chọn bằng validation cải thiện cả trung bình và độ phân tán tại đây. High có chiều ngược lại: final 386.548426 ± 29.624104 s tốt hơn best 395.157037 ± 44.472238 s. Chọn độc lập có giá trị, nhưng mục tiêu validation một seed không xếp hạng tối ưu mọi kết quả kiểm thử.')
for s in SC:
 q=imp(avg('drl_ppo',s,'queue_length'),avg('rule_based',s,'queue_length'),'queue_length')
 w=imp(avg('drl_ppo',s,'waiting_time'),avg('rule_based',s,'waiting_time'),'waiting_time')
 add(f'**{s.title()}:** PPO best versus Rule-Based improvement: queue {q:.6f}%; waiting {w:.6f}%.',
     f'**{s.title()}:** mức cải thiện PPO best so với Rule-Based: queue {q:.6f}%; waiting {w:.6f}%.')
add('On Low/Medium, a responsive queue heuristic already performs strongly, leaving limited headroom; PPO is slightly worse on queue, waiting and speed means, but slightly higher on arrivals. On High, Rule-Based beats PPO best on all five means. “Comparable” denotes proximity of observed values, not an equivalence test.',
    'Ở Low/Medium, heuristic phản ứng theo hàng chờ vốn đã mạnh nên dư địa cải thiện nhỏ; PPO có trung bình queue, waiting và speed hơi kém hơn, nhưng arrivals nhỉnh hơn. Ở High, Rule-Based tốt hơn PPO best trên cả năm trung bình. “Xấp xỉ” chỉ mô tả độ gần của giá trị quan sát, không phải kết luận kiểm định tương đương.')
add('Imbalance is the main success: directional features reveal which axis is underserved, and the squared queue difference rewards balancing that aggregate V1 features could not represent directly. This mechanism is consistent with all five favorable Imbalance means, but is not causally isolated. The small arrival gain and three paired test seeds do not establish statistical significance or superiority on every seed. Action allocation itself remains unobserved in archived CSVs.',
    'Imbalance là thành công chính: đặc trưng định hướng cho thấy trục nào chưa được phục vụ đủ; chênh lệch hàng chờ bình phương khuyến khích cân bằng mà đặc trưng gộp V1 không biểu diễn trực tiếp. Cơ chế này phù hợp với cả năm trung bình Imbalance tốt hơn, nhưng chưa được tách biệt nhân quả. Mức tăng arrivals nhỏ và ba seed kiểm thử ghép cặp không đủ khẳng định ý nghĩa thống kê hoặc thắng ở mọi seed. Phân bổ action thực tế vẫn chưa quan sát được từ CSV đã lưu.')


add('## 5. Cross-Version Comparison: V2 Seed 100 versus V1 Seeds 107 and 710',
    '## 5. So sánh liên phiên bản: V2 Seed 100 với V1 Seed 107 và 710')
add('The table retains historical values as recorded. V1 columns represent single scenario runs, whereas V2 columns are three-seed mean ± sample Std. V1-107 “800k” actually saved 800,768 steps and V1-710 “600k” saved 600,064 steps. The 500k column is explicitly unavailable, not a zero or inferred result.',
    'Bảng giữ nguyên giá trị lịch sử đã ghi. Các cột V1 là từng lượt chạy kịch bản riêng; V2 là trung bình ba seed ± độ lệch chuẩn mẫu. V1-107 “800k” thực lưu 800.768 bước và V1-710 “600k” thực lưu 600.064 bước. Cột 500k ghi rõ chưa có kết quả, không phải 0 hoặc số suy diễn.')
table(['Scenario','Metric','V1 107 / 500k','V1 107 / 800k','V1 710 / 600k','V2 100 / best','V2 100 / final'],[
 [s,k,'Not evaluated',f(old[107]['drl_ppo',s][k]),f(old[710]['drl_ppo',s][k]),
  ms('drl_ppo',s,k),ms('drl_ppo_final',s,k)] for s in SC for k in MT],
 ['Kịch bản','Chỉ số','V1 107 / 500k','V1 107 / 800k','V1 710 / 600k','V2 100 / best','V2 100 / final'])
image_at(6,'Historical V1-to-V2 waiting progression with explicit missing 500k evaluations',
         'Tiến trình waiting V1 đến V2, đánh dấu rõ thiếu đánh giá 500k')
table(['Scenario','V2 best waiting reduction vs 107/800k (%)','V2 best waiting reduction vs 710/600k (%)'],[
 [s,f(100*(1-avg('drl_ppo',s,'waiting_time')/float(old[107]['drl_ppo',s]['waiting_time']))),
    f(100*(1-avg('drl_ppo',s,'waiting_time')/float(old[710]['drl_ppo',s]['waiting_time'])))] for s in SC],
 ['Kịch bản','Giảm waiting V2 best so với 107/800k (%)','Giảm waiting V2 best so với 710/600k (%)'])
add('These percentages describe recorded waiting changes, not a controlled estimate of architectural benefit. Minimum green changed from 30 to 15 s; scenario exposures, seeds, rollout structure and sampling changed together. V1 arrivals have incompatible accumulation/aggregation, and V1 Fixed-Time speed was network-wide. Do not interpret V1-to-V2 arrival ratios as throughput improvements.',
    'Các tỷ lệ mô tả thay đổi waiting đã ghi, không phải ước lượng có kiểm soát về lợi ích kiến trúc. Xanh tối thiểu đổi từ 30 xuống 15 s; mức tiếp xúc kịch bản, seed, cấu trúc rollout và lấy mẫu cùng thay đổi. Arrivals V1 khác cách cộng và tổng hợp; tốc độ Fixed-Time V1 đo toàn mạng. Không diễn giải tỷ số arrivals V1–V2 như cải thiện thông lượng.')
add('The three decisive engineering changes are: directional normalized inputs that retain NS/EW demand; scaled/shaped rewards plus balanced rollouts and controlled PPO updates; and corrected multi-seed evaluation with independent checkpoint selection. Their combined association with better historical PPO High/Imbalance waiting is supported. Separate causal contributions require controlled ablations under identical timing and traffic seeds.',
    'Ba bước tiến kỹ thuật chủ đạo là: đầu vào định hướng được chuẩn hóa, giữ nhu cầu NS/EW; reward có scaling/shaping kết hợp rollout cân bằng và cập nhật PPO được kiểm soát; đánh giá đa seed đã sửa metric cùng chọn checkpoint độc lập. Dữ liệu ủng hộ mối liên hệ giữa gói thay đổi này với waiting High/Imbalance thấp hơn PPO lịch sử. Muốn xác định đóng góp nhân quả riêng cần ablation với cùng thời gian đèn và seed lưu lượng.')
add('The supported reversal against a contemporary baseline occurs on Imbalance. V2 does not reverse Rule-Based superiority on High, and V1 seed 107 already had favorable recorded High waiting. Neither universal V1 failure nor universal V2 dominance follows from the evidence.',
    'Sự đảo chiều được dữ liệu ủng hộ so với baseline cùng giao thức diễn ra ở Imbalance. V2 chưa đảo ngược ưu thế Rule-Based tại High; seed 107 V1 từng có waiting High tốt hơn theo bảng lịch sử. Không thể kết luận V1 thất bại toàn diện hoặc V2 vượt trội toàn diện.')

add('## 6. Limitations, Conclusions and Future Work',
    '## 6. Giới hạn thực nghiệm, kết luận và hướng phát triển')
add('### 6.1 Limitations','### 6.1 Giới hạn')
add('**Safety:** the existing combined subprocess log contains junction-collision and emergency-braking warnings. These are not a PPO-specific collision rate and cannot establish relative safety without stage-attributed event exposure. Signal timing guards do not demonstrate collision-free behavior, legal compliance or field readiness. The reward includes no explicit collision penalty.',
    '**An toàn:** log subprocess tổng hợp hiện có cảnh báo va chạm trong nút và phanh khẩn cấp. Đây không phải tỷ lệ va chạm riêng của PPO; chưa thể so sánh an toàn khi thiếu phân loại sự kiện và mức tiếp xúc theo giai đoạn. Khóa thời gian tín hiệu không chứng minh vận hành không va chạm, tuân thủ pháp lý hoặc sẵn sàng thực địa. Reward chưa có phạt va chạm riêng.')
add('**Representation and horizon:** queue, vehicles and waiting saturate above 60, 80 and 1500 per axis; reward saturates at -10. Saturation incidence cannot be reconstructed from aggregate traffic CSVs. A 3600 s horizon leaves incomplete trips, terminal vehicles and possibly delayed insertions. No clearance period or trip-completion distribution is evaluated here.',
    '**Biểu diễn và chân trời:** queue, số xe và waiting bão hòa trên 60, 80 và 1500 mỗi trục; reward bão hòa tại -10. CSV giao thông gộp không cho phép xác định tỷ lệ bão hòa đặc trưng theo hướng. Chân trời 3600 s có thể để lại hành trình chưa hoàn thành, xe cuối kỳ và xe chưa chèn được. Báo cáo chưa đánh giá giai đoạn giải tỏa sau nhu cầu hoặc phân bố hoàn thành hành trình.')
add('**Statistical scope:** one V2 training seed and three held-out traffic seeds provide descriptive paired evidence, not broad robustness or statistical significance. Test-seed Std is not training-seed uncertainty. Repeated selection on validation seed 999 can itself adapt to that validation traffic. Historical V1 data are confounded by timing and metric changes.',
    '**Phạm vi thống kê:** một seed huấn luyện V2 và ba seed lưu lượng kiểm thử cung cấp bằng chứng ghép cặp mang tính mô tả, chưa chứng minh độ vững tổng quát hoặc ý nghĩa thống kê. Std giữa seed kiểm thử không phải bất định giữa seed huấn luyện. Chọn lặp trên validation seed 999 có thể thích nghi với chính lưu lượng validation. Dữ liệu V1 bị nhiễu bởi thay đổi thời gian đèn và metric.')
add('**Missing instrumentation:** no archived action/override/phase history, no independently evaluated seed-107 500k table and no pure inference timer exist in the inspected sources. Figure 03 and the 500k progression slot document missing evidence. The 218880 critic spike has no proven causal diagnosis.',
    '**Thiếu instrumentation:** các nguồn đã kiểm tra không có lịch sử action/override/phase được lưu, không có bảng đánh giá độc lập checkpoint 500k seed 107 và không có bộ đo suy luận thuần. Hình 03 và vị trí 500k ở biểu đồ tiến trình thể hiện phần bằng chứng còn thiếu. Nguyên nhân gai Critic tại 218880 chưa được chứng minh.')
add('### 6.2 Conclusion and next experiments','### 6.2 Kết luận và thực nghiệm tiếp theo')
add('V2 improves state observability, optimization scale and experimental auditability. Its selected checkpoint improves all five Imbalance mean metrics versus Rule-Based and reduces Imbalance variability relative to final. Rule-Based remains stronger on the High mean scorecard, and final is stronger than selected on High. Retain validation selection while recognizing its scenario trade-off.',
    'V2 cải thiện khả năng quan sát trạng thái, thang đo tối ưu và khả năng kiểm toán thực nghiệm. Checkpoint được chọn cải thiện cả năm trung bình Imbalance so với Rule-Based và giảm biến động Imbalance so với final. Rule-Based vẫn mạnh hơn trong bảng trung bình High; final tốt hơn best tại High. Nên giữ chọn bằng validation, đồng thời nhận diện đánh đổi giữa các kịch bản.')
add('Next: train independent seeds 200 and 300 with unchanged held-out rules; expand validation traffic seeds; run ablations for directionality, scaling, imbalance penalty and min-green timing; record controller events and synchronized policy latency; report paired uncertainty, trip metrics and clearance backlog; add safety constraints/penalties and stage-attributed collision rates; then extend to coordinated multiple intersections.',
    'Tiếp theo: huấn luyện độc lập seed 200 và 300 với giao thức held-out giữ nguyên; mở rộng seed validation; ablation định hướng, scaling, phạt lệch tải và thời gian xanh tối thiểu; lưu sự kiện controller và đo suy luận có đồng bộ; báo cáo bất định ghép cặp, chỉ số hành trình và tồn đọng sau giải tỏa; bổ sung ràng buộc/phạt an toàn và tỷ lệ va chạm theo giai đoạn; sau đó mở rộng phối hợp nhiều giao lộ.')
add('### 6.3 Provenance and verification','### 6.3 Nguồn dữ liệu và kiểm chứng')
add('Primary artifacts: [training metadata](../../models/seed100/training_metadata.json), [pipeline timings](../seed100/pipeline_timings.json), [preflight](../seed100/preflight_check.json), [V2 summary](../seed100/summary_final.csv), [original V2 report](drl_seed100_v2_report.md), [V1 summary](v1_baseline_drl_summary_107_710.md).',
    'Nguồn chính: [metadata huấn luyện](../../models/seed100/training_metadata.json), [thời gian pipeline](../seed100/pipeline_timings.json), [preflight](../seed100/preflight_check.json), [bảng tổng hợp V2](../seed100/summary_final.csv), [báo cáo V2 gốc](drl_seed100_v2_report.md), [tổng kết V1](v1_baseline_drl_summary_107_710.md).')
add('Source read directly: '+', '.join(source_names)+'. Historical reports: '+', '.join(history_names)+'. Detailed evaluation data: evaluation/seed100/{best,final}/{episodes,metrics}.csv and all baseline CSVs for 101/102/103. Training/validation Monitor, reset JSONL, validation NPZ and all 13 requested TensorBoard scalars were read. V1 TensorBoard files and per-seed summary CSVs were also checked.',
    'Mã nguồn đọc trực tiếp: '+', '.join(source_names)+'. Báo cáo lịch sử: '+', '.join(history_names)+'. Dữ liệu đánh giá: evaluation/seed100/{best,final}/{episodes,metrics}.csv và toàn bộ CSV baseline seed 101/102/103. Đã đọc Monitor train/validation, JSONL reset, NPZ validation và đủ 13 scalar TensorBoard yêu cầu. Đã đối chiếu event TensorBoard V1 và CSV tổng hợp theo seed.')
add(f'All 48 evaluated episodes were independently reconstructed from 720 samples each; {checks} numerical equalities against episode/summary CSVs were checked. Mean/Std, percentage improvement and CV use unrounded source values; tables display six decimals except the 9-significant-digit scalar summary. All 80 validation episodes, saved checkpoint step identities, 836 training episodes and balanced seed cycles were verified. Seven PNGs are checked for positive size and 300-DPI metadata. Both reports are checked for valid Markdown table widths, six main sections, eight image links and absence of missing numeric values. Existing source/data/report hashes are checked before and after generation.',
    f'Đã tái tính độc lập 48 episode đánh giá, mỗi episode 720 mẫu; kiểm tra {checks} đẳng thức số với CSV episode/summary. Trung bình/Std, tỷ lệ cải thiện và CV dùng giá trị nguồn chưa làm tròn; bảng hiển thị sáu chữ số thập phân, riêng scalar hiển thị chín chữ số có nghĩa. Đã đối chiếu 80 episode validation, bước lưu checkpoint, 836 episode huấn luyện và chu kỳ seed cân bằng. Bảy PNG được kiểm tra dung lượng dương và metadata 300 DPI. Hai báo cáo được kiểm tra số cột bảng Markdown, sáu phần chính, tám liên kết ảnh và không có giá trị số bị thiếu. Hash mã nguồn/dữ liệu/báo cáo cũ được kiểm tra trước và sau khi tạo.')

readme="""# Seed 100 detailed analysis figures

Generated by scripts/export_seed100_plots.py from archived data only. PNGs use 300 DPI and English scientific figure labels; both report editions embed the same figures.

| File | Contents and interpretation |
| --- | --- |
| 01_learning_curves_reward_and_val.png | Training rollout mean, display-only EMA alpha=0.10, and seed-999 validation; best step verified against NPZ and model archive. |
| 02_tensorboard_losses_and_diagnostics.png | Nine unmodified TensorBoard diagnostics; 218880 local value-loss spike and 0.02 KL reference. First FPS is 6, then reaches 8 and ends at 10. |
| 03_action_decision_and_override_matrix.png | Explicit three-panel missing-data audit. Requested/executed actions, override, phase_id and green_elapsed were not persisted. No heatmap counts, action proportions or durations are fabricated. |
| 04_timeseries_3600s_all_scenarios.png | Five metrics by four scenarios; mean at each 5-second post-step timestamp across seeds 101/102/103. Arrivals are cumulative; other metrics remain snapshots. |
| 05_per_seed_breakdown_101_102_103.png | Individual seed waiting, queue and speed for High/Imbalance and all four methods. |
| 06_ppo_best_vs_final_stability.png | All five metrics: mean plus sample Std (ddof=1) and CV=100*Std/abs(mean) across test seeds. |
| 07_v1_to_v2_progression_comparison.png | Historical waiting values and V2 three-seed mean; percentage reduction versus each measured V1 model. No 500k evaluation was found, and its slot is not plotted as zero. |

V1-to-V2 differences are descriptive, with timing/seed/sampling confounds. The 28.7% 500k-to-800k degradation claim cannot be verified. Pure policy-inference latency was not instrumented. Figure 03 documents a limitation rather than supplying unobserved behavior data.

No existing source, model, evaluation CSV, report or comparison image is overwritten. The exporter deliberately refuses to run if either new report or the detailed-analysis output directory already exists.
"""
# Verify Python code is parsable without creating a bytecode cache.
ast.parse(Path(__file__).read_text(encoding='utf-8'))
reports=[(out,'\n'.join(EN)+'\n'),(vi_out,'\n'.join(VI)+'\n')]
def validate_markdown(report):
 inside=False;ncols=0;count=0
 assert not re.search(r'\b(?:NaN|None|[+-]?inf)\b',report,re.I)
 for line in report.splitlines():
  if line.startswith('|'):
   cells=line.strip().strip('|').split('|')
   if not inside:
    ncols=len(cells);inside=True;count+=1
   assert len(cells)==ncols,line
  else:inside=False
 assert len(re.findall(r'^## \d\.',report,re.M))==6
 links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',report)
 assert len(links)==8 and len(set(links))==8
 for link in links:assert (out.parent/link).resolve().is_file(),link
 return count
images=[]
for filename in PLOTS:
 path=plotdir/filename
 assert path.is_file() and path.stat().st_size>0
 with Image.open(path) as im:
  im.verify()
 with Image.open(path) as im:
  dpi=im.info['dpi'];assert all(abs(d-300)<1 for d in dpi)
  images.append(dict(file=filename,bytes=path.stat().st_size,pixels=list(im.size),dpi=list(dpi)))
assert len(list(plotdir.glob('*.png')))==7
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in before.items())
tablecounts=[]
for path,report in reports:
 tablecounts.append(validate_markdown(report))
 assert all(row in report for is_vi,row in set(gold) if is_vi == (path == vi_out))
 with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(report)
 assert path.read_text(encoding='utf-8')==report
with (plotdir/'README.md').open('x',encoding='utf-8',newline='\n') as stream:stream.write(readme)
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in before.items())
quality=dict(status='passed',reports=[str(p) for p,_ in reports],
             report_lines=[len(r.splitlines()) for _,r in reports],markdown_tables=tablecounts,
             csv_numeric_checks=checks,evaluation_episodes=len(episodes),samples_per_episode=720,
             tensorboard_scalar_tags=tags,validation_episodes=len(vr),training_episodes=len(tr),
             best_model_step=bs,existing_files_sha256_unchanged=len(before),
             figures=images,limitations=['Action/override/phase history not persisted',
             'Seed107 500k evaluation unavailable','Pure inference latency not instrumented'])
with (plotdir/'quality_checks.json').open('x',encoding='utf-8') as stream:json.dump(quality,stream,indent=2,ensure_ascii=False)
print(json.dumps({k:v for k,v in quality.items() if k!='figures'},ensure_ascii=False,indent=2),flush=True)

