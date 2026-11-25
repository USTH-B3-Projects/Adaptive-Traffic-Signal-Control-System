import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#52514e",
  "axes.labelcolor":"#0b0b0b","xtick.color":"#52514e","ytick.color":"#52514e","axes.titlecolor":"#0b0b0b","pdf.fonttype":42})
BLUE,ORANGE,AQUA,YELLOW="#2a78d6","#eb6834","#1baf7a","#eda100"
# Numbers: evaluation with SUMO 1.28.0 (results/drl, results/constant); fixed-time and rule-based from branch maianh.
FT={'Low': [(4.96, 0.04), (18.0, 1.0), (97.88, 1.07), (567.63, 24.16)], 'Medium': [(12.93, 0.39), (35.67, 2.89), (238.83, 8.04), (1037.87, 74.52)], 'High': [(45.58, 2.86), (93.33, 3.21), (939.12, 75.53), (3160.43, 357.15)], 'Imbalance': [(82.78, 6.97), (259.67, 34.12), (1850.26, 111.75), (10014.07, 387.89)]}
RB={'Low': [(3.62, 0.11), (13.0, 1.0), (51.5, 1.62), (281.5, 49.75)], 'Medium': [(9.48, 0.18), (28.0, 1.0), (131.17, 2.95), (586.27, 63.43)], 'High': [(42.07, 3.47), (92.67, 2.08), (693.94, 51.83), (2471.07, 219.77)], 'Imbalance': [(38.56, 4.49), (119.67, 3.79), (692.27, 126.49), (4879.0, 1033.06)]}
SW={'Low': [(3.62, 0.1), (13.33, 1.15), (51.56, 1.64), (285.2, 51.79)], 'Medium': [(9.48, 0.18), (28.0, 1.0), (131.17, 2.95), (586.27, 63.43)], 'High': [(41.16, 3.1), (95.67, 9.71), (681.01, 58.16), (2631.1, 268.37)], 'Imbalance': [(77.13, 6.82), (239.0, 21.66), (1302.12, 101.6), (7040.53, 298.17)]}
DQ={'Low': [(0, 3.33, 14.33, 47.05, 278.57), (1, 3.63, 13.0, 52.12, 281.0), (2, 3.59, 14.0, 51.99, 270.17)], 'Medium': [(0, 9.66, 29.0, 135.84, 551.6), (1, 9.51, 28.33, 132.27, 607.9), (2, 9.58, 28.0, 135.08, 545.7)], 'High': [(0, 41.16, 95.67, 681.01, 2631.1), (1, 41.16, 95.67, 681.01, 2631.1), (2, 39.66, 87.0, 640.21, 2238.73)], 'Imbalance': [(0, 34.97, 107.33, 606.56, 3713.73), (1, 34.35, 106.0, 608.81, 3896.8), (2, 38.08, 118.33, 706.74, 4132.47), (3, 34.17, 107.67, 604.16, 3069.4), (4, 35.21, 111.33, 637.33, 3801.93)]}
KEEP=[(93.44, 11.93), (257.0, 26.89), (2912.17, 444.88), (14723.93, 2789.57)]
V2={'high_seed0_v2a_best':[(41.52, 5.4), (93.33, 4.51), (712.94, 119.28), (2602.2, 282.43)],'high_seed0_v2b_best':[(41.28, 2.85), (92.67, 10.02), (680.89, 58.3), (2804.9, 370.05)]}
def dq(s):
    a=np.array(DQ[s])[:,1:]; return a.mean(0), a.std(0,ddof=1)
SC=["Low","Medium","High","Imbalance"]
# Fig 1
fig,ax=plt.subplots(2,4,figsize=(10,4.6))
names=["Fixed-time","Rule-based","Always SWITCH","DQN (v1)"]; cols=[AQUA,ORANGE,YELLOW,BLUE]; hat=["//","..","xx",""]
for j,s in enumerate(SC):
    for i,(mi,lab) in enumerate([(0,"mean queue (vehicles)"),(2,"mean total waiting time (s)")]):
        a=ax[i,j]; dm,ds=dq(s)
        vals=[FT[s][mi],RB[s][mi],SW[s][mi],(dm[mi],ds[mi])]
        for k,(v,sd) in enumerate(vals):
            a.bar(k,v,yerr=sd,color=cols[k],hatch=hat[k],edgecolor="#fcfcfb",linewidth=0.8,capsize=2,error_kw={"lw":.8,"ecolor":"#0b0b0b"})
        a.set_xticks([]); 
        if i==0: a.set_title(s,fontweight="bold")
        if j==0: a.set_ylabel(lab)
        a.margins(y=.12)
