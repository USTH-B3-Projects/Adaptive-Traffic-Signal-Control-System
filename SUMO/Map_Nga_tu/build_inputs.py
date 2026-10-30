from pathlib import Path
import xml.etree.ElementTree as E
import argparse
import math
import copy

parser = argparse.ArgumentParser(description='Regenerate the isolated test inputs (not the compiled network).')
parser.add_argument('--duration', type=float, default=3600, help='Flow end time in seconds')
parser.add_argument('--rate', type=float, default=180, help='Vehicles/hour per approach')
args = parser.parse_args()
if not math.isfinite(args.duration) or not math.isfinite(args.rate) or args.duration <= 0 or args.rate <= 0:
    parser.error('duration and rate must be finite positive numbers')
if args.duration <= 3 * 900 / args.rate:
    parser.error('duration must exceed the last staggered approach start')
R = Path(__file__).resolve().parent

def save(path, root):
    p = R / path
    p.parent.mkdir(parents=True, exist_ok=True)
    E.indent(root)
    E.ElementTree(root).write(p, encoding='utf-8', xml_declaration=True)

n = E.Element('nodes')
E.SubElement(n, 'node', id='J', x='0', y='0', type='traffic_light_right_on_red')
for arm,x,y in [('N',0,260.5),('S',0,-260.5),('E',260.5,0),('W',-260.5,0)]:
    E.SubElement(n,'node',id=arm,x=str(x),y=str(y),type='dead_end')
save('network/intersection.nod.xml',n)
e = E.Element('edges')
for arm in 'NSEW':
    for suffix,a,b in [('in',arm,'J'),('out','J',arm)]:
        E.SubElement(e,'edge',{'id':f'{arm}_{suffix}','from':a,'to':b,'numLanes':'2','speed':'13.9','width':'3.25','length':'250','priority':'1'})
save('network/intersection.edg.xml',e)
c = E.Element('connections')
# Clockwise approaches; SUMO orders right, straight lane 0/1, then left.
movements = {'N': {'r':'W','s':'S','l':'E'}, 'E': {'r':'N','s':'W','l':'S'},
             'S': {'r':'E','s':'N','l':'W'}, 'W': {'r':'S','s':'E','l':'N'}}
for i,arm in enumerate('NESW'):
    for j,(direction,lane) in enumerate([('r',0),('s',0),('s',1),('l',1)]):
        E.SubElement(c,'connection',{'from':arm+'_in','to':movements[arm][direction]+'_out',
                     'fromLane':str(lane),'toLane':str(lane),'tl':'J','linkIndex':str(i*4+j)})
save('network/intersection.con.xml',c)
a = E.Element('additional')
t = E.SubElement(a,'tlLogic',id='J',type='static',programID='test',offset='0')
for name,duration,green in [('NS through/right',30,{0,1,2,8,9,10}),
                            ('NS protected left',15,{3,11}),
                            ('EW through/right',30,{4,5,6,12,13,14}),
                            ('EW protected left',15,{7,15})]:
    for suffix,seconds,light in [('',duration,'G'),(' yellow',3,'y'),(' clearance',3,'r')]:
        state = ''.join(light if i in green else ('s' if light == 'G' and i in {0,4,8,12} else 'r') for i in range(16))
        if light == 'G':
            # Let the priority queue start before admitting stop-and-yield turns.
            E.SubElement(t,'phase',duration='3',state=state.replace('s','r'),name=name+' start')
            seconds -= 3
        E.SubElement(t,'phase',duration=str(seconds),state=state,name=name+suffix)
save('config/traffic_light.add.xml',a)
r = E.Element('routes')
for name,cls,length,width,speed,accel,decel,gap,tau,gain,keep in [
 ('motorcycle','motorcycle',2,.8,13.9,2.6,4.5,.5,.6,2,0),
 ('car','passenger',4.5,1.8,13.9,2,4.5,2.5,1.2,0,1),
 ('bus','bus',12,2.5,11.1,1.2,3.5,3,1.5,0,1)]:
    attrs = dict(id=name,vClass=cls,length=length,width=width,maxSpeed=speed,accel=accel,decel=decel,minGap=gap,tau=tau,lcSpeedGain=gain,lcKeepRight=keep,emergencyDecel=7,sigma=.5,speedFactor=1,speedDev=0,carFollowModel='Krauss',laneChangeModel='SL2015',lcStrategic=1,lcCooperative=1,lcAssertive=1,latAlignment='center',minGapLat=.6,jmStopSignWait=1)
    if name == 'motorcycle':
        attrs.update(lcCooperative=.5,latAlignment='arbitrary',maxSpeedLat=.6,lcSublane=1)
    # Keep a 1 m stopping buffer and never push into priority traffic out of impatience.
    attrs.update(jmStoplineGapMinor=1,impatience='off')
    attrs.update(guiShape={'motorcycle':'motorcycle', 'car':'passenger', 'bus':'bus'}[name], color={'motorcycle':'240,190,35', 'car':'45,125,215', 'bus':'225,90,55'}[name])
    E.SubElement(r,'vType',{k:str(v) for k,v in attrs.items()})
type_weights = {'motorcycle':.8, 'car':.17, 'bus':.03}
turn_weights = {'s':.6, 'l':.2, 'r':.2}
for arm in 'NESW':
    for direction,target in movements[arm].items():
        E.SubElement(r,'route',id=arm+'_'+direction,edges=arm+'_in '+target+'_out')
