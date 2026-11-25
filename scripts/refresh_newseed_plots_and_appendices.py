"""Refresh presentation from existing CSVs and append source-verified report appendices.
No SUMO, PPO loading, training or evaluation is performed.
"""
from pathlib import Path
import csv,json,hashlib,re,statistics,subprocess
from PIL import Image
from seed100_newseeds_report import render_presentation_plots
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evaluation/seed100_eval_57_367_1024'
R=ROOT/'results/seed100_eval_57_367_1024'
FOLDER=ROOT/'results/comparison_result'
TARGETS=[FOLDER/name for name in (
 'drl_seed100_comprehensive_report_vi.md','drl_seed100_comprehensive_report_en.md',
 'drl_seed100_v2_report.md','drl_seed100_full_analysis_report.md')]
PLOTS=[R/'plots'/name for name in ('01_summary_comparison.png','02_per_seed_high_imbalance.png','03_timeseries_all_scenarios.png')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 assert all(p.is_file() for p in TARGETS)
 old={p:p.read_bytes() for p in TARGETS}
 for p,b in old.items():
  assert b'seed100' in b or b'Seed 100' in b or b'Seed100' in b
  assert b'APPENDIX-NEW-TRAFFIC-SEEDS-57-367-1024' not in b
 protected={p:sha(p) for folder in ('results','evaluation','models','runs') for p in (ROOT/folder).rglob('*')
            if p.is_file() and p not in TARGETS and p not in PLOTS}
 summary=read(R/'summary_final.csv');episodes=read(E/'episodes.csv');imps=read(R/'improvement.csv');runtime=read(R/'runtime.csv')
 meta=json.loads((R/'run_metadata.json').read_text(encoding='utf-8'))
 assert meta['model_sha256']==sha(ROOT/meta['model'])
 assert meta['deterministic'] and not meta['training']
 assert meta['settings']['min_green']==15 and meta['settings']['all_red_time']==3
 assert [len(x) for x in (summary,episodes,imps,runtime)]==[12,36,20,36]
 metrics=('queue_length','waiting_time','average_speed','arrived_count','vehicles_in_network')
 methods=('fixed_time','rule_based','drl_ppo');scenarios=('low','medium','high','imbalance');seeds=(57,367,1024)
 names=dict(zip(methods,('Fixed-Time','Rule-Based','PPO best')))
 sm={(x['method'],x['scenario']):x for x in summary}
 ep={(x['method'],x['scenario'],int(x['seed'])):x for x in episodes}
 raw={}
 for row in read(E/'metrics.csv'):raw.setdefault((row['method'],row['scenario'],int(row['seed'])),[]).append(row)
 checks=0
 for key,group in raw.items():
  assert len(group)==720 and all(float(row['simulation_time'])==5*(i+1) for i,row in enumerate(group))
  for k in metrics:
   values=[float(row[k]) for row in group]
   assert (sum(values) if k=='arrived_count' else statistics.fmean(values))==float(ep[key][k])
   checks+=1
 for m in methods:
  for s in scenarios:
   for k in metrics:
    v=[float(ep[m,s,seed][k]) for seed in seeds]
    assert statistics.fmean(v)==float(sm[m,s][k+'_mean'])
    assert statistics.stdev(v)==float(sm[m,s][k+'_std']);checks+=2
 for row in imps:
  s,k=row['scenario'],row['metric'];p=float(sm['drl_ppo',s][k+'_mean'])
  for m,col in (('fixed_time','ppo_vs_fixed_time_percent'),('rule_based','ppo_vs_rule_based_percent')):
   b=float(sm[m,s][k+'_mean']);v=100*(p-b)/b if k in ('average_speed','arrived_count') else 100*(b-p)/b
   assert v==float(row[col]);checks+=1
 render_presentation_plots(E,R)
 def f(v):return f'{float(v):.6f}'
 report_checks={}
 for path in TARGETS:
  vi=path.name.endswith('_vi.md');lines=[]
  def add(en,translation=None):lines.extend([translation if vi and translation is not None else en,''])
  def table(en,rows,translation=None):
   headers=translation if vi and translation is not None else en
   lines.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
   for row in rows:
    assert len(row)==len(headers);lines.append('| '+' | '.join(map(str,row))+' |')
   lines.append('')
  add('## Appendix — Additional traffic-seed evaluation: 57, 367, 1024',
      '## Phụ lục — Đánh giá bổ sung trên bộ seed lưu lượng 57, 367, 1024')
  add('<!-- APPENDIX-NEW-TRAFFIC-SEEDS-57-367-1024 -->')
  add('This appendix evaluates the same PPO best checkpoint from training seed 100 (models/seed100/best_model/best_model.zip), '
      'with deterministic=True and no retraining. It is a separate 36-episode / 25,920-sample comparison against newly executed Fixed-Time and Rule-Based baselines; '
      'the earlier 101/102/103 results and all preceding text remain unchanged.',
      'Phụ lục đánh giá cùng checkpoint PPO best của seed huấn luyện 100 (models/seed100/best_model/best_model.zip), '
      'với deterministic=True, không huấn luyện lại. Đây là đợt đối chiếu riêng gồm 36 episode / 25.920 mẫu với Fixed-Time và Rule-Based được chạy mới; '
      'kết quả 101/102/103 và toàn bộ nội dung phía trước giữ nguyên.')
  add('V2 settings: simulation step 0.1 s, decision interval 5 s, min/max green 15/75 s, yellow/all-red 3/3 s, 3600 s per episode. '
      'PPO/Rule-Based share adaptive signal constraints; Fixed-Time retains its static 51 s green per axis inside the same bounds. '
      'Shared post-step metrics use episode means, except arrived_count, which sums all 0.1 s substeps. '
      'Waiting is summed current lane waiting, not completed-trip delay; speed is vehicle-weighted on eight incoming lanes. '
      'These corrected V2 measurements and 15 s minimum green must not be conflated with older 30 s baseline logs.',
      'Cấu hình V2: bước mô phỏng 0,1 s, quyết định mỗi 5 s, xanh tối thiểu/tối đa 15/75 s, vàng/toàn đỏ 3/3 s, mỗi episode 3600 s. '
      'PPO/Rule-Based dùng chung ràng buộc điều khiển thích nghi; Fixed-Time giữ xanh tĩnh 51 s mỗi trục trong cùng giới hạn. '
      'Metric chung lấy sau bước và trung bình toàn episode, riêng arrived_count cộng đủ arrivals từng substep 0,1 s. '
      'Waiting là tổng current waiting theo làn, không phải delay hành trình; speed có trọng số trên tám làn vào. '
      'Không đồng nhất phép đo V2 đã sửa và xanh tối thiểu 15 s với các log baseline cũ dùng 30 s.')
  add('### A. Multi-seed mean ± sample Std (ddof=1)','### A. Trung bình đa seed ± độ lệch chuẩn mẫu (ddof=1)')
  add('Units: queue/network in vehicles, waiting in seconds, speed in m/s, arrivals in vehicles per episode. Lower queue/wait/network and higher speed/arrivals are favorable.',
      'Đơn vị: queue/network là xe, waiting là giây, speed là m/s, arrivals là xe/episode. Queue/wait/network càng thấp càng tốt; speed/arrivals càng cao càng tốt.')
  table(['Scenario','Metric','Fixed-Time','Rule-Based','PPO best'],[
   [s,k,*[f(sm[m,s][k+'_mean'])+' ± '+f(sm[m,s][k+'_std']) for m in methods]] for s in scenarios for k in metrics],
   ['Kịch bản','Chỉ số','Fixed-Time','Rule-Based','PPO best'])
  add('### B. PPO best improvement (%)','### B. Tỷ lệ cải thiện PPO best (%)')
  add('Positive is favorable: 100(B-P)/B for queue/wait/network; 100(P-B)/B for speed/arrivals. Calculated before rounding.',
      'Dương là cải thiện: 100(B-P)/B cho queue/wait/network; 100(P-B)/B cho speed/arrivals. Tính trước khi làm tròn.')
  table(['Scenario','Metric','vs Fixed-Time (%)','vs Rule-Based (%)'],[
   [r['scenario'],r['metric'],f(r['ppo_vs_fixed_time_percent']),f(r['ppo_vs_rule_based_percent'])] for r in imps],
   ['Kịch bản','Chỉ số','so với Fixed-Time (%)','so với Rule-Based (%)'])
  add('### C. Individual traffic seeds','### C. Phân rã từng seed lưu lượng')
  for seed in seeds:
   add(f'#### Seed {seed}')
   table(['Scenario','Method','Queue','Waiting (s)','Speed (m/s)','Arrivals','Network vehicles'],[
    [s,names[m],*[f(ep[m,s,seed][k]) for k in metrics]] for s in scenarios for m in methods],
    ['Kịch bản','Phương pháp','Queue','Waiting (s)','Speed (m/s)','Arrivals','Xe toàn mạng'])
  add('### D. Measured runtime','### D. Runtime thực đo')
  add('Methods ran concurrently; episode wall time includes SUMO startup/close and inference but excludes the one-time model load. '
      'These shared-resource measurements are not isolated algorithm-speed benchmarks or pure inference latency.',
      'Các phương pháp chạy đồng thời; wall time episode gồm khởi động/đóng SUMO và suy luận, không gồm lần nạp model ban đầu. '
      'Đây không phải benchmark tốc độ thuật toán chạy độc lập hoặc độ trễ suy luận thuần.')
  table(['Method','Scenario','Seed','Wall seconds'],[
   [names[r['method']],r['scenario'],r['seed'],f(r['wall_seconds'])] for r in runtime],
   ['Phương pháp','Kịch bản','Seed','Wall time (s)'])
  add('### E. Figures and source provenance','### E. Biểu đồ và nguồn dữ liệu')
  for p in PLOTS:
   add('!['+p.name+'](../seed100_eval_57_367_1024/plots/'+p.name+')')
  add('Figure 03 retains raw 5 s snapshot samples beneath trailing 60 s means (12 full samples, starting at t=60 s); cumulative arrivals are unchanged. '
      'This is a display transformation only. Three traffic seeds describe test variability, not training-seed uncertainty or statistical significance.',
      'Hình 03 giữ chuỗi snapshot gốc 5 s dưới đường trung bình trượt 60 s (đủ 12 mẫu, bắt đầu tại t=60 s); arrivals tích lũy giữ nguyên. '
      'Đây chỉ là biến đổi hiển thị. Ba seed lưu lượng phản ánh biến động kiểm thử, không phải bất định giữa seed huấn luyện hoặc bằng chứng ý nghĩa thống kê.')
  add('Sources: [episodes](../../evaluation/seed100_eval_57_367_1024/episodes.csv), '
      '[raw metrics](../../evaluation/seed100_eval_57_367_1024/metrics.csv), '
      '[mean/std](../seed100_eval_57_367_1024/summary_final.csv), '
      '[improvement](../seed100_eval_57_367_1024/improvement.csv), [runtime](../seed100_eval_57_367_1024/runtime.csv), '
      '[separate comparison report](drl_seed100_eval_57_367_1024_comparison.md).',
      'Nguồn: [episode](../../evaluation/seed100_eval_57_367_1024/episodes.csv), '
      '[metric thô](../../evaluation/seed100_eval_57_367_1024/metrics.csv), '
      '[mean/std](../seed100_eval_57_367_1024/summary_final.csv), '
      '[cải thiện](../seed100_eval_57_367_1024/improvement.csv), [runtime](../seed100_eval_57_367_1024/runtime.csv), '
      '[báo cáo đối chiếu riêng](drl_seed100_eval_57_367_1024_comparison.md).')
  appendix='\n'+'\n'.join(lines)+'\n'
  assert not re.search(r'\b(?:NaN|None|inf)\b',appendix,re.I)
  active=False;width=0
  for line in appendix.splitlines():
   if line.startswith('|'):
    n=len(line.split('|'))-2
    if not active:active=True;width=n
    assert n==width
   else:active=False
  for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',appendix):assert (path.parent/link).resolve().is_file()
  with path.open('ab') as stream:stream.write(appendix.encode('utf-8'))
  assert path.read_bytes()==old[path]+appendix.encode('utf-8')
  report_checks[path.name]=dict(original_bytes=len(old[path]),original_sha256=hashlib.sha256(old[path]).hexdigest(),append_only=True)
 assert all(sha(p)==h for p,h in protected.items())
 images=[]
 for p in PLOTS:
  assert p.stat().st_size>0
  with Image.open(p) as im:
   assert all(abs(d-300)<1 for d in im.info['dpi'])
   images.append(dict(file=p.name,bytes=p.stat().st_size,dpi=list(im.info['dpi']),sha256=sha(p)))
   im.verify()
 diff=subprocess.run(['git','diff','--numstat','--',*[str(p.relative_to(ROOT)) for p in TARGETS]],capture_output=True,text=True,check=True).stdout
 for line in diff.splitlines():assert line.split('\t')[1]=='0',line
 proof=dict(status='passed',numeric_source_checks=checks,protected_files_unchanged=len(protected),
            reports=report_checks,figures=images,git_diff_numstat=diff,training_or_evaluation_executed=False)
 dest=R/'presentation_appendix_checks.json'
 with dest.open('x',encoding='utf-8') as stream:json.dump(proof,stream,indent=2,ensure_ascii=False)
 print(json.dumps(proof,indent=2,ensure_ascii=False))
if __name__=='__main__':main()

