# NOTEVIEW - note reader for TI-84 Plus CE Python
# Needs NOTEIDX.py + N*.py files made by the converter.
#
# Menu:   up/down select, enter/right open, clear quit
# Reader: up/down scroll, left/right page,
#         enter next page, clear back

W=31  # screen columns used
H=8   # text rows per screen

UP=1
DN=2
LF=3
RT=4
OK=5
BK=6

try:
  from ti_system import wait_key
  KEYS=1
except:
  KEYS=0

try:
  from ti_system import disp_clr
except:
  def disp_clr():
    print("\n"*12)

# TI-OS key codes returned by wait_key()
KMAP={3:UP,4:DN,2:LF,1:RT,5:OK,9:BK,10:BK}
# typed commands when wait_key() is missing
TMAP={"8":UP,"2":DN,"4":LF,"6":RT,"":OK,"0":BK,"q":BK}

def getk():
  while 1:
    if KEYS:
      k=KMAP.get(wait_key())
    else:
      k=TMAP.get(input("8/2/4/6 move,0 back:").strip())
    if k:
      return k

def imp(n):
  try:
    try:
      return __import__(n)
    except NameError:
      g={}
      exec("import "+n,g)
      return g[n]
  except:
    return None

def forget(n):
  try:
    import sys
    del sys.modules[n]
  except:
    pass
  try:
    import gc
    gc.collect()
  except:
    pass

def foot(s):
  print(s[:W],end="")

def reader(e,C):
  t=e[0]
  nid=e[1]
  n=e[2]
  top=0
  cache={}
  while 1:
    need={}
    for i in range(top,min(top+H,n)):
      need[i//C]=1
    for c in list(cache):
      if c not in need:
        del cache[c]
    for c in need:
      if c not in cache:
        nm="N%03d%02d"%(nid,c)
        m=imp(nm)
        cache[c]=m.L if m else ()
        forget(nm)
    disp_clr()
    print(t[:W])
    for i in range(top,top+H):
      s=""
      if i<n:
        L=cache[i//C]
        j=i%C
        if j<len(L):
          s=L[j]
        else:
          s="?missing file N%03d%02d"%(nid,i//C)
      print(s[:W])
    if n:
      p="%d-%d/%d"%(top+1,min(top+H,n),n)
    else:
      p="(empty)"
    foot(p+"  clear:back")
    k=getk()
    if k==BK:
      return
    if k==DN:
      top+=1
    elif k==UP:
      top-=1
    elif k==RT or k==OK:
      top+=H
    elif k==LF:
      top-=H
    if top>n-H:
      top=n-H
    if top<0:
      top=0

def main():
  x=imp("NOTEIDX")
  if not x:
    disp_clr()
    print("No notes found.")
    print("Send NOTEIDX.py and the")
    print("N*.py files made by the")
    print("converter, then run again.")
    return
  N=x.N
  C=x.C
  forget("NOTEIDX")
  sel=0
  top=0
  while 1:
    disp_clr()
    print("NOTES (%d)"%len(N))
    for i in range(top,top+H):
      s=""
      if i<len(N):
        s=("> " if i==sel else "  ")+N[i][0]
      print(s[:W])
    foot("enter:open  clear:quit")
    k=getk()
    if k==BK:
      disp_clr()
      return
    if not N:
      continue
    if k==DN:
      sel=(sel+1)%len(N)
    elif k==UP:
      sel=(sel-1)%len(N)
    elif k==OK or k==RT:
      reader(N[sel],C)
    if sel<top:
      top=sel
    if sel>=top+H:
      top=sel-H+1

main()