h=[plt.Rectangle((0,0),1,1,facecolor=c,hatch=ht,edgecolor="#fcfcfb") for c,ht in zip(cols,hat)]
fig.legend(h,names,loc="lower center",ncol=4,frameon=False,bbox_to_anchor=(0.5,-0.01))
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig("figures/fig1_overview.pdf"); fig.savefig("figures/fig1_overview.png",dpi=200); plt.close(fig)
# Fig 2 imbalance per seed
a=np.array(DQ["Imbalance"]); fig,ax=plt.subplots(1,2,figsize=(8,3.3))
for i,(col,lab,idx,lines) in enumerate([(1,"mean queue (vehicles)",0,[("Rule-based",RB["Imbalance"][0][0],ORANGE,"-"),("Always SWITCH",SW["Imbalance"][0][0],YELLOW,"--"),("Always KEEP",KEEP[0][0],AQUA,":")]),
                                       (3,"mean total waiting time (s)",2,[("Rule-based",RB["Imbalance"][2][0],ORANGE,"-"),("Always SWITCH",SW["Imbalance"][2][0],YELLOW,"--"),("Always KEEP",KEEP[2][0],AQUA,":")])]):
    ax[i].bar(a[:,0],a[:,col],color=BLUE,edgecolor="#fcfcfb",width=.6)
    for x,v in zip(a[:,0],a[:,col]): ax[i].text(x,v,f"{v:.1f}",ha="center",va="bottom",fontsize=7.5,color="#0b0b0b")
    for n,v,c,ls in lines: ax[i].axhline(v,color=c,ls=ls,lw=1.6,label=n)
    ax[i].set_xticks(a[:,0]); ax[i].set_xlabel("DRL seed"); ax[i].set_ylabel(lab); ax[i].margins(y=.1)
h_,l_=ax[0].get_legend_handles_labels(); fig.legend(h_,l_,loc="lower center",ncol=3,frameon=False,fontsize=8,bbox_to_anchor=(0.5,-0.01))
fig.tight_layout(rect=(0,0.07,1,1)); fig.savefig("figures/fig2_imbalance_seeds.pdf"); fig.savefig("figures/fig2_imbalance_seeds.png",dpi=200); plt.close(fig)
# Fig 3 High v2
fig,ax=plt.subplots(1,2,figsize=(8,3.3))
labs=["Rule-based","Always\nSWITCH","DQN v1\n(3 seeds)","v2a best","v2b best"]
cs=[ORANGE,YELLOW,BLUE,BLUE,BLUE]; hs=["..","xx","","//","\\\\"]
dm,ds=dq("High")
v2=V2
sh=SW["High"]
q=[RB["High"][0],sh[0],(dm[0],ds[0]),v2["high_seed0_v2a_best"][0],v2["high_seed0_v2b_best"][0]]
w=[RB["High"][3],sh[3],(dm[3],ds[3]),v2["high_seed0_v2a_best"][3],v2["high_seed0_v2b_best"][3]]
for i,(vals,lab) in enumerate([(q,"mean queue (vehicles)"),(w,"max total waiting time (s)")]):
    for k,(v,sd) in enumerate(vals):
        ax[i].bar(k,v,yerr=sd,color=cs[k],hatch=hs[k],edgecolor="#fcfcfb",capsize=2,error_kw={"lw":.8,"ecolor":"#0b0b0b"})
        ax[i].text(k,v+sd,f"{v:.1f}",ha="center",va="bottom",fontsize=7.5)
    ax[i].set_xticks(range(5)); ax[i].set_xticklabels(labs,fontsize=7.5); ax[i].set_ylabel(lab); ax[i].margins(y=.15)
fig.tight_layout(); fig.savefig("figures/fig3_high_v2.pdf"); fig.savefig("figures/fig3_high_v2.png",dpi=200); plt.close(fig)
# Fig 4 improvement vs RB
fig,ax=plt.subplots(figsize=(7,3.4)); w_=0.2
mnames=["mean queue","max queue","mean total waiting time","max total waiting time"]; mc=[BLUE,ORANGE,AQUA,YELLOW]; mh=["","//","..","xx"]
imp=np.zeros((4,4))
for j,s in enumerate(SC):
    dm,_=dq(s)
    for m in range(4):
        r=RB[s][m][0]; imp[m,j]=(r-dm[m])/r*100
for m in range(4):
    xs=np.arange(4)+(m-1.5)*w_
    ax.bar(xs,imp[m],w_,color=mc[m],hatch=mh[m],edgecolor="#fcfcfb",label=mnames[m])
    for x,v in zip(xs,imp[m]): ax.text(x,v+(0.6 if v>=0 else -0.6),(f"{v:.0f}" if round(v)!=0 else "0"),ha="center",va="bottom" if v>=0 else "top",fontsize=7)
ax.axhline(0,color="#52514e",lw=.8); ax.set_xticks(range(4)); ax.set_xticklabels(SC)
ax.set_ylabel("DQN improvement over rule-based (%)\n(positive = DQN better)"); ax.legend(frameon=False,fontsize=8,ncol=2,loc="upper left"); ax.margins(y=.15)
fig.tight_layout(); fig.savefig("figures/fig4_vs_rulebased.pdf"); fig.savefig("figures/fig4_vs_rulebased.png",dpi=200); plt.close(fig)
np.set_printoptions(suppress=True); print(imp.round(1))
