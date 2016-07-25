# TODO: Do something about figure/subplot/graphic handles
# TODO: obs plotting

from common import *

from mpl_toolkits.mplot3d.art3d import juggle_axes

class LivePlot:
  def __init__(self,params,E,stats,xx,yy):
    N,m = E.shape
    dt = params.t.dt
    ii  = range(m)

    self.stats  = stats
    self.xx     = xx
    self.yy     = yy

    self.is_on  = False
    print('Press <Enter> to toggle live plot')

    #ens_props = {} # yields rainbow
    ens_props = {'color': 0.6*cwhite} # 0.7*cblue

    self.fg = plt.figure(21,figsize=(8,8))
    self.fg.clf()
    set_figpos('E (mac)')

    self.ax  = plt.subplot(211)
    self.lmu,= plt.plot(ii,stats.mu[0,:],'b',lw=2,ls='-',label='Ens.mean'  )
    self.lx ,= plt.plot(ii,xx[0      ,:],'k',lw=3,ls='-',label='Truth')

    #lE  = plt.plot(ii,E.T,lw=1,*ens_props)
    self.ks  = 3.0
    self.CI  = self.ax.fill_between(ii, \
        stats.mu[0,:] - self.ks*sqrt(stats.var[0,:]), \
        stats.mu[0,:] + self.ks*sqrt(stats.var[0,:]), \
        alpha=0.4,label=(str(self.ks) + ' sigma'))

    if hasattr(params.h,'plot'):
      self.yplot = params.h.plot
      self.obs = params.h.plot(yy[0,:])
      self.obs.set_label('Obs')
      self.obs.set_visible('off')

    self.ax.legend()
    self.ax.set_xlabel('State index')

    ax2 = plt.subplot(212)
    A   = anom(E)[0]
    # TODO: Very wasteful (e.g. LA: m=1000)
    # Do as Sakov, and use fft?
    self.ews, = ax2.plot(sqrt(np.maximum(0,eigh(A @ A.T)[0][-min(N-1,m):])))
    ax2.set_xlabel('Sing. value index')
    ax2.set_yscale('log')
    ax2.set_ylim([1e-3,1e1])

    
    fg3 = plt.figure(23,figsize=(8,6))
    fg3.clf()
    set_figpos('NE (mac)')

    ax3      = fg3.add_subplot(111,projection='3d')
    self.sx  = ax3.scatter(*xx[0,:3]  ,s=300,c='y',marker=(5, 1))
    self.sE  = ax3.scatter(*E[: ,:3].T,s=10,**ens_props)

    tail_k       = max([2,int(1/dt)])
    self.tail_xx = ones((tail_k,3)) * xx[0,:3] # init
    self.ltx,    = ax3.plot(*self.tail_xx.T,'b',lw=4)

    self.tail_E  = zeros((tail_k,N,3))
    for k in range(tail_k):
      self.tail_E[k,:,:] = E[:,:3]
    self.ltE = []
    for n in range(N):
      lEn, = ax3.plot(*self.tail_E[:,n,:].squeeze().T,**ens_props)
      self.ltE.append(lEn)

    #ax3.axis('off')
    for i in range(3):
      set_ilim(ax3,i,xx,1.7)

    plt.pause(0.01)


  def update(self,E,k,kObs):

    if heardEnter():
      self.is_on = not self.is_on
    if not self.is_on:
      return

    N,m = E.shape
    ii  = range(m)
    stats = self.stats
    
    fg2 = plt.figure(21)
    self.lmu.set_ydata(stats.mu[k,:])
    self.lx .set_ydata(self.xx[k,:])

    #for i,l in enumerate(lE):
      #l.set_ydata(E[i,:])
    self.CI.remove()
    self.CI  = self.ax.fill_between(ii, \
        stats.mu[k,:] - self.ks*sqrt(stats.var[k,:]), \
        stats.mu[k,:] + self.ks*sqrt(stats.var[k,:]), alpha=0.4)

    plt.sca(self.ax)
    if hasattr(self,'obs'):
      try:
        self.obs.remove()
      except Exception:
        pass
      if kObs is not None:
        self.obs = self.yplot(self.yy[kObs,:])

    plt.pause(0.01)

    A = anom(E)[0]
    self.ews.set_ydata(sqrt(np.maximum(0,eigh(A @ A.T)[0][-min(N-1,m):])))

    fg3 = plt.figure(23)
    self.sx._offsets3d = juggle_axes(*vec2list2(self.xx[k,:3]),'z')
    self.sE._offsets3d = juggle_axes(*E[:,:3].T,'z')

    self.tail_xx = np.roll(self.tail_xx,1,axis=0)
    self.tail_xx[0,:] = self.xx[k,:3]
    self.ltx.set_data(self.tail_xx[:,0],self.tail_xx[:,1])
    self.ltx.set_3d_properties(self.tail_xx[:,2])

    self.tail_E = np.roll(self.tail_E,1,axis=0)
    self.tail_E[0,:,:] = E[:,:3]
    for n in range(N):
      self.ltE[n].set_data(self.tail_E[:,n,0],self.tail_E[:,n,1])
      self.ltE[n].set_3d_properties(self.tail_E[:,n,2])

    plt.pause(0.01)
    #input("Press Enter to continue...")
    #fg3.savefig('figs/l63_' + str(k) + '.png',format='png',dpi=70)
    


def set_ilim(ax,i,data,zoom=1.0):
  Min  = np.min(data[:,i])
  Max  = np.max(data[:,i])
  lims = round2sigfig([Min, Max])
  lims = inflate_ens(lims,1/zoom)
  if i is 0: ax.set_xlim(lims)
  if i is 1: ax.set_ylim(lims)
  if i is 2: ax.set_zlim(lims)