m = copy.deepcopy(r)
flows = []
for i,arm in enumerate('NSEW'):
    for kind,share in type_weights.items():
        for direction,turn_share in turn_weights.items():
            rate = args.rate * share * turn_share
            period = 3600 / rate
            # Keep immediate origin starts; spread rare streams across their periods.
            begin = i * 900 / args.rate if kind == 'motorcycle' and direction == 's' else period * (i + .5) / 4
            if begin >= args.duration:
                continue
            lane = 1 if direction == 'l' or (direction == 's' and kind == 'motorcycle') else 0
            flows.append(E.Element('flow',id=f'{arm}_{kind}_{direction}',type=kind,route=arm+'_'+direction,
                                   begin=f'{begin:.12g}',end=str(args.duration),vehsPerHour=f'{rate:.12g}',
                                   departLane=str(lane),departSpeed='0'))
r.extend(sorted(flows,key=lambda flow:float(flow.get('begin'))))
save('routes/test_routes.rou.xml',r)
# Keep the finite diagnostic independent of continuous demand.
# The extra motorcycle starts behind a bus on a valid straight lane to test safe overtaking.
cases = [('bus','s',0),('motorcycle','s',0),('motorcycle','s',1),('car','s',0),
         ('bus','l',1),('motorcycle','l',1),('car','l',1),
         ('bus','r',0),('motorcycle','r',0),('car','r',0)]
for group,(kind,direction,lane) in enumerate(cases):
    for arm in 'NESW':
        suffix = 'filter' if group == 1 else direction
        E.SubElement(m,'vehicle',id=f'{arm}_{kind}_{suffix}',type=kind,route=arm+'_'+direction,
                     depart=str(group*3),departLane=str(lane),departSpeed='0')
save('routes/movement_test.rou.xml',m)
c = E.Element('configuration')
for section,values in [('input',{'net-file':'../network/intersection.net.xml','route-files':'../routes/test_routes.rou.xml','additional-files':'traffic_light.add.xml,environment.add.xml'}),('time',{'begin':'0','end':str(args.duration + 120),'step-length':'0.1'}),('processing',{'collision.check-junctions':'true','collision.action':'warn','lateral-resolution':'0.325'}),('random_number',{'seed':'42'}),('gui_only',{'gui-settings-file':'gui.view.xml','delay':'60'})]:
    s = E.SubElement(c,section)
    for key,value in values.items(): E.SubElement(s,key,value=value)
save('config/intersection.sumocfg',c)
movement_config = copy.deepcopy(c)
movement_config.find('input/route-files').set('value','../routes/movement_test.rou.xml')
movement_config.find('time/end').set('value','360')
save('config/movement_test.sumocfg',movement_config)
# Decorative polygons never create lanes, obstacles or pedestrian demand.
a = E.Element('additional')
def polygon(name, points, color, layer):
    E.SubElement(a, 'poly', id=name, type='decoration', color=color, fill='true',
                 layer=str(layer), shape=' '.join(f'{x},{y}' for x,y in points))
def rectangle(name, x1,y1,x2,y2,color,layer):
    polygon(name, [(x1,y1),(x2,y1),(x2,y2),(x1,y2)], color,layer)
for i,(x,y) in enumerate([(20,20),(281,20),(20,281),(281,281)]):
    rectangle(f'block_{i}',x,y,x+220,y+220,'178,199,162',-10)
    rectangle(f'paving_{i}',x+8,y+8,x+212,y+212,'219,215,203',-9)
    rectangle(f'garden_{i}',x+14,y+14,x+206,y+206,'166,192,145',-8)
    rectangle(f'building_{i}',x+38,y+38,x+130,y+100,'183,173,155',-7)
    rectangle(f'roof_{i}',x+42,y+42,x+126,y+96,'206,197,178',-6)
    for j,(dx,dy) in enumerate([(22,160),(60,180),(105,160),(160,30),(180,75),(165,130),(185,180)]):
        points=[(x+dx+5*math.cos(k*math.pi/8), y+dy+5*math.sin(k*math.pi/8)) for k in range(16)]
        polygon(f'tree_{i}_{j}',points,'76,126,78',-5)
for i,(lo,hi) in enumerate([(0,240),(281,521)]):
    for j,(left,right) in enumerate([(248,253),(268,273)]):
        rectangle(f'verge_ns_{i}_{j}',left,lo,right,hi,'213,209,196',-2)
        rectangle(f'verge_ew_{i}_{j}',lo,left,hi,right,'213,209,196',-2)
save('config/environment.add.xml',a)
view = E.Element('viewsettings')
scheme = E.SubElement(view,'scheme',name='test-intersection')
E.SubElement(scheme,'background',backgroundColor='234,232,223',showGrid='0')
E.SubElement(scheme,'edges',laneEdgeMode='0',laneShowBorders='1',showLinkDecals='1',showLinkRules='1',hideConnectors='0')
E.SubElement(scheme,'vehicles',vehicleMode='0',vehicleQuality='2',vehicle_exaggeration='1',vehicle_minSize='1',showBlinker='1')
E.SubElement(scheme,'junctions',junctionMode='0',drawShape='1',drawCrossingsAndWalkingareas='1')
E.SubElement(view,'viewport',x='260.5',y='260.5',zoom='110')
save('config/gui.view.xml',view)
