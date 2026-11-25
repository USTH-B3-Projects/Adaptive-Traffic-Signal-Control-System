"""Isolated inference-only comparison on traffic seeds 57, 367 and 1024."""
from pathlib import Path
import argparse,csv,hashlib,json,logging,os,subprocess,sys,time,statistics,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
TAG='seed100_eval_57_367_1024'
E=ROOT/'evaluation'/TAG
R=ROOT/'results'/TAG
REPORT=ROOT/'results/comparison_result/drl_seed100_eval_57_367_1024_comparison.md'
MODEL=ROOT/'models/seed100/best_model/best_model.zip'
SEEDS=(57,367,1024)
SC=('low','medium','high','imbalance')
MS=('fixed_time','rule_based','drl_ppo')
MT=('queue_length','waiting_time','average_speed','arrived_count','vehicles_in_network')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 rows=list(rows);assert rows
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def jsonwrite(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def worker(method):
 from DRL.baselines import fixed_episode,rule_episode
 from DRL.metrics import episode_summary,aggregate_episodes
 model=None
 if method=='drl_ppo':
  from stable_baselines3 import PPO
  from DRL.evaluate import evaluate_scenario
  model=PPO.load(MODEL,device='cuda')
  assert model.observation_space.shape==(12,)
 folder=E/method
 folder.mkdir(exist_ok=False)
 episodes=[];allrows=[];timings=[]
 for seed in SEEDS:
  for scenario in SC:
   print(f'START {method} {scenario} seed={seed}',flush=True)
   started=time.perf_counter()
   if method=='drl_ppo':
    result=evaluate_scenario(model,scenario,seed)
    rows=result['rows']
   else:rows=(fixed_episode if method=='fixed_time' else rule_episode)(scenario,seed)
   elapsed=time.perf_counter()-started
   assert len(rows)==720
   assert all(float(r['simulation_time'])==5*(i+1) for i,r in enumerate(rows))
   assert all(math.isfinite(float(r[k])) for r in rows for k in MT)
   episode=episode_summary(rows)
   assert episode['end_time']==3600
   write(folder/f'metrics_{scenario}_seed{seed}.csv',rows)
   write(folder/f'episode_{scenario}_seed{seed}.csv',[episode])
   episodes.append(episode);allrows.extend(rows)
   timings.append(dict(method=method,scenario=scenario,seed=seed,wall_seconds=elapsed,
                       samples=720,wall_ms_per_decision=elapsed/720*1000))
   jsonwrite(R/f'progress_{method}.json',dict(completed=len(episodes),last_scenario=scenario,last_seed=seed,elapsed_seconds=elapsed))
   print(f'DONE {method} {scenario} seed={seed} seconds={elapsed:.3f}',flush=True)
 write(folder/'metrics.csv',allrows)
 write(folder/'episodes.csv',episodes)
 write(folder/'summary.csv',aggregate_episodes(episodes))
 write(R/f'runtime_{method}.csv',timings)

def main():
 if E.exists() or R.exists() or REPORT.exists():raise FileExistsError('New output targets already exist; refusing overwrite')
 E.mkdir();R.mkdir();(R/'plots').mkdir()
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s',
   handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler(R/'pipeline.log',encoding='utf-8')])
 protected={}
 for folder in ('results','evaluation','models','runs','DRL','FixedTime','RuleBased','SUMO'):
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and not any(q==p or q in p.parents for q in (E,R)):
    protected[p.relative_to(ROOT).as_posix()]=sha(p)
 jsonwrite(R/'preservation_manifest.json',protected)
 from DRL.core.scenario_loader import load_settings
 from DRL.core.simulation import _binary,_traci
 from DRL.gym_env import TrafficSignalEnv
 from stable_baselines3 import PPO
 import torch,importlib.metadata
 settings=load_settings()
 expected=dict(simulation_step=.1,decision_interval=5,min_green=15,max_green=75,yellow_time=3,all_red_time=3,gui=False)
 assert all(settings[k]==v for k,v in expected.items())
 assert os.environ.get('SUMO_HOME') and torch.cuda.is_available()
 traci=_traci();binary=_binary(settings)
 version=subprocess.run([binary,'--version'],capture_output=True,text=True,check=True).stdout
 model=PPO.load(MODEL,device='cuda')
 assert model.observation_space.shape==(12,) and model.action_space.n==2
 assert (model.observation_space.low==0).all() and (model.observation_space.high==1).all()
 del model
 resetlog=[json.loads(line) for line in (ROOT/'runs/ppo_seed100/training_episodes.jsonl').read_text().splitlines()]
 overlap={str(s):sum(r['sumo_seed']==s for r in resetlog) for s in SEEDS}
 assert not any(overlap.values())
 metadata=dict(settings=settings,model=str(MODEL.relative_to(ROOT)),model_sha256=sha(MODEL),
  seeds=SEEDS,scenarios=SC,observation_shape=[12],observation_bounds=[0,1],deterministic=True,
  training=False,gpu=torch.cuda.get_device_name(0),sumo_home=os.environ['SUMO_HOME'],
  sumo_binary=binary,sumo_version=version,actual_training_seed_overlap=overlap,
  versions={p:importlib.metadata.version(p) for p in ('torch','stable-baselines3','gymnasium','numpy','PyYAML','matplotlib')},
  runtime_protocol='Three concurrent method processes; episodes sequential within each method. Episode wall time excludes model load and includes SUMO startup/close and inference.')
 jsonwrite(R/'run_metadata.json',metadata)
 logging.info('PREFLIGHT PASSED; settings=%s; GPU=%s',expected,metadata['gpu'])
 started=time.perf_counter();children=[];streams=[]
 try:
  for method in MS:
   stream=(R/f'subprocess_{method}.log').open('x',encoding='utf-8')
   streams.append(stream)
   process=subprocess.Popen([sys.executable,'-u','-B',str(Path(__file__).resolve()),'--method',method],
     cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
     env=dict(os.environ,PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg'))
   children.append((method,process))
  while any(p.poll() is None for _,p in children):
   for method,p in children:
    if p.poll() not in (None,0):raise RuntimeError(f'{method} failed: see subprocess log')
   status={}
   for method,p in children:
    progress=R/f'progress_{method}.json'
    try:status[method]=json.loads(progress.read_text()).get('completed',0) if progress.exists() else 0
    except json.JSONDecodeError:status[method]='writing'
   logging.info('PROGRESS %s; wall %.0fs',status,time.perf_counter()-started)
   time.sleep(25)
  assert all(p.returncode==0 for _,p in children)
 finally:
  for method,p in children:
   if p.poll() is None:
    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
    p.wait()
  for stream in streams:stream.close()
 from seed100_newseeds_report import generate
 generate(E,R,REPORT,metadata,protected,time.perf_counter()-started)
 logging.info('COMPLETED: %s',REPORT)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--method',choices=MS)
 args=parser.parse_args()
 if args.method:worker(args.method)
 else:main()

