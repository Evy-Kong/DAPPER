# Reproduce results from
# table1 of sakov et al "iEnKF" (2012)

from common import *

from mods.L3.fundamentals import step

m = 3
p = m

#T = 4**6
T = 4**4
t = Chronology(0.01,dkObs=25,T=T,BurnIn=4)

m = 3
f = {
    'm': m,
    'model': lambda x,t,dt: step(x,t,dt),
    'noise': 0
    }

mu0 = array([1.509, -1.531, 25.46])
X0 = GaussRV(C=2,mu=mu0)

h = {
    'm': p,
    'model': lambda x,t: x,
    'noise': GaussRV(C=2,m=p)
    }

other = {'name': os.path.relpath(__file__,'mods/')}

params = OSSE(f,h,t,X0,**other)

####################
# Suggested tuning
####################

# rmse_a = ? (sak: 0.82)
#cfg.N       = 3
#cfg.infl    = 1.30 # Not well-tuned coz resuls too variable
#cfg.AMethod = 'Sqrt'
#cfg.rot     = False
#method      = EnKF

# rmse_a = 0.63 (sak 0.65)
#cfg.N       = 10
#cfg.infl    = 1.02
#cfg.AMethod = 'Sqrt'
#cfg.rot     = True
#method      = EnKF
#cfg.iMax    = 10
#method      = iEnKF # rmse_a = 0.31