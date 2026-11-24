"""Refresh five seed-100 figures and only the authorized report passages."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import math
import os
import re
import tempfile
import statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PIL import Image
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

ROOT=Path(__file__).resolve().parents[1]
PLOT=ROOT/'results/seed100/plots/detailed_analysis'
AUDIT=ROOT/'evaluation/seed100/action_audit'
SC=('low','medium','high','imbalance')
MS=('fixed_time','rule_based','drl_ppo')
MT=('queue_length','waiting_time','average_speed','arrived_count','vehicles_in_network')
NAMES=dict(zip(MS,('Fixed-Time','Rule-Based','PPO best')))
COLORS={'fixed_time':'#737b85','rule_based':'#e58d2c','drl_ppo':'#157f99'}
LABEL={'queue_length':'Queue (vehicles)','waiting_time':'Waiting (s)','average_speed':'Speed (m/s)',
       'arrived_count':'Cumulative arrivals','vehicles_in_network':'Network vehicles'}
CATEGORIES=('KEEP','SWITCH','blocked_min_green','forced_max_green','transition_noop')
FILENAMES=[
'01_learning_curves_reward_and_val.png',
'02_tensorboard_losses_and_diagnostics.png',
'03_action_decision_and_override_matrix.png',
'04_timeseries_3600s_all_scenarios.png',
'05_per_seed_breakdown_101_102_103.png',
'06_ppo_best_vs_final_stability.png',
'07_v1_to_v2_progression_comparison.png']

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixed_report_regions(text):
    text=re.sub(r'(?ms)^### 3\.3 .*?(?=^## 4\.)','<AUTHORIZED_3_3>\n\n',text,count=1)
    return re.sub(r'(?ms)^### 6\.1 .*?(?=^### 6\.2 )','<AUTHORIZED_6_1>\n\n',text,count=1)

def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def atomic_text(path,text):
    fd,temporary=tempfile.mkstemp(prefix='._refresh_',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:
            stream.write(text)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)

def save(fig,index):
    fd,temporary=tempfile.mkstemp(prefix='._refresh_',suffix='.png',dir=PLOT)
    os.close(fd)
    try:
        fig.savefig(temporary,dpi=300,facecolor='white')
        with Image.open(temporary) as im:
            assert all(abs(x-300)<1 for x in im.info['dpi'])
            im.verify()
        os.replace(temporary,PLOT/FILENAMES[index])
    finally:
        plt.close(fig)
        if os.path.exists(temporary):
            os.remove(temporary)
    print('REFRESHED '+FILENAMES[index],flush=True)

def load_actions():
    proof=json.loads((AUDIT/'reproducibility_check.json').read_text(encoding='utf-8'))
    assert proof['status']=='passed' and proof['completed_episodes']==12
    rows=read(AUDIT/'action_steps.csv')
    eps=read(AUDIT/'action_episodes.csv')
    greens=read(AUDIT/'action_switches.csv')
    reference={(r['scenario'],int(r['seed'])):r for r in read(ROOT/'evaluation/seed100/best/episodes.csv')}
    groups={}
    for row in rows:
        groups.setdefault((row['scenario'],int(row['seed'])),[]).append(row)
    assert set(groups)=={(s,k) for s in SC for k in (101,102,103)}
    assert len(eps)==12 and len(rows)==8640
    equalities=0
    for ep in eps:
        key=ep['scenario'],int(ep['seed'])
        values=groups[key]
        assert len(values)==720
        for i,r in enumerate(values):
            assert float(r['simulation_time'])==5*(i+1)
            assert int(r['requested_action']) in (0,1)
            assert r['outcome'] in CATEGORIES
        for metric in MT:
            reconstructed=(sum(float(r[metric]) for r in values) if metric=='arrived_count'
                           else statistics.fmean(float(r[metric]) for r in values))
            assert reconstructed==float(ep[metric])==float(reference[key][metric]),(key,metric)
            equalities+=1
    assert equalities==60
    matrix=np.zeros((2,len(CATEGORIES)),dtype=np.int64)
    for row in rows:
        matrix[int(row['requested_action']),CATEGORIES.index(row['outcome'])]+=1
    assert matrix.sum()==8640
    assert all(15-1e-7<=float(g['green_elapsed'])<=75+1e-7 for g in greens)
    # Every actual green departure has one recorded controller-boundary event.
    assert len(greens)==sum(r['executed_action']=='SWITCH' for r in rows)
    assert len(greens)==sum(len(json.loads(r['green_switch_events'])) for r in rows)
    return rows,eps,greens,matrix,proof

def plot_actions(rows,greens,matrix):
    fig,axs=plt.subplots(1,3,figsize=(25,7.4),layout='constrained',
                         gridspec_kw={'width_ratios':[1.55,1.05,1.10]})
    totals=matrix.sum(axis=1,keepdims=True)
    assert np.all(totals>0)
    percent=100*matrix/totals
    heat=axs[0].imshow(percent,cmap='Blues',vmin=0,vmax=100,aspect='auto')
    axs[0].set_xticks(range(5),['KEEP','SWITCH','Blocked:\nmin_green 15 s',
                               'Forced:\nmax_green 75 s','Transition\nNOOP'],fontsize=11)
    axs[0].set_yticks([0,1],[f'KEEP = 0\nn={totals[0,0]:,}',f'SWITCH = 1\nn={totals[1,0]:,}'],fontsize=12)
    axs[0].set_ylabel('Policy-requested action',fontsize=13)
    axs[0].set_title('A. Decision and override matrix\nCounts + percentage within requested-action row',fontsize=14,pad=15)
    for i in range(2):
        for j in range(5):
            axs[0].text(j,i,f'{matrix[i,j]:,}\n{percent[i,j]:.2f}%',ha='center',va='center',
                        color='white' if percent[i,j]>55 else '#17212b',fontsize=12)
    colorbar=fig.colorbar(heat,ax=axs[0],fraction=.035,pad=.02)
    colorbar.set_label('Row (%)')
    per_scenario=[]
    for s in SC:
        cohort=[r for r in rows if r['scenario']==s]
        counts=Counter(r['executed_action'] for r in cohort)
        keep,switch,noop=counts['KEEP'],counts['SWITCH'],counts['NOOP']
        assert keep+switch+noop==2160
        per_scenario.append(dict(scenario=s,keep=keep,switch=switch,noop=noop,
                                 denominator=keep+switch,
                                 keep_pct=100*keep/(keep+switch),switch_pct=100*switch/(keep+switch)))
    x=np.arange(4)
    axs[1].bar(x,[r['keep_pct'] for r in per_scenario],color='#157f99',label='Executed KEEP',width=.65)
    axs[1].bar(x,[r['switch_pct'] for r in per_scenario],
               bottom=[r['keep_pct'] for r in per_scenario],color='#d66d52',label='Executed SWITCH',width=.65)
    for i,r in enumerate(per_scenario):
        axs[1].text(i,r['keep_pct']/2,f'{r["keep_pct"]:.1f}%\nn={r["keep"]}',ha='center',va='center',color='white',fontsize=11)
        axs[1].text(i,r['keep_pct']+r['switch_pct']/2,f'{r["switch_pct"]:.1f}%\nn={r["switch"]}',
                    ha='center',va='center',color='white',fontsize=11)
    axs[1].set_xticks(x,[r['scenario'].title()+f'\nNOOP: {r["noop"]}' for r in per_scenario],fontsize=11)
    axs[1].set_ylim(0,112);axs[1].set_ylabel('Executed KEEP / SWITCH (%)',fontsize=13)
    axs[1].set_title('B. Realized actions by scenario\nNOOP excluded from percentage denominator',fontsize=14,pad=15)
    axs[1].legend(loc='upper center',ncol=1,fontsize=10)
    axs[1].grid(axis='y',alpha=.16)
    samples=[[float(r['green_elapsed']) for r in greens if r['scenario']==s] for s in SC]
    boxes=axs[2].boxplot(samples,tick_labels=[s.title()+f'\nn={len(v)}' for s,v in zip(SC,samples)],
                         patch_artist=True,widths=.55,medianprops={'color':'#17324d','linewidth':2},
                         flierprops={'markersize':3,'alpha':.35})
    for box in boxes['boxes']:
        box.set_facecolor('#8bc6d6')
    axs[2].axhline(15,color='#d66d52',ls='--',lw=1.4,label='min_green = 15 s')
    axs[2].axhline(75,color='#5f7182',ls='--',lw=1.4,label='max_green = 75 s')
    axs[2].set_ylim(8,90);axs[2].set_ylabel('Observed green duration at departure (s)',fontsize=13)
    axs[2].set_title('C. Completed green intervals\nExact request/substep transition timestamps',fontsize=14,pad=15)
    axs[2].legend(loc='upper center',fontsize=10);axs[2].grid(axis='y',alpha=.16)
    fig.suptitle('PPO best: measured action audit — 12 deterministic episodes, 8,640 decisions\n'
                 'Exclusive interval outcomes; complete green intervals only, unfinished episode tails excluded',fontsize=17)
    save(fig,2)
    return per_scenario,samples

def make_training_plots(ts,steps,means,best_step):
    def xy(tag):
        return [e.step for e in ts[tag]],[e.value for e in ts[tag]]
    def axis(ax):
        ax.set_xlim(0,601920);ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1000:g}k'))
        ax.set_xlabel('Training decision steps',fontsize=12);ax.tick_params(labelsize=11);ax.grid(alpha=.2)
    fig,axs=plt.subplots(1,2,figsize=(17,5.8),layout='constrained')
    x,y=xy('rollout/ep_rew_mean')
    smoothed=[y[0]]
    for v in y[1:]:
        smoothed.append(.1*v+.9*smoothed[-1])
    axs[0].plot(x,y,color=COLORS['drl_ppo'],alpha=.25,label='Raw SB3 episode moving mean')
    axs[0].plot(x,smoothed,color=COLORS['drl_ppo'],lw=2,label='EMA on logged values (alpha=0.10)')
    axs[0].set_title('A. Training return',fontsize=15);axs[0].set_ylabel('Episode reward',fontsize=13)
    axs[1].plot(steps,means,'o-',color=COLORS['drl_ppo'],ms=4,label='Validation seed 999: four-scenario mean')
    peak=int(np.argmax(means))
    axs[1].scatter([best_step],[means[peak]],marker='*',s=220,color='#d64d45',zorder=6)
    axs[1].annotate(f'Best checkpoint: {best_step:,}\nReward: {means[peak]:.6f}',(best_step,means[peak]),
                    xytext=(25,-85),textcoords='offset points',fontsize=11,
                    arrowprops={'arrowstyle':'->'})
    dip=np.flatnonzero(steps==172800)
    assert len(dip)==1
    dip_value=float(means[dip[0]])
    axs[1].annotate(f'Local dip: 172,800\n{dip_value:.2f}',(172800,dip_value),
                    xytext=(-95,-58),textcoords='offset points',fontsize=11,
                    arrowprops={'arrowstyle':'->'},bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
    axs[1].set_title('B. Independent validation selection',fontsize=15)
    axs[1].set_ylabel('Mean episode reward',fontsize=13)
    for ax in axs:
        axis(ax)
        ax.axvline(best_step,color='#b3473c',ls='--',lw=1.25,alpha=.8,label='Best checkpoint: 316,800')
        ax.legend(loc='lower right',fontsize=11)
    fig.suptitle('V2 seed 100: training and independent validation',fontsize=18)
    save(fig,0)
    diag=('train/explained_variance','train/value_loss','train/policy_gradient_loss',
          'train/loss','train/entropy_loss','train/approx_kl',
          'train/clip_fraction','train/learning_rate','time/fps')
    fig,axs=plt.subplots(3,3,figsize=(18,13),layout='constrained')
    for ax,tag in zip(axs.flat,diag):
        x,y=xy(tag);ax.plot(x,y,color=COLORS['drl_ppo'],lw=1)
        axis(ax);ax.set_title(tag,fontsize=13)
        if tag in ('train/value_loss','train/loss'):
            assert all(v>0 for v in y),'Log axis cannot display non-positive observations'
            ax.set_yscale('log');ax.set_ylabel('Loss (log scale)',fontsize=12)
            ax.grid(which='minor',alpha=.1)
        if tag=='train/value_loss':
            spike=min(ts[tag],key=lambda e:abs(e.step-218880))
            assert spike.step==218880
            ax.annotate(f'218,880: {spike.value:.3f}',(spike.step,spike.value),
                        xytext=(22,-30),textcoords='offset points',fontsize=10,
                        arrowprops={'arrowstyle':'->'})
        if tag=='train/approx_kl':
            ax.axhline(.02,color='#d64d45',ls='--',lw=1,label='target_kl = 0.02');ax.legend()
        if tag=='train/learning_rate':
            ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
        if tag=='time/fps':
            ax.set_ylabel('RL decisions / wall second',fontsize=11)
    fig.suptitle('V2 seed 100: unchanged TensorBoard samples; value and total losses on log axes',fontsize=17)
    save(fig,1)
    return dip_value

def plot_timeseries():
    raw={}
    for m in MS:
        paths=(ROOT/f'evaluation/seed100/baselines/{m}').rglob('metrics_*.csv') if m!='drl_ppo' else [ROOT/'evaluation/seed100/best/metrics.csv']
        for path in paths:
            for r in read(path):
                raw.setdefault((m,r['scenario'],int(r['seed'])),[]).append(r)
    assert len(raw)==36
    fig,axs=plt.subplots(5,4,figsize=(24,20),layout='constrained')
    for j,s in enumerate(SC):
        for i,k in enumerate(MT):
            ax=axs[i,j]
            for m in MS:
                data=[]
                for seed in (101,102,103):
                    values=raw[m,s,seed]
                    assert len(values)==720
                    assert all(float(r['simulation_time'])==5*(z+1) for z,r in enumerate(values))
                    data.append([float(r[k]) for r in values])
                data=np.asarray(data,dtype=float)
                if k=='arrived_count':
                    mean=np.cumsum(data,axis=1).mean(axis=0)
                    ax.plot(np.arange(5,3601,5),mean,color=COLORS[m],lw=1.8)
                else:
                    mean=data.mean(axis=0)
                    ax.plot(np.arange(5,3601,5),mean,color=COLORS[m],alpha=.22,lw=.7)
                    # No padding, extrapolation or partial-window assumption:
                    # first full 12-sample trailing average is at t=60 s.
                    smooth=np.convolve(mean,np.ones(12)/12,mode='valid')
                    ax.plot(np.arange(60,3601,5),smooth,color=COLORS[m],lw=1.8)
            ax.set_xlim(0,3600);ax.set_xticks([0,900,1800,2700,3600])
            ax.tick_params(labelsize=12);ax.grid(alpha=.18)
            if i==0:ax.set_title(s.title(),fontsize=17)
            if j==0:ax.set_ylabel(LABEL[k],fontsize=14)
            if i==4:ax.set_xlabel('Simulation time (s)',fontsize=14)
    fig.legend([plt.Line2D([],[],color=COLORS[m],lw=2) for m in MS],
               [NAMES[m] for m in MS],loc='outside lower center',ncol=3,fontsize=15)
    fig.suptitle('Traffic trajectories: mean across held-out seeds 101, 102, 103\n'
                 'Snapshot rows: faint raw 5 s samples + bold trailing 60 s mean; arrivals: unchanged cumulative totals',
                 fontsize=19)
    save(fig,3)

def plot_progression():
    old={seed:{r['scenario']:float(r['waiting_time']) for r in read(ROOT/f'results/seed{seed}/summary_final.csv')
               if r['method']=='drl_ppo'} for seed in (107,710)}
    summary={r['scenario']:r for r in read(ROOT/'results/seed100/summary_final.csv') if r['method']=='drl_ppo'}
    fig,axs=plt.subplots(2,2,figsize=(16,12),layout='constrained')
    for ax,s in zip(axs.flat,SC):
        values=[old[107][s],old[710][s],float(summary[s]['waiting_time_mean'])]
        sd=float(summary[s]['waiting_time_std'])
        ax.bar(range(3),values,color=['#b3b8bd','#9562a6',COLORS['drl_ppo']],width=.58)
        ax.errorbar([2],[values[-1]],yerr=[sd],fmt='none',color='black',capsize=5)
        # The former 1.25*maximum ceiling is raised by a further 15%.
        ceiling=max(max(values),values[-1]+sd)*1.25*1.15
        ax.set_ylim(0,ceiling);ax.set_xlim(-.65,2.65)
        ax.set_xticks(range(3),['V1 107 / 800k','V1 710 / 600k','V2 100 / best'],fontsize=12)
        ax.set_ylabel('Mean waiting (s)',fontsize=13);ax.tick_params(labelsize=12)
        ax.set_title(s.title(),fontsize=16);ax.grid(axis='y',alpha=.18)
        for x,b in enumerate(values[:2]):
            delta=100*(b-values[-1])/b
            ax.text(x,b+ceiling*.035,f'{b:.2f}\nV2 reduction: {delta:.2f}%',ha='center',fontsize=11)
        ax.text(2,values[-1]+sd+ceiling*.035,f'{values[-1]:.2f}',ha='center',fontsize=12)
    fig.suptitle('Historical PPO waiting: V1 single runs versus V2 three-seed mean\n'
                 '107/500k omitted: no independent evaluation table. Timing, traffic seeds and sampling differ.',
                 fontsize=17)
    save(fig,6)


def markdown_table(headers,rows):
    lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
    for row in rows:
        assert len(row)==len(headers)
        lines.append('| '+' | '.join(map(str,row))+' |')
    return '\n'.join(lines)+'\n'

def update_reports(rows,greens,matrix,scenario_counts,samples):
    original={}
    replacements={}
    figure='../seed100/plots/detailed_analysis/03_action_decision_and_override_matrix.png'
    n=len(rows)
    minimum=min(float(g['green_elapsed']) for g in greens)
    maximum=max(float(g['green_elapsed']) for g in greens)
    counts=Counter(r['outcome'] for r in rows)
    startup=sum(r['request_override_reason']=='startup_phase' for r in rows)
    for language in ('en','vi'):
        path=ROOT/f'results/comparison_result/drl_seed100_comprehensive_report_{language}.md'
        text=path.read_text(encoding='utf-8')
        original[path]=text
        if language=='en':
            title='### 3.3 Decision behavior: measured deterministic replay audit'
            intro=('Supplement added after the original archived-data analysis: the existing CSVs did not store behavioral fields, '
                   'so the saved best_model.zip was replayed, without training, for exactly 12 episodes '
                   '(seeds 101,102,103 × low,medium,high,imbalance). New files are isolated in '
                   '[action_audit](../../evaluation/seed100/action_audit/action_audit_summary.md). '
                   'All 60 episode traffic values match the original best/episodes.csv with exact float equality, '
                   'and all 51,840 per-step metric/time comparisons also match. The original evaluation files and scorecards are unchanged.')
            image=f'![Measured decisions, overrides and exact green durations]({figure})'
            evidence=(f'The audit contains {n:,} decisions and {len(greens):,} completed green intervals. '
                      'Panel A assigns one exclusive outcome per decision interval, with counts and percentages within each requested-action row. '
                      'Priority is max-green override, min-green block, transition NOOP, then plain KEEP/SWITCH. '
                      f'Startup-phase request overrides: {startup:,}; these remain executed KEEP and are not relabelled as min-green blocks.')
            matrix_headers=['Requested action','KEEP','SWITCH','Blocked min-green','Forced max-green','Transition NOOP','Total']
            matrix_rows=[[f'{a} = {i}',*[str(v) for v in matrix[i]],str(matrix[i].sum())]
                         for i,a in enumerate(('KEEP','SWITCH'))]
            behavior_headers=['Scenario','KEEP','SWITCH','NOOP excluded','KEEP / SWITCH denominator','KEEP (%)','SWITCH (%)',
                              'Completed greens','Green min / median / max (s)']
            behavior_rows=[]
            for r,v in zip(scenario_counts,samples):
                behavior_rows.append([r['scenario'],r['keep'],r['switch'],r['noop'],r['denominator'],
                                      f'{r["keep_pct"]:.6f}',f'{r["switch_pct"]:.6f}',len(v),
                                      f'{min(v):.6f} / {statistics.median(v):.6f} / {max(v):.6f}'])
            method=('Panel B normalizes KEEP/SWITCH only over executed non-NOOP decisions; transition NOOP remains visible in panel A and the table. '
                    'Panel C uses green_elapsed immediately before the actual green-departure call, recorded by read-only runtime wrappers '
                    'delegating to the original controller. Automatic max-green boundaries are captured at 0.1 s substeps. '
                    'No duration is inferred from five-second phase runs. The still-active final green in an episode is right-censored and excluded. '
                    f'Observed completed durations span {minimum:.6f}–{maximum:.6f} s, satisfying the configured bounds within simulator floating-point precision.')
            provenance=('Pre/post state, request-time execution, final interval outcomes and timestamped events are in '
                        '[action_steps.csv](../../evaluation/seed100/action_audit/action_steps.csv); exact completed durations are in '
                        '[action_switches.csv](../../evaluation/seed100/action_audit/action_switches.csv). '
                        '[action_episodes.csv](../../evaluation/seed100/action_audit/action_episodes.csv) retains episode means for four metrics and '
                        'the episode sum for arrivals, following the original definition. '
                        '[reproducibility_check.json](../../evaluation/seed100/action_audit/reproducibility_check.json) records the exact comparisons. '
                        'This is a supplementary behavioral replay, not a replacement performance evaluation or a safety certification.')
            missing=('**Remaining instrumentation limits:** the supplementary 12-episode action audit now supplies the measured data in Figure 03, '
                     'with exact reproduction of the original traffic metrics. It excludes unfinished green intervals and does not instrument pure policy-inference latency. '
                     'No independently evaluated seed-107 500k table exists; Figure 07 omits that unevaluated model. '
                     'The 218880 critic spike still has no proven causal diagnosis.')
            note_pattern=r'(?m)^\*\*(?:Missing instrumentation|Remaining instrumentation limits):\*\*.*$'
        else:
            title='### 3.3 Hành vi ra quyết định: audit replay tất định đã đo'
            intro=('Phần bổ sung sau phân tích dữ liệu lưu trữ ban đầu: CSV cũ không lưu các trường hành vi, '
                   'vì vậy đã replay best_model.zip có sẵn, không huấn luyện, đúng 12 episode '
                   '(seed 101,102,103 × low,medium,high,imbalance). File mới được cách ly tại '
                   '[action_audit](../../evaluation/seed100/action_audit/action_audit_summary.md). '
                   'Cả 60 giá trị giao thông theo episode khớp CSV best/episodes.csv bằng so sánh float chính xác; '
                   'đồng thời 51.840 phép đối chiếu metric/thời gian từng bước cũng khớp. File đánh giá gốc và các bảng kết quả được giữ nguyên.')
            image=f'![Hành động, override và thời lượng xanh thực đo]({figure})'
            evidence=(f'Audit ghi {n:,} quyết định và {len(greens):,} khoảng xanh đã kết thúc. '
                      'Khung A phân mỗi khoảng quyết định vào đúng một kết quả, hiển thị số lượt và tỷ lệ phần trăm trong từng hàng action yêu cầu. '
                      'Thứ tự ưu tiên là ép chuyển max-green, chặn min-green, NOOP chuyển tiếp, rồi KEEP/SWITCH thông thường. '
                      f'Có {startup:,} override tại pha khởi động; các trường hợp này vẫn là KEEP thực thi, không đổi nhãn thành chặn min-green.')
            matrix_headers=['Action yêu cầu','KEEP','SWITCH','Chặn min-green','Ép max-green','NOOP chuyển tiếp','Tổng']
            matrix_rows=[[f'{a} = {i}',*[str(v) for v in matrix[i]],str(matrix[i].sum())]
                         for i,a in enumerate(('KEEP','SWITCH'))]
            behavior_headers=['Kịch bản','KEEP','SWITCH','NOOP loại khỏi mẫu số','Mẫu số KEEP / SWITCH','KEEP (%)','SWITCH (%)',
                              'Khoảng xanh hoàn tất','Xanh min / trung vị / max (s)']
            behavior_rows=[]
            for r,v in zip(scenario_counts,samples):
                behavior_rows.append([r['scenario'],r['keep'],r['switch'],r['noop'],r['denominator'],
                                      f'{r["keep_pct"]:.6f}',f'{r["switch_pct"]:.6f}',len(v),
                                      f'{min(v):.6f} / {statistics.median(v):.6f} / {max(v):.6f}'])
            method=('Khung B chỉ chuẩn hóa KEEP/SWITCH trên các quyết định thực thi khác NOOP; NOOP chuyển tiếp vẫn được thể hiện ở khung A và trong bảng. '
                    'Khung C dùng green_elapsed ngay trước lệnh rời pha xanh thực tế, được ghi bằng wrapper quan sát lúc chạy và chuyển nguyên lời gọi cho controller gốc. '
                    'Biên ép chuyển max-green được ghi ở substep 0,1 s. Không suy thời lượng từ chuỗi pha 5 giây. '
                    'Pha xanh còn hoạt động cuối episode bị cắt phải nên không đưa vào phân bố. '
                    f'Thời lượng hoàn tất quan sát được nằm trong {minimum:.6f}–{maximum:.6f} s, phù hợp ràng buộc cấu hình trong sai số biểu diễn số thực của bộ mô phỏng.')
            provenance=('State trước/sau, kết quả ngay lúc yêu cầu, kết quả toàn khoảng và sự kiện có timestamp nằm trong '
                        '[action_steps.csv](../../evaluation/seed100/action_audit/action_steps.csv); thời lượng hoàn tất chính xác nằm trong '
                        '[action_switches.csv](../../evaluation/seed100/action_audit/action_switches.csv). '
                        '[action_episodes.csv](../../evaluation/seed100/action_audit/action_episodes.csv) giữ trung bình episode cho bốn metric và '
                        'tổng episode cho arrivals, đúng định nghĩa gốc. '
                        '[reproducibility_check.json](../../evaluation/seed100/action_audit/reproducibility_check.json) lưu các phép so sánh chính xác. '
                        'Đây là replay bổ sung để phân tích hành vi, không thay thế đánh giá hiệu năng hoặc chứng nhận an toàn.')
            missing=('**Giới hạn instrumentation còn lại:** audit hành động bổ sung 12 episode đã cung cấp dữ liệu thực đo cho Hình 03, '
                     'đồng thời tái lập chính xác metric giao thông gốc. Audit loại các khoảng xanh chưa kết thúc và chưa đo riêng độ trễ suy luận policy thuần. '
                     'Vẫn chưa có bảng đánh giá độc lập checkpoint 500k seed 107; Hình 07 bỏ mô hình chưa được đánh giá đó. '
                     'Nguyên nhân gai Critic tại 218880 vẫn chưa được chứng minh.')
            note_pattern=r'(?m)^\*\*(?:Thiếu instrumentation|Giới hạn instrumentation còn lại):\*\*.*$'
        section='\n\n'.join((title,intro,image,evidence,markdown_table(matrix_headers,matrix_rows).rstrip(),
                             markdown_table(behavior_headers,behavior_rows).rstrip(),method,provenance))+'\n\n'
        revised,count=re.subn(r'(?ms)^### 3\.3 .*?(?=^## 4\.)',lambda _:section,text,count=1)
        assert count==1
        # Replace only the related instrumentation paragraph within 6.1.
        match=re.search(r'(?ms)^### 6\.1 .*?(?=^### 6\.2 )',revised)
        assert match
        new_61,count=re.subn(note_pattern,lambda _:missing,match.group(),count=1)
        assert count==1
        revised=revised[:match.start()]+new_61+revised[match.end():]
        assert fixed_report_regions(text)==fixed_report_regions(revised)
        # All original scorecard sections, including every Table 1–4 cell, stay byte-for-byte identical.
        assert re.search(r'(?ms)^## 4\..*?(?=^## 5\.)',text).group()==re.search(r'(?ms)^## 4\..*?(?=^## 5\.)',revised).group()
        assert not re.search(r'\b(?:NaN|None)\b',revised)
        replacements[path]=revised
    for path,text in replacements.items():
        atomic_text(path,text)
    return {p.name:{'before_outside_allowed_sha256':text_sha(fixed_report_regions(original[p])),
                    'after_outside_allowed_sha256':text_sha(fixed_report_regions(text)),
                    'scorecard_section_unchanged':True} for p,text in replacements.items()}

def main():
    os.chdir(ROOT)
    rows,eps,greens,matrix,proof=load_actions()
    manifest=json.loads((AUDIT/'preservation_manifest.json').read_text(encoding='utf-8'))
    protected=manifest['protected_files_sha256']
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    report_guard=manifest['reports_outside_authorized_sections_sha256']
    for name,h in report_guard.items():
        assert text_sha(fixed_report_regions((ROOT/'results/comparison_result'/name).read_text(encoding='utf-8')))==h
    untouched={name:sha(PLOT/name) for name in FILENAMES[4:6]}
    eventpaths=list((ROOT/'runs/ppo_seed100').rglob('events.out.tfevents.*'))
    assert len(eventpaths)==1
    ea=EventAccumulator(str(eventpaths[0]),size_guidance={'scalars':0})
    ea.Reload()
    tags=['rollout/ep_rew_mean','train/explained_variance','train/value_loss',
          'train/policy_gradient_loss','train/loss','train/entropy_loss',
          'train/approx_kl','train/clip_fraction','train/learning_rate','time/fps']
    ts={t:ea.Scalars(t) for t in tags}
    assert all(math.isfinite(e.value) for values in ts.values() for e in values)
    with np.load(ROOT/'evaluation/seed100/validation/evaluations.npz') as npz:
        steps=npz['timesteps'].copy();means=npz['results'].mean(axis=1)
    best_step=int(steps[int(np.argmax(means))])
    assert best_step==316800
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,
                         'axes.labelsize':12,'legend.fontsize':10,'savefig.dpi':300})
    dip_value=make_training_plots(ts,steps,means,best_step)
    scenario_counts,samples=plot_actions(rows,greens,matrix)
    plot_timeseries()
    plot_progression()
    report_checks=update_reports(rows,greens,matrix,scenario_counts,samples)
    assert all(sha(PLOT/name)==value for name,value in untouched.items())
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    for name,h in report_guard.items():
        assert text_sha(fixed_report_regions((ROOT/'results/comparison_result'/name).read_text(encoding='utf-8')))==h
    readme="""# Seed 100 detailed analysis figures

