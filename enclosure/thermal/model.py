#!/usr/bin/env python3
"""Five-node steady-state screening network. Not CFD or temperature calibration.

For each node: sum(G_ij * (T_i - T_j)) + G_i0*T_i = Q_i.
Compare upper-bay power on/off at identical SCD30 self-heating. This isolates
the enclosure-induced module rise; it does not predict the SHT31 readout.
"""
import csv
import itertools
import json
import os
from pathlib import Path
import re
import tempfile
import numpy as np
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'sensor-workshop-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).resolve().parent
INPUTS = json.loads((HERE/'inputs.json').read_text())
P = {}
for line in (HERE.parent/'parameters.scad').read_text().splitlines():
    m = re.match(r'(\w+)\s*=\s*(.*?);', line)
    if m: P[m[1]] = json.loads(m[2])
NODES = ['H', 'C', 'M', 'S', 'A']

def bridge_conductance(slotted, k):
    # Same notional perimeter cut in both versions; continuous plate in v0.2.
    x0,y0,x1,y1 = P['thermal_island']
    width = P['thermal_bridge_count']*P['thermal_bridge_width'] if slotted else 2*(x1-x0+y1-y0)
    return k*(width/1000)*(P['carrier_thickness']/1000)/(P['thermal_slot_width']/1000)

def network(slotted, k, coefficients):
    c=coefficients
    edges = [('H',None,c['H_ambient']),('H','C',c['H_C']),('H','M',c['H_M']),
             ('C',None,c['C_ambient']),('C','A',c['C_A']),('M','A',c['M_A']),
             ('M','S',c['M_S']),('S','A',c['S_A']),('S',None,c['S_ambient']),
             ('A',None,c['A_ambient']),('H','S',c['H_S_wire']),
             ('C','M',bridge_conductance(slotted,k)),
             ('H','A',c['H_A']+(c['slot_extra_H_A'] if slotted else 0))]
    matrix=np.zeros((5,5))
    for a,b,g in edges:
        assert g>0
        i=NODES.index(a);matrix[i,i]+=g
        if b is not None:
            j=NODES.index(b);matrix[j,j]+=g;matrix[i,j]-=g;matrix[j,i]-=g
    return matrix, edges

def solve(power, slotted=True, k=.22, coefficients=None):
    matrix,edges=network(slotted,k,coefficients or INPUTS['nominal'])
    q=np.array([power,0,0,INPUTS['sensor_self_heat_W'],0])
    baseline=q.copy();baseline[0]=0
    t=np.linalg.solve(matrix,q);t0=np.linalg.solve(matrix,baseline)
    assert np.max(abs(matrix@t-q))<1e-10
    rejected=sum(g*t[NODES.index(a)] for a,b,g in edges if b is None)
    assert abs(rejected-q.sum())<1e-10
    assert np.all(t>=-1e-10) and np.all(t-t0>=-1e-10)
    return t-t0, t

def main():
    keys=list(INPUTS['sweep'])
    scenarios=[]
    for values in itertools.product(*(INPUTS['sweep'][x] for x in keys),INPUTS['plastic_k_W_mK']):
        c={**INPUTS['nominal'],**dict(zip(keys,values[:-1]))}
        scenarios.append((c,values[-1]))
    # Check model invariants, not the validity of unmeasured coefficients.
    assert np.allclose(solve(0)[0],0)
    assert np.allclose(solve(1.6)[0],2*solve(.8)[0])
    rows=[]
    for case in INPUTS['cases']:
        solar=case['solar_W_m2']*case['absorptance']*P['case_width']*P['case_depth']/1e6
        power=case['electronics_W']+solar
        old=solve(power,False)[0][3];new=solve(power,True)[0][3]
        changes=[(solve(power,False,k,c)[0][3],solve(power,True,k,c)[0][3]) for c,k in scenarios]
        rows.append(dict(case=case['name'],electronics_W=case['electronics_W'],absorbed_top_solar_W=round(solar,4),
                         v02_nominal_rise_C=round(old,4),v03_nominal_rise_C=round(new,4),
                         v03_scenario_min_C=round(min(b for a,b in changes),4),v03_scenario_max_C=round(max(b for a,b in changes),4),
                         paired_improvement_min_C=round(min(a-b for a,b in changes),4),paired_improvement_max_C=round(max(a-b for a,b in changes),4)))
    with (HERE/'results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={'model':'unvalidated five-node steady-state engineering screen','CAD_version':'0.3','scenario_count':len(scenarios),
            'metric':'Enclosure-induced sensor/module temperature rise above identical self-heating-only baseline; NOT calibrated sensor readout error',
            'units':'W, K (temperature differences also C)',
            'nominal_plate_conductance_W_K':{'v02':bridge_conductance(False,.22),'v03':bridge_conductance(True,.22)},
            'geometry':{k:P[k] for k in ['thermal_island','thermal_slot_width','thermal_bridge_count','thermal_bridge_width','carrier_thickness']},
            'checks':['zero added heat gives zero enclosure rise','energy balance and equation residual < 1e-10 W','positive temperatures and conductances','linear response to added power'],
            'cases':rows,'limitations':['No physical thermal measurements or CFD.','Scenario extrema are not confidence intervals or guaranteed bounds.',
            'Sensor node omits package gradients and firmware compensation.','No sun-heated table, side solar load, gusts, transient warm-up or rain model.',
            'Slot leakage and all heat-transfer coefficients are unmeasured; geometry improvement is not guaranteed in practice.']}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    with PdfPages(HERE/'thermal-review.pdf') as pdf:
        fig,ax=plt.subplots(figsize=(10.5,7))
        power=np.linspace(0,1.8,100)
        low=min(solve(1,True,k,c)[0][3] for c,k in scenarios)
        high=max(solve(1,True,k,c)[0][3] for c,k in scenarios)
        ax.fill_between(power,power*low,power*high,color='#dce5df',label=f'{len(scenarios)} assumption combinations (not confidence bounds)')
        ax.plot(power,power*solve(1,False)[0][3],color='#a77c51',lw=2,label='v0.2 continuous carrier · nominal assumptions')
        ax.plot(power,power*solve(1,True)[0][3],color='#287a77',lw=2,label='v0.3 slotted carrier · nominal assumptions')
        ax.axhline(INPUTS['proposed_enclosure_bias_target_C'],color='#aa4b3d',ls='--',label='Proposed 0.5 °C enclosure contribution target')
        ax.set(xlabel='Assumed heat in upper bay (W), excluding SCD30 self-heating',ylabel='Additional sensor/module temperature rise (°C)',xlim=(0,1.8),ylim=(0,None))
        ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=8)
        fig.suptitle('Heat below the enclosure remains a measurement risk',fontsize=17,x=.1,ha='left')
        fig.text(.1,.04,'Steady-state screening, 25 °C ambient, shade. Coefficients and power are unmeasured.\nIncludes mounting conduction, warm air, radiation and wire conduction. Not a prediction of calibrated SCD30 readout.',fontsize=9)
        fig.subplots_adjust(left=.1,right=.96,top=.87,bottom=.19)
        fig.savefig(HERE/'thermal-screen.png',dpi=170);pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(10.5,7));ax=fig.add_axes([.07,.49,.86,.39]);ax.axis('off')
        points={'H':(.16,.76),'C':(.42,.76),'M':(.65,.76),'S':(.8,.2),'A':(.35,.2)}
        names={'H':'Upper bay / shell','C':'Outer carrier','M':'Mounting island','S':'SCD30 / PCB','A':'Under-skirt air'}
        for a,b,g in network(True,.22,INPUTS['nominal'])[1]:
            if b is None:continue
            x,y=points[a];u,v=points[b];ax.plot([x,u],[y,v],color='#9aa9a1',lw=1,zorder=0)
        for n,(x,y) in points.items():ax.text(x,y,n+'\n'+names[n],ha='center',va='center',fontsize=9,bbox=dict(boxstyle='round,pad=.6',fc='#eef3ef',ec='#5c7a70'))
        ax.set(xlim=(0,1),ylim=(-.08,1.08))
        fig.suptitle('What the small model can and cannot establish',x=.07,ha='left',fontsize=17)
        tableax=fig.add_axes([.07,.21,.86,.22]);tableax.axis('off')
        table=tableax.table(cellText=[[r['case'],f"{r['v02_nominal_rise_C']:.2f}",f"{r['v03_nominal_rise_C']:.2f}",f"{r['v03_scenario_min_C']:.2f}–{r['v03_scenario_max_C']:.2f}"] for r in rows],colLabels=['Assumed condition','v0.2 °C','v0.3 °C','v0.3 scenarios °C'],colWidths=[.52,.13,.13,.22],loc='center',cellLoc='left');table.auto_set_font_size(False);table.set_fontsize(8);table.scale(1,1.5)
        fig.text(.07,.06,'Ambient heat rejection: H, C, S and A. Air/radiation bypass H→M remains in both designs.\nSlots reduce the plastic path, but may leak warm air. Sun cases include top absorption only.\nPrint one pilot and compare the same operating sensor inside/outside the case against a separate shaded reference.',fontsize=9)
        pdf.savefig(fig);plt.close(fig)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
