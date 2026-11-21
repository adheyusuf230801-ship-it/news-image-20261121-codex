import os, struct, zlib

W=H=1024
INK=(25,28,32); PAPER=(248,246,239); RED=(150,35,38); GRAY=(80,84,88); LIGHT=(224,220,210)
pix=[[PAPER for _ in range(W)] for _ in range(H)]
def rect(x,y,w,h,c):
    for yy in range(max(0,y),min(H,y+h)):
        row=pix[yy]
        for xx in range(max(0,x),min(W,x+w)): row[xx]=c
def line(x1,y1,x2,y2,c=INK,t=2):
    if x1==x2:
        rect(x1-t//2,min(y1,y2),t,abs(y2-y1)+1,c)
    elif y1==y2: rect(min(x1,x2),y1-t//2,abs(x2-x1)+1,t,c)
    else:
        # Rasterize the sloping strokes used by the existing pictograms.
        steps=max(abs(x2-x1),abs(y2-y1))
        for i in range(steps+1):
            x=round(x1+(x2-x1)*i/steps); y=round(y1+(y2-y1)*i/steps)
            rect(x-t//2,y-t//2,t,t,c)
def circle(cx,cy,r,c):
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            if 0<=x<W and 0<=y<H and (x-cx)**2+(y-cy)**2<=r*r: pix[y][x]=c
FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],'B':['11110','10001','10001','11110','10001','10001','11110'],'C':['01111','10000','10000','10000','10000','10000','01111'],'D':['11110','10001','10001','10001','10001','10001','11110'],'E':['11111','10000','10000','11110','10000','10000','11111'],'F':['11111','10000','10000','11110','10000','10000','10000'],'G':['01111','10000','10000','10111','10001','10001','01111'],'H':['10001','10001','10001','11111','10001','10001','10001'],'I':['11111','00100','00100','00100','00100','00100','11111'],'J':['00111','00010','00010','00010','10010','10010','01100'],'K':['10001','10010','10100','11000','10100','10010','10001'],'L':['10000','10000','10000','10000','10000','10000','11111'],'M':['10001','11011','10101','10101','10001','10001','10001'],'N':['10001','11001','10101','10011','10001','10001','10001'],'O':['01110','10001','10001','10001','10001','10001','01110'],'P':['11110','10001','10001','11110','10000','10000','10000'],'Q':['01110','10001','10001','10001','10101','10010','01101'],'R':['11110','10001','10001','11110','10100','10010','10001'],'S':['01111','10000','10000','01110','00001','00001','11110'],'T':['11111','00100','00100','00100','00100','00100','00100'],'U':['10001','10001','10001','10001','10001','10001','01110'],'V':['10001','10001','10001','10001','10001','01010','00100'],'W':['10001','10001','10001','10101','10101','11011','10001'],'X':['10001','10001','01010','00100','01010','10001','10001'],'Y':['10001','10001','01010','00100','00100','00100','00100'],'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],'1':['00100','01100','00100','00100','00100','00100','01110'],'2':['01110','10001','00001','00010','00100','01000','11111'],'3':['11110','00001','00001','01110','00001','00001','11110'],'4':['00010','00110','01010','10010','11111','00010','00010'],'5':['11111','10000','10000','11110','00001','00001','11110'],'6':['01110','10000','10000','11110','10001','10001','01110'],'7':['11111','00001','00010','00100','01000','01000','01000'],'8':['01110','10001','10001','01110','10001','10001','01110'],'9':['01110','10001','10001','01111','00001','00001','01110'],
' ':['00000']*7,'-':['00000','00000','00000','11111','00000','00000','00000'],'.':['00000']*6+['00100'],',':['00000']*6+['01000'],':':['00000','00100','00100','00000','00100','00100','00000'],'/':['00001','00010','00100','01000','10000','00000','00000'],'?':['01110','10001','00001','00010','00100','00000','00100']}
FONT['+']=['00000','00100','00100','11111','00100','00100','00000']
FONT['%']=['11001','11010','00010','00100','01000','01011','10011']
FONT[';']=['00000','00100','00100','00000','00100','00100','01000']
def text(x,y,s,scale=4,c=INK,maxw=None):
    s=s.upper(); step=6*scale
    if maxw:
        s=''.join(ch if ch in FONT else ' ' for ch in s)
    for ch in s:
        g=FONT.get(ch,FONT[' '])
        for ry,row in enumerate(g):
            for rx,v in enumerate(row):
                if v=='1': rect(x+rx*scale,y+ry*scale,scale,scale,c)
        x+=step
def text_width(s,scale):
    # Five bitmap columns plus one inter-character column; no trailing gap.
    return (6*len(s)-1)*scale if s else 0

def wrap(s,width,scale):
    out=[]; cur=''
    for word in s.upper().split():
        if text_width(word,scale)>width:
            raise ValueError('Word exceeds text area: '+word)
        candidate=(cur+' '+word).strip()
        if text_width(candidate,scale)<=width: cur=candidate
        else: out.append(cur); cur=word
    if cur: out.append(cur)
    return out

def panel(x,y,w,h,kicker,head,summary,kind):
    # Every panel reserves its rightmost 78 pixels for its pictogram.
    # A further 12-pixel gutter separates that zone from all text.
    tx=x+14; text_right=x+w-90; width=text_right-tx
    ks=next(s for s in (3,2,1) if text_width(kicker,s)<=width)
    chosen=None
    for ss in (2,1):
        for hs in (4,3,2):
            heads=wrap(head,width,hs); summaries=wrap(summary,width,ss)
            end=42+len(heads)*(7*hs+4)+len(summaries)*(7*ss+4)-4
            if end<=h-10:
                chosen=(hs,ss,heads,summaries); break
        if chosen: break
    if chosen is None: raise ValueError('Panel content does not fit: '+head)
    hs,ss,heads,summaries=chosen
    rect(x,y,w,h,LIGHT); rect(x,y,w,5,RED); text(tx,y+14,kicker,ks,RED)
    yy=y+42
    for ln in heads: text(tx,yy,ln,hs,INK); yy+=7*hs+4
    for ln in summaries: text(tx,yy,ln,ss,GRAY); yy+=7*ss+4
    ix=x+w-42; iy=y+h//2+10
    if kind=='explosion':
        circle(ix,iy,20,RED); line(ix-34,iy,ix+34,iy,INK,3); line(ix,iy-34,ix,iy+34,INK,3)
    elif kind=='chart':
        line(ix-28,iy+24,ix-10,iy+4,RED,5); line(ix-10,iy+4,ix+4,iy+12,RED,5); line(ix+4,iy+12,ix+28,iy-25,RED,5); line(ix-30,iy+28,ix+32,iy+28,INK,2)
    elif kind=='handshake':
        rect(ix-30,iy-8,25,16,INK); rect(ix+5,iy-8,25,16,INK); line(ix-5,iy,ix+5,iy,RED,5)
    elif kind=='eu':
        circle(ix,iy,25,INK); circle(ix,iy,17,PAPER)
        for a in range(0,360,60): circle(ix+int(12*__import__('math').cos(a)),iy+int(12*__import__('math').sin(a)),2,RED)
    elif kind=='border':
        rect(ix-30,iy-28,8,56,INK); rect(ix+22,iy-28,8,56,INK); line(ix-20,iy-8,ix+22,iy+18,RED,5)
    elif kind=='jail':
        for q in range(-24,25,12): line(ix+q,iy-25,ix+q,iy+25,INK,4)
        line(ix-30,iy+25,ix+30,iy+25,RED,4)
    elif kind=='ballot':
        rect(ix-26,iy-12,52,35,INK); rect(ix-18,iy-25,36,14,PAPER); line(ix-8,iy-18,ix+15,iy-18,RED,3)
    elif kind=='prime':
        text(ix-20,iy-18,'Z',5,RED); circle(ix+22,iy-6,8,INK); line(ix+10,iy+22,ix+32,iy+22,INK,3)
    elif kind=='target':
        circle(ix,iy,24,INK); circle(ix,iy,20,LIGHT)
        circle(ix,iy,11,RED); circle(ix,iy,7,LIGHT)
        line(ix-30,iy,ix+30,iy,INK,2); line(ix,iy-30,ix,iy+30,INK,2)
    elif kind=='missile':
        line(ix-34,iy+20,ix+25,iy-22,RED,8); line(ix-20,iy+22,ix-34,iy+34,INK,4); circle(ix+28,iy-25,7,INK)

rect(0,0,W,H,PAPER)
text(44,28,'THE WORLD IN ONE DAY',8,INK); text(48,102,'SATURDAY 21 NOVEMBER 2026',5,RED); line(42,148,982,148,RED,5)
rect(42,170,940,285,(235,232,222)); text(62,188,'LEAD / POLAND / NATO',3,RED)
lead_head='MISSILE LANDS ON NATO SOIL'
lead_summary=('RUSSIAN CRUISE MISSILE HITS NEAR NOWY LIPOWIEC; '
              'WARSAW CALLS IT A DELIBERATE PROVOCATION. '
              'NATO SCRAMBLES JETS AS ALLIES SEEK MORE SUPPORT.')
# The lead reserves x=778..944 for its larger pictogram, with a clear gutter.
text(62,220,lead_head,4,INK)
assert text_width(lead_head,4)<=688
for i,ln in enumerate(wrap(lead_summary,688,3)):
    text(62,270+i*25,ln,3,GRAY)

circle(850,292,72,PAPER); circle(850,292,55,INK); circle(850,292,42,PAPER); line(805,330,890,245,RED,10); circle(895,237,10,RED); text(790,370,'POLAND',3,RED)
panels=[
(42,475,300,170,'UKRAINE','AIR ATTACK','400+ DRONES, 110 MISSILES; AT LEAST 11 KILLED.','explosion'),
(362,475,300,170,'MARKETS','AI SELL-OFF','NASDAQ -5.28%; NVIDIA FALLS ABOUT 14%.','chart'),
(682,475,300,170,'DIPLOMACY','PEACE TALKS','US ENVOYS SEE A PATH TO SECURITY GUARANTEES.','handshake'),
(42,665,300,150,'EUROPE','UK-EU DEALS','FOOD, CARBON AND YOUTH MOBILITY PACTS SIGNED.','eu'),
(362,665,300,150,'BORDERS','ESTONIA CLOSES','ALL CROSSINGS TO RUSSIA SHUT AFTER SUSPECTED SABOTAGE.','border'),
(682,665,300,150,'AMERICAS','Rikers by 2032','MAMDANI PLANS FOUR SMALLER JAILS, FEWER INMATES.','jail'),
(42,835,300,125,'AMERICAS','BUKELE SEEKS 3RD TERM','EL SALVADOR VOTE COULD EXTEND RULE TO 2033.','ballot'),
(362,835,300,125,'SCIENCE / CLAIM','RIEMANN PROOF?','ANTHROPIC MATHEMATICIAN RELEASES LEAN CODE, NOT YET VERIFIED.','prime')]
for p in panels: panel(*p)
panel(682,835,300,125,'EUROPE/SECURITY','DENMARK ACCUSES RUSSIA OF PLOT','DENMARK SAYS MOSCOW PLOTTED TO KILL A US-UKRAINIAN RAPPER.','target')
line(42,978,982,978,RED,3); text(48,987,'21 NOVEMBER 2026 - THE WORLD IN ONE IMAGE',2,GRAY)
def png_bytes():
    raw=b''.join(b'\0'+bytes(sum(([r,g,b] for (r,g,b) in row),[])) for row in pix)
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
out=os.environ.get('MAKEFUN_OUTPUT_DIR','/output'); os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'entry.png'),'wb') as f:f.write(png_bytes())