Reproduction and refresh command (atsc environment):
    python -B scripts/export_seed100_plots.py --refresh

The action replay has already been completed: exactly 12 episodes, using the original saved best policy without training. Do not rerun it to refresh these plots. Its records are isolated under evaluation/seed100/action_audit.

| Figure | Data and display treatment |
| --- | --- |
| 01_learning_curves_reward_and_val.png | Unchanged TensorBoard/NPZ values. Both panels mark the 316800 best checkpoint; validation dip at 172800 is annotated from the actual NPZ mean. Raw training curve and display-only EMA alpha=0.10 retained. |
| 02_tensorboard_losses_and_diagnostics.png | Nine original scalar series. train/value_loss and train/loss use log Y axes with no replacement or clipping of values; the actual 218880 spike is retained. |
| 03_action_decision_and_override_matrix.png | Real audit: requested action by five exclusive interval outcomes, actual KEEP/SWITCH proportions excluding NOOP, and completed green-duration boxplots. Duration comes from controller-boundary timestamps, including automatic substeps, not phase runs times 5 s. |
| 04_timeseries_3600s_all_scenarios.png | Three-seed means at aligned post-step timestamps. Four snapshot rows show raw 5 s values (alpha=0.22, linewidth=0.7) plus full-window trailing 60 s means (12 samples, linewidth=1.8). The smoothed line starts at 60 s; no padded or partial windows. Cumulative arrivals remain unchanged. |
| 05_per_seed_breakdown_101_102_103.png | Preserved byte-for-byte. Individual seed waiting, queue and speed for High/Imbalance and all four methods. |
| 06_ppo_best_vs_final_stability.png | Preserved byte-for-byte. Sample Std ddof=1 and CV across three test seeds. |
| 07_v1_to_v2_progression_comparison.png | Only three independently evaluated models. No 107/500k placeholder; subtitle explains missing evaluation. Historical values and reduction formulas unchanged. Y ceiling increased for label clearance. |

