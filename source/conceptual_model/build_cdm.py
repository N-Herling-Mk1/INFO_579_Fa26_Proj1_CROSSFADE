"""CROSSFADE conceptual data model draft (crow's foot) -> conceptual_data_model_draft.png

The graded deliverables/conceptual_data_model.png is the partner-drawn official
version (mk8). This script only rebuilds the draft it was checked against."""
import subprocess, sys
I = 72  # points per inch (neato -n2)
ENT, ASC = "#1F5FA8", "#B35C00"
nodes = {  # name: (x_in, y_in, kind)
 "Artist":(-0.4,3.2,"e"), "Track":(3.4,3.2,"e"), "Play":(7.2,3.2,"a"), "Listener":(11.0,3.2,"e"),
 "Genre Probability":(-0.4,1.0,"a"), "Track Score":(3.4,1.0,"a"), "Station":(7.2,0.4,"e"),
 "Station Blend":(10.4,-1.6,"a"), "Scoring Model":(5.3,-1.2,"e"), "Genre":(1.5,-2.4,"e"),
}
ONE, MANY1, MANY0, ONE0 = "teetee", "crowtee", "crowodot", "teeodot"
edges = [  # parent, child, parent-end, child-end, verb
 ("Artist","Track",ONE,MANY0,"uploads"),
 ("Track","Track Score",ONE,MANY0,"is scored in"),
 ("Scoring Model","Track Score",ONE,MANY0,"produces"),
 ("Genre","Track Score",ONE,MANY0,"is top genre of"),
 ("Listener","Play",ONE,MANY0,"streams"),
 ("Track","Play",ONE,MANY0,"is streamed in"),
 ("Station","Play",ONE0,MANY0,"surfaces"),
 ("Listener","Station",ONE,MANY0,"creates"),
 ("Scoring Model","Station",ONE,MANY0,"evaluates"),
 ("Station","Station Blend",ONE,MANY1,"blends"),
 ("Genre","Station Blend",ONE,MANY0,"is weighted in"),
 ("Track Score","Genre Probability",ONE,MANY1,"distributes over"),
 ("Genre","Genre Probability",ONE,MANY0,"is assigned in"),
]
L = ['digraph CDM {','graph [splines=line, outputorder=edgesfirst, pad=0.35, bgcolor=white];',
     'node [shape=box, style="filled,rounded", fontname="Helvetica-Bold", fontsize=15, width=2.3, height=0.6, fixedsize=true, penwidth=2];',
     'edge [dir=both, arrowsize=1.25, penwidth=1.6, color="#333333", fontname="Helvetica-Oblique", fontsize=11, fontcolor="#444444"];']
for n,(x,y,k) in nodes.items():
    c = ENT if k=="e" else ASC
    extra = ', peripheries=2' if k=="a" else ''
    L.append(f'"{n}" [pos="{x*I:.0f},{y*I:.0f}!", color="{c}", fillcolor="{c}18", fontcolor="{c}"{extra}];')
import math
lab=[]
for p,c,t,h,v in edges:
    L.append(f'"{p}" -> "{c}" [arrowtail={t}, arrowhead={h}];')
    (x1,y1,_),(x2,y2,_)=nodes[p],nodes[c]
    mx,my=(x1+x2)/2,(y1+y2)/2; dx,dy=x2-x1,y2-y1; n=math.hypot(dx,dy)
    nx,ny=-dy/n,dx/n
    if ny<0 or (abs(ny)<1e-9 and nx<0): nx,ny=-nx,-ny   # offset up / to the left side consistently
    off=0.22 if abs(dy)<1e-9 else 0.0
    if abs(dx)<1e-9: nx,ny,off=-1,0,0.62                # vertical edges: label to the left
    if off==0: nx,ny,off=(-dy/n,dx/n,0.30)
    if v=='is weighted in': nx,ny=-nx,-ny   # keep clear of Scoring Model
    lab.append((v,mx+nx*off,my+ny*off))
L.append('node [shape=plaintext, style="", width=0, height=0, fixedsize=false, fontname="Helvetica-Oblique", fontsize=12, fontcolor="#444444", penwidth=0];')
for i,(v,x,y) in enumerate(lab):
    L.append(f'"rl{i}" [label="{v}", pos="{x*I:.0f},{y*I:.0f}!"];')
# legend
lx, ly = 1.6, -3.6
leg = [("exactly one",ONE),("one or many",MANY1),("zero or one",ONE0),("zero or many",MANY0)]
L.append('node [shape=plaintext, style="", width=0, height=0, fixedsize=false, fontname="Helvetica", fontsize=12, fontcolor="#222222", penwidth=0];')
for i,(txt,sym) in enumerate(leg):
    x = lx + i*2.35
    L.append(f'"la{i}" [label="", pos="{x*I:.0f},{ly*I:.0f}!", width=0.01, height=0.01, fixedsize=true];')
    L.append(f'"lb{i}" [label="", pos="{(x+1.0)*I:.0f},{ly*I:.0f}!", width=0.01, height=0.01, fixedsize=true];')
    L.append(f'"lt{i}" [label="{txt}", pos="{(x+0.5)*I:.0f},{(ly-0.32)*I:.0f}!"];')
    L.append(f'"la{i}" -> "lb{i}" [dir=forward, arrowhead={sym}, label=""];')
L.append(f'"lk1" [label=<<font color="{ENT}"><b>&#9632;</b></font> entity>, pos="{(lx+2.0)*I:.0f},{(ly-0.85)*I:.0f}!"];')
L.append(f'"lk2" [label=<<font color="{ASC}"><b>&#9632;</b></font> associative entity (double border)>, pos="{(lx+5.2)*I:.0f},{(ly-0.85)*I:.0f}!"];')
L.append(f'"title" [label=<<b>CROSSFADE — Conceptual Data Model</b><br/><font point-size="12">crow\'s foot notation · relationships read parent → child</font>>, fontsize=20, pos="{5.3*I:.0f},{4.3*I:.0f}!"];')
L.append('}')
import os
HERE = os.path.dirname(os.path.abspath(__file__))
DOT = os.path.join(HERE, "cdm.dot")
PNG = os.path.normpath(os.path.join(HERE, "conceptual_data_model_draft.png"))
open(DOT,"w").write("\n".join(L))
print("[1/2] wrote cdm.dot"); sys.stdout.flush()
subprocess.run(["neato","-n2","-Tpng","-Gdpi=200",DOT,"-o",PNG],check=True)
print(f"[2/2] rendered {PNG}")
