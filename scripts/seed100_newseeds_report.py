"""Measured report/plots for the isolated three-seed comparison."""
from pathlib import Path
import csv,json,hashlib,math,re,statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
SC=('low','medium','high','imbalance')
MS=('fixed_time','rule_based','drl_ppo')
MT=('queue_length','waiting_time','average_speed','arrived_count','vehicles_in_network')
NAMES=dict(zip(MS,('Fixed-Time','Rule-Based','PPO best')))
LABEL=dict(zip(MT,('Queue (vehicles)','Waiting (s)','Speed (m/s)','Arrivals (vehicles)','Network vehicles')))
COLORS=dict(zip(MS,('#737b85','#e58d2c','#157f99')))
def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path,rows):
 assert rows
 with path.open('x',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def improvement(p,b,k):return 100*(p-b)/b if k in ('average_speed','arrived_count') else 100*(b-p)/b
def generate(E,R,report,metadata,protected,total_runtime):
 from DRL.metrics import aggregate_episodes
 root=E.parents[1];seeds=(57,367,1024)
 episodes=[];raw={};runtime=[]
 for method in MS:
  episodes+=read(E/method/'episodes.csv')
  runtime+=read(R/f'runtime_{method}.csv')
  for row in read(E/method/'metrics.csv'):
   raw.setdefault((method,row['scenario'],int(row['seed'])),[]).append(row)
 assert len(episodes)==36 and len(runtime)==36 and len(raw)==36
 episode_map={(r['method'],r['scenario'],int(r['seed'])):r for r in episodes}
 assert len(episode_map)==36 and set(episode_map)=={(m,s,k) for m in MS for s in SC for k in seeds}
 numeric_checks=0
 for key,rows in raw.items():
  assert len(rows)==720
  assert all(float(r['simulation_time'])==5*(i+1) for i,r in enumerate(rows))
  for metric in MT:
   values=[float(r[metric]) for r in rows];assert all(math.isfinite(v) for v in values)
   v=sum(values) if metric=='arrived_count' else statistics.fmean(values)
   assert v==float(episode_map[key][metric]),(key,metric)
   numeric_checks+=1
  assert int(episode_map[key]['samples'])==720 and float(episode_map[key]['end_time'])==3600
 typed=[]
 for row in episodes:
  typed.append(dict(row,seed=int(row['seed']),**{k:float(row[k]) for k in MT}))
 summary=aggregate_episodes(typed)
 summarymap={(r['method'],r['scenario']):r for r in summary}
 def mean(m,s,k):return summarymap[m,s][k+'_mean']
 def sd(m,s,k):return summarymap[m,s][k+'_std']
 for m in MS:
  for s in SC:
   for k in MT:
    values=[float(episode_map[m,s,seed][k]) for seed in seeds]
    assert mean(m,s,k)==statistics.fmean(values) and sd(m,s,k)==statistics.stdev(values)
    numeric_checks+=2
 improvements=[dict(scenario=s,metric=k,
   ppo_vs_fixed_time_percent=improvement(mean('drl_ppo',s,k),mean('fixed_time',s,k),k),
   ppo_vs_rule_based_percent=improvement(mean('drl_ppo',s,k),mean('rule_based',s,k),k))
   for s in SC for k in MT]
 write(E/'episodes.csv',episodes)
 write(E/'metrics.csv',[r for key in raw for r in raw[key]])
 write(R/'summary_final.csv',summary)
 write(R/'improvement.csv',improvements)
 write(R/'runtime.csv',runtime)
 (R/'pipeline_timings.json').write_text(json.dumps(dict(evaluation_wall_seconds=total_runtime,
  methods_concurrent=True,method_episode_wall_seconds={m:sum(float(r['wall_seconds']) for r in runtime if r['method']==m) for m in MS}),
  indent=2)+'\n',encoding='utf-8')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'legend.fontsize':11})
 figures=[]
 def save(fig,name):
  p=R/'plots'/name;assert not p.exists()
  fig.savefig(p,dpi=300,facecolor='white');plt.close(fig)
  with Image.open(p) as im:
   assert all(abs(d-300)<1 for d in im.info['dpi'])
   figures.append(dict(file=p.name,bytes=p.stat().st_size,pixels=list(im.size),dpi=list(im.info['dpi'])))
   im.verify()
 fig,axs=plt.subplots(5,4,figsize=(23,18),layout='constrained')
 for j,s in enumerate(SC):
  for i,k in enumerate(MT):
   ax=axs[i,j]
   for x,m in enumerate(MS):
    ax.bar(x,mean(m,s,k),yerr=sd(m,s,k),color=COLORS[m],capsize=4,width=.65)
   ax.set_xticks(range(3),['Fixed-Time','Rule-Based','PPO best'],rotation=15)
   ax.grid(axis='y',alpha=.18)
   if i==0:ax.set_title(s.title(),fontsize=16)
   if j==0:ax.set_ylabel(LABEL[k],fontsize=13)
 fig.suptitle('V2 seed 100 best: three-seed mean ± sample Std (ddof=1)\nTraffic evaluation seeds: 57, 367, 1024',fontsize=18)
 save(fig,'01_summary_comparison.png')
 fig,axs=plt.subplots(5,2,figsize=(16,18),layout='constrained')
 for j,s in enumerate(('high','imbalance')):
  for i,k in enumerate(MT):
   ax=axs[i,j];x=np.arange(3)
   for z,m in enumerate(MS):
    ax.bar(x+(z-1)*.24,[float(episode_map[m,s,seed][k]) for seed in seeds],.24,color=COLORS[m],label=NAMES[m])
   ax.set_xticks(x,[f'Seed {seed}' for seed in seeds]);ax.set_ylabel(LABEL[k])
   ax.grid(axis='y',alpha=.18)
   if i==0:ax.set_title(s.title(),fontsize=16)
 fig.legend([plt.Rectangle((0,0),1,1,color=COLORS[m]) for m in MS],
            [NAMES[m] for m in MS],loc='outside lower center',ncol=3,fontsize=13)
 fig.suptitle('High and Imbalance: each individual evaluation seed',fontsize=18)
 save(fig,'02_per_seed_high_imbalance.png')
 fig,axs=plt.subplots(5,4,figsize=(24,19),layout='constrained')
 for j,s in enumerate(SC):
  for i,k in enumerate(MT):
   ax=axs[i,j]
   for m in MS:
    values=np.array([[float(r[k]) for r in raw[m,s,seed]] for seed in seeds])
    if k=='arrived_count':values=np.cumsum(values,axis=1)
    ax.plot(np.arange(5,3601,5),values.mean(axis=0),color=COLORS[m],lw=1.1)
   ax.set_xlim(0,3600);ax.set_xticks([0,900,1800,2700,3600]);ax.grid(alpha=.18)
   if i==0:ax.set_title(s.title(),fontsize=16)
   if j==0:ax.set_ylabel('Cumulative arrivals' if k=='arrived_count' else LABEL[k],fontsize=13)
   if i==4:ax.set_xlabel('Simulation time (s)',fontsize=12)
 fig.legend([plt.Line2D([],[],color=COLORS[m],lw=2) for m in MS],
            [NAMES[m] for m in MS],loc='outside lower center',ncol=3,fontsize=13)
 fig.suptitle('Aligned post-step traffic: mean of seeds 57, 367, 1024\n'
              'Samples begin at 5 s; arrivals are cumulative, other metrics are snapshots',fontsize=18)
 save(fig,'03_timeseries_all_scenarios.png')
 lines=[]
 def add(text=''):lines.extend([text,''])
 def table(headers,rows):
  lines.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
  for row in rows:
   assert len(row)==len(headers)
   lines.append('| '+' | '.join(map(str,row))+' |')
  lines.append('')
 def f(x):return f'{float(x):.6f}'
 add('# Đối chiếu DRL V2 seed 100 trên bộ seed lưu lượng 57, 367, 1024')
 add('Ngày thực hiện: 25/11/2026. Báo cáo dùng riêng dữ liệu mới chạy; không huấn luyện lại và không thay thế kết quả bộ 101/102/103. '
     'PPO best được chọn từ thực nghiệm trước, nạp trọng số cố định và suy luận deterministic=True; hai baseline được chạy mới trên cùng bộ seed.')
 add('## 1. Cấu hình, môi trường và giao thức công bằng')
 table(['Thiết lập','Giá trị'],[[k,str(metadata['settings'][k])] for k in
       ('simulation_step','decision_interval','min_green','max_green','yellow_time','all_red_time','gui')])
 add('Quan sát PPO: Box float32 12D trong [0,1], theo hai trục NS/EW; action Discrete(2), 0=KEEP và 1=SWITCH. '
     'Mô hình nạp thành công bằng PPO trên '+metadata['gpu']+'. SUMO_HOME='+metadata['sumo_home']+'.')
 table(['Thư viện','Phiên bản'],list(metadata['versions'].items()))
 add('PPO và Rule-Based dùng chung Environment/SignalController, xanh tối thiểu 15 s và tối đa 75 s. '
     'Fixed-Time giữ chương trình SUMO tĩnh: xanh 51 s mỗi trục, chu kỳ 114 s, vàng 3 s và toàn đỏ 3 s; '
     'xanh nằm trong khoảng 15–75 s nhưng không có quyết định thích nghi KEEP/SWITCH. '
     'Cả ba dùng StateExtractor và phép đo V2 trên cùng tám làn vào.')
 add('Mỗi episode 3600 s, 720 mẫu post-step tại 5..3600 s. Queue là số xe dừng; waiting là tổng current waiting theo làn, '
     'không phải delay trung bình mỗi hành trình; speed (m/s) có trọng số số xe trên tám làn vào; vehicles_in_network là số xe toàn mạng. '
     'Bốn chỉ số này lấy trung bình snapshot. Arrivals cộng đủ mọi substep 0,1 s rồi cộng toàn episode. '
     'Cùng seed và cấu hình đồng bộ đầu vào ngẫu nhiên; quỹ đạo và chèn xe vẫn có thể phụ thuộc controller.')
 add('So với log baseline V1 cũ dùng min_green=30 s, lần đối chiếu này chạy lại baseline theo V2 15 s và thống nhất seed, arrivals, '
     'phạm vi speed, thời điểm lấy mẫu. Không trộn số liệu baseline cũ vào bảng mới. '
     'Ba seed kiểm thử không xuất hiện trong JSONL reset huấn luyện đã kiểm tra; riêng 1024 nằm trong dải RNG huấn luyện nhưng không được rút ở lần chạy đã lưu.')
 add('Ba phương pháp chạy song song bằng tiến trình riêng; từng phương pháp chạy tuần tự 12 episode. Runtime là wall time thực tế trong điều kiện chia sẻ tài nguyên, '
     'bao gồm khởi động/đóng SUMO và suy luận, không gồm nạp model một lần; không dùng để kết luận tốc độ thuật toán khi chạy độc lập hoặc độ trễ mạng thuần.')
 add('## 2. Bảng 1 — Trung bình đa seed ± độ lệch chuẩn mẫu')
 add('Std dùng ddof=1 trên ba kết quả episode. Queue, waiting, network occupancy càng thấp càng tốt; speed, arrivals càng cao càng tốt. '
     'Cột tốt nhất chỉ dựa trên trung bình mô tả; giữ các trường hợp đồng hạng.')
 table(['Kịch bản','Chỉ số','Fixed-Time','Rule-Based','PPO best','Trung bình tốt nhất'],[
  [s,k,*[f(mean(m,s,k))+' ± '+f(sd(m,s,k)) for m in MS],
   ', '.join(NAMES[m] for m in MS if mean(m,s,k)==(max if k in ('average_speed','arrived_count') else min)(mean(n,s,k) for n in MS))]
  for s in SC for k in MT])
 add('## 3. Bảng 2 — Tỷ lệ cải thiện PPO best')
 add('Mức cải thiện dương nghĩa là tốt hơn: 100(B−P)/B cho queue/wait/network; 100(P−B)/B cho speed/arrivals. '
     'P là PPO best, B là baseline. Tính trước khi làm tròn.')
 table(['Kịch bản','Chỉ số','So với Fixed-Time (%)','So với Rule-Based (%)'],[
  [r['scenario'],r['metric'],f(r['ppo_vs_fixed_time_percent']),f(r['ppo_vs_rule_based_percent'])] for r in improvements])
 add('## 4. Bảng 3 — Chi tiết từng seed')
 for seed in seeds:
  add(f'### Seed {seed}')
  table(['Kịch bản','Phương pháp','Queue','Waiting (s)','Speed (m/s)','Arrivals','Network vehicles'],[
   [s,NAMES[m],*[f(episode_map[m,s,seed][k]) for k in MT]] for s in SC for m in MS])
 add('Độ khó phụ thuộc phương pháp/kịch bản; bảng sau xếp seed theo waiting thực tế, không coi một seed luôn nặng hơn về nhu cầu đầu vào.')
 table(['Kịch bản','Phương pháp','Waiting giảm dần: seed:giá trị'],[
  [s,NAMES[m],'; '.join(f'{seed}:{f(episode_map[m,s,seed]["waiting_time"])}' for seed in
    sorted(seeds,key=lambda k:float(episode_map[m,s,k]['waiting_time']),reverse=True))] for s in SC for m in MS])
 add('## 5. Bảng 4 — Runtime thực đo')
 table(['Phương pháp','Kịch bản','Seed','Wall time (s)','Wall ms / decision'],[
  [NAMES[r['method']],r['scenario'],r['seed'],f(r['wall_seconds']),f(r['wall_ms_per_decision'])] for r in runtime])
 add(f'Thời gian từ lúc khởi chạy các worker đến hoàn tất đánh giá: {total_runtime:.6f} s. Tổng wall time các episode '
     'không bằng thời gian toàn luồng vì các phương pháp chạy đồng thời. Chỉ số ms/decision gồm cả SUMO/TraCI, không phải latency suy luận thuần.')
 add('## 6. Biểu đồ và phân tích từ dữ liệu mới')
 for img in figures:
  add('!['+img['file']+'](../'+R.name+'/plots/'+img['file']+')')
 for s in SC:
  favorable=[k for k in MT if improvement(mean('drl_ppo',s,k),mean('rule_based',s,k),k)>0]
  equal=[k for k in MT if mean('drl_ppo',s,k)==mean('rule_based',s,k)]
  add(f'**{s.title()}:** PPO best tốt hơn Rule-Based trên {len(favorable)}/5 trung bình; '
      f'{len(equal)} chỉ số bằng nhau. Cải thiện queue: '
      f'{improvement(mean("drl_ppo",s,"queue_length"),mean("rule_based",s,"queue_length"),"queue_length"):.6f}%; '
      f'waiting: {improvement(mean("drl_ppo",s,"waiting_time"),mean("rule_based",s,"waiting_time"),"waiting_time"):.6f}%. '
      'Chiều biến động các chỉ số còn lại và mức phân tán được thể hiện đầy đủ trong Bảng 1–3.')
 add('Các xếp hạng là kết quả mô tả của một checkpoint và ba seed lưu lượng, không phải kiểm định ý nghĩa thống kê hoặc bằng chứng nhân quả '
     'riêng cho từng thành phần kiến trúc. Std phản ánh seed lưu lượng, chưa phản ánh seed huấn luyện. '
     'Cửa sổ 3600 s có thể còn xe chưa hoàn thành; occupancy trung bình không phải backlog cuối kỳ. '
     'Cảnh báo SUMO, nếu có, được giữ trong subprocess log; các chỉ số ùn tắc không chứng nhận an toàn giao thông.')
 add('## 7. Nguồn dữ liệu và kiểm chứng')
 add(f'Dữ liệu: [episodes.csv](../../evaluation/{E.name}/episodes.csv), '
     f'[metrics.csv](../../evaluation/{E.name}/metrics.csv), '
     f'[summary_final.csv](../{R.name}/summary_final.csv), [improvement.csv](../{R.name}/improvement.csv), '
     f'[runtime.csv](../{R.name}/runtime.csv), [metadata](../{R.name}/run_metadata.json), '
     f'[kiểm tra chất lượng](../{R.name}/quality_checks.json).')
 add('Script gọi lại DRL.evaluate.evaluate_scenario, DRL.baselines.fixed_episode/rule_episode và DRL.metrics; '
     'không sửa bộ ghi file hoặc các đường dẫn output mặc định của dự án. '
     'Không gọi learn và không lưu lại model. Các file cũ được đối chiếu SHA-256 trước/sau.')
 add(f'Đã tái tính {numeric_checks} giá trị episode/trung bình/Std từ 36 nhóm dữ liệu, '
     'mỗi nhóm 720 mẫu. Các bảng dùng số liệu nguồn chưa làm tròn, hiển thị sáu chữ số thập phân; '
     'đủ 36 runtime, 20 cặp tỷ lệ cải thiện và ba biểu đồ 300 DPI.')
 text='\n'.join(lines)+'\n'
 assert not re.search(r'\b(?:NaN|None|inf)\b',text,re.I)
 active=False;width=0;tables=0
 for line in text.splitlines():
  if line.startswith('|'):
   n=len(line.split('|'))-2
   if not active:active=True;width=n;tables+=1
   assert n==width
  else:active=False
 assert not report.exists()
 # Validate links including planned quality output before publishing.
 links=re.findall(r'\[[^\]]*\]\(([^)]+)\)',text)
 for link in links:
  p=(report.parent/link).resolve()
  assert p.is_file() or p==R/'quality_checks.json',link
 assert all(sha(root/p)==h for p,h in protected.items())
 with report.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
 quality=dict(status='passed',episodes=36,samples=25920,episode_samples=720,numeric_checks=numeric_checks,
   summary_rows=12,improvement_rows=20,runtime_rows=36,ddof=1,markdown_tables=tables,
   protected_files_unchanged=len(protected),model_sha256_unchanged=sha(root/metadata['model'])==metadata['model_sha256'],
   figures=figures,training_executed=False,concurrent_methods=True)
 (R/'quality_checks.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 for p in [*E.rglob('*.csv'),*R.rglob('*.csv'),*R.rglob('*.png'),report]:
  assert p.is_file() and p.stat().st_size>0
 for link in links:assert (report.parent/link).resolve().is_file()
 assert all(sha(root/p)==h for p,h in protected.items())
 print(json.dumps(quality,indent=2),flush=True)