All seven PNG files have 300-DPI metadata and positive size. The existing seed100_baseline_comparison.png remains byte-identical.

## Action audit definitions

- Source: evaluation/seed100/action_audit/action_steps.csv, action_episodes.csv, action_switches.csv.
- Reproducibility: 60/60 episode traffic values match exactly. Arrivals are episode sums; the other four metrics are episode time means. Every 5 s metric/time record also matches the original best evaluation exactly.
- Matrix cells show count and within-requested-action-row percentage. Each decision belongs to one outcome, with max-green override taking priority, then min-green block, transition NOOP, plain KEEP/SWITCH.
- Startup-phase blocks remain executed KEEP and are separately counted; they are not misclassified as min-green blocks.
- Panel B reports percentages over KEEP + SWITCH, explicitly excluding transition NOOP.
- Green durations are measured immediately before an actual green departure. The unfinished last green is right-censored and excluded. Min/max reference lines are 15/75 s.
- Only report Section 3.3 and its related instrumentation paragraph in Section 6.1 were changed. Original evaluation scorecards and all other report text remain unchanged.
- V1 comparisons remain descriptive because timing, seeds and measurement changed. No 500k evaluation or pure inference-latency measurement has been invented.

See quality_checks.json and evaluation/seed100/action_audit/reproducibility_check.json for automated checks.
"""
    atomic_text(PLOT/'README.md',readme)
    images=[]
    for filename in FILENAMES:
        path=PLOT/filename
        assert path.is_file() and path.stat().st_size>0
        with Image.open(path) as im:
            assert all(abs(d-300)<1 for d in im.info['dpi'])
            images.append(dict(file=filename,bytes=path.stat().st_size,pixels=list(im.size),
                               dpi=list(im.info['dpi']),sha256=sha(path)))
            im.verify()
    assert len(list(PLOT.glob('*.png')))==7
    table_counts=[];line_counts=[]
    for name in report_guard:
        path=ROOT/'results/comparison_result'/name
        text=path.read_text(encoding='utf-8')
        active=False;width=0;table_count=0
        for line in text.splitlines():
            if line.startswith('|'):
                cells=line.strip('|').split('|')
                if not active:
                    active=True;width=len(cells);table_count+=1
                assert len(cells)==width
            else:
                active=False
        assert len(re.findall(r'^## \d\.',text,re.M))==6
        links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
        assert len(links)==8 and all((path.parent/p).is_file() for p in links)
        assert not re.search(r'\b(?:NaN|None)\b',text)
        table_counts.append(table_count);line_counts.append(len(text.splitlines()))
    quality=json.loads((PLOT/'quality_checks.json').read_text(encoding='utf-8'))
    quality.update(status='passed',figures=images,markdown_tables=table_counts,report_lines=line_counts,
                   existing_files_sha256_unchanged=len(protected),
                   action_audit=dict(completed_episodes=12,decision_records=len(rows),
                                     exact_episode_metric_matches=60,episode_metrics_checked=60,
                                     exact_step_time_metric_matches=proof['step_metric_and_time_exact_checks'],
                                     maximum_absolute_episode_difference=0.0,
                                     decision_matrix_counts=matrix.tolist(),
                                     matrix_percent_denominator='Each requested-action row',
                                     panel_b_scenario_counts=scenario_counts,
                                     completed_green_intervals=len(greens),
                                     green_min=min(float(g['green_elapsed']) for g in greens),
                                     green_max=max(float(g['green_elapsed']) for g in greens)),
                   refresh=dict(figures_updated=[FILENAMES[i] for i in (0,1,2,3,6)],
                                figures_preserved_sha256=untouched,
                                validation_local_dip_step=172800,validation_local_dip_value=dip_value,
                                smoothing='Trailing full 12-sample windows; t=60..3600; no data padding',
                                protected_files_sha256_unchanged=len(protected),
                                report_scope_checks=report_checks),
                   limitations=['Seed107 500k evaluation unavailable',
                                'Pure inference latency not instrumented',
                                'Unfinished green intervals are right-censored and excluded'])
    atomic_text(PLOT/'quality_checks.json',json.dumps(quality,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':'passed','episodes':12,'exact_episode_metric_checks':60,
                      'step_metric_time_checks':proof['step_metric_and_time_exact_checks'],
                      'decisions':len(rows),'completed_green_intervals':len(greens),
                      'matrix':matrix.tolist(),'pngs':len(images),'tables_per_report':table_counts,
                      'protected_files_unchanged':len(protected),'report_scope_checks':report_checks},
                     indent=2,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()