def estimate_good_plot_length(xx,chrono):
  L = estimate_corr_length(xx)
  if L is not 0:
    K = round2sigfig(100*L,2)
  else:
    K = chrono.K/10
  K = max(K,chrono.dtObs)
  return K

def get_plot_inds(chrono,Kplot,Tplot,xx):
  if Kplot is None:
    if Tplot:
      Kplot = find_1st_ind(chrono.tt >= Tplot)
    else:
      Kplot = estimate_good_plot_length(xx,chrono)
  kkObs  = chrono.kkObs
  plot_kk    = chrono.kk[chrono.kk<=Kplot]
  plot_kkObs = kkObs[kkObs<=Kplot]
  return plot_kk, plot_kkObs


def plot_3D_trajectory(xx,stats,chrono,\
    Kplot=None,Tplot=None):
  """ xx: array with (exactly) 3 columns."""
  s = stats

  plt.figure(14).clf()
  set_figpos('SE')

  kk = get_plot_inds(chrono,Kplot,Tplot,xx.ravel(order='F'))[0]

  ax3 = plt.subplot(111, projection='3d')
  ax3.plot   (xx[kk    ,0],xx[kk    ,1],xx[kk    ,2],c='k',label='Truth'   )
  ax3.plot   (s.mu[kk  ,0],s.mu[kk  ,1],s.mu[kk  ,2],c='b',label='Ens.mean')
  ax3.scatter(xx[0     ,0],xx[0     ,1],xx[0     ,2],s=40 ,c='g'           )
  ax3.scatter(xx[kk[-1],0],xx[kk[-1],1],xx[kk[-1],2],s=40 ,c='r'           )
  ax3.legend()


def plot_diagnostics_dashboard(xx,stats,chrono,N, \
    dim=0,Kplot=None,Tplot=None):
  s  = stats

  fg = plt.figure(12,figsize=(8,8)).clf()
  set_figpos('NE')

  pkk,pkkObs = get_plot_inds(chrono,Kplot,Tplot,xx[:,dim])
  tt = chrono.tt

  ax_d = plt.subplot(4,1,1)
  ax_d.plot(tt[pkk],xx[pkk  ,dim],'k',lw=2,        label='Truth')
  ax_d.plot(tt[pkk],s.mu[pkk,dim],'g',lw=1,ls='--',label='DA estim.')
  ax_d.set_ylabel('$x_{' + str(dim) + '}$',usetex=True,size=20)
  ax_d.legend()

  ax_e = plt.subplot(4,1,2)
  ax_e.plot(tt[pkk], s.rmse[pkk],'k',lw=2)
  ax_e.fill_between(tt[pkk], s.rmsv[pkk],alpha=0.4)
  ax_e.set_ylim(0,np.percentile(s.rmse[pkk],99))
  ax_e.set_ylabel('RMS Err and Var')

  if not all(s.trHK[:] == 0):
    ax_K = plt.subplot(4,1,3)
    ax_K.plot(tt[pkkObs], s.trHK[:len(pkkObs)],'k',lw=2)
    ax_K.set_ylim(0,np.percentile(s.trHK[:len(pkkObs)],99.6))
    ax_K.set_ylabel('trace(K)')
    ax_K.set_xlabel('time (t)')

  if not all(s.rh[-1,:] == 0):
    ax_H = plt.subplot(4,1,4)
    integer_hist(s.rh[chrono.kkBI,:].ravel(),N,alpha=0.5)


def integer_hist(E,N,**kwargs):
  """Histogram for integers."""
  ax = plt.gca()
  ax.hist(E,bins=N+1,range=(-0.5,N+0.5),normed=1,**kwargs)
  ax.set_xlim(np.min(E)-0.5,np.max(E)+0.5)



def set_figpos(case):
  if 'Qt4Agg' is not matplotlib.get_backend():
    return
  fmw = plt.get_current_fig_manager().window
  w = fmw.width()
  h = fmw.height()
  x = fmw.x()
  y = fmw.y()
  if 'mac' in case:
    if case.startswith('NE'):
      fmw.setGeometry(640, 45, 640, 365)
    elif case.startswith('SE'):
      fmw.setGeometry(640, 431, 640, 365)
    elif case.startswith('E '):
      fmw.setGeometry(640, 45, 640, 751)
    else:
      sys.exit('Position not defined')
  else:
    if case.startswith('NE'):
      Cx = 1922
      Cy = -720
      w = 700
      h = 900
      fmw.setGeometry(Cx-w,Cy-h,w,h) # x,y,w,h
    elif case.startswith('SE'):
      Cx = 1922
      Cy = 0
      h = 500
      w = 700
      fmw.setGeometry(Cx-w,Cy-h,w,h)
    elif case.startswith('E '):
      fmw.setGeometry(642, -1418, 716, 1418)
    else:
      sys.exit('Position not defined')
  

@atmost_2d
def plt_vbars(xx,y1y2=None,*kargs,**kwargs):
  if y1y2 == None:
    y1y2 = plt.ylim()
  yy = np.tile(asmatrix(y1y2).ravel().T,(1,len(xx)))
  xx = np.tile(xx,(2,1))
  plt.plot(xx,yy,*kargs,**kwargs)

@atmost_2d
def plt_hbars(yy,x1x2=None,*kargs,**kwargs):
  if x1x2 == None:
    x1x2 = plt.xlim()
  xx = np.tile(asmatrix(x1x2).ravel().T,(1,len(yy)))
  yy = np.tile(yy,(2,1))
  plt.plot(xx,yy,*kargs,**kwargs)
