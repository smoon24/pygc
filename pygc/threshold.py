"""
================================================
Description | LP threshold in TIGRESS simulation
Author      | Sanghyuk Moon
================================================
"""

from pyathena.classic.cooling import coolftn
import numpy as np
from astropy import constants as ac
from astropy import units as au
from scipy.optimize import bisect
from scipy.interpolate import interp1d

muH = 1.4271

class LPthres(coolftn):
    """
    Functions related to the Larson-Penston threshold
    """
    def __init__(self):
        # wrap classic.cooling and define interpolation functions
        super().__init__()
        self.coolft=interp1d(self.temp, self.cool)
        self.heatft=interp1d(self.temp, self.heat)
        self.muft=interp1d(self.temp, self.temp/self.T1)

    def get_Teq(self, heat_ratio, nH):
        """
        Calculate equilibrium temperature at given density and heating ratio.
        heat_ratio = (FUV heating rate) / (solar neighborhood FUV heating rate)
        """
        try:
            Teq = bisect(lambda x: heat_ratio*self.heatft(x)/nH - self.coolft(x)
                    ,12.95,1e7)
        except ValueError:
            Teq = np.nan
        return Teq

    def get_prs(self, nH, T):
        """
        Calculate pressure from density and temperature
        """
        prs = nH*muH/self.muft(T)*T
        return prs

    def get_rhoLP(self, dx, cs2, asnH=True):
        """
        Calculate LP threshold density
        """
        if isinstance(dx, au.quantity.Quantity):
            dx = dx.to('pc')
        else:
            dx = dx * au.pc
        if isinstance(cs2, au.quantity.Quantity):
            cs2 = cs2.to('km**2 s**-2')
        else:
            cs2 = cs2 * (au.km/au.s)**2
        rhoLP = 8.86/np.pi*cs2/ac.G/dx**2
        if asnH:
            rhoLP = (rhoLP/muH/ac.m_p).to('cm**-3').value
        else:
            rhoLP = rhoLP.to('Msun pc**-3').value
        return rhoLP

    def get_rhoLPeq(self, dx, Teq, asnH=True):
        """
        Caculate LP threshold density from given temperature,
        assuming thermal equilibrium
        """
        if isinstance(dx, au.quantity.Quantity):
            dx = dx.to('pc')
        else:
            dx = dx * au.pc
        if isinstance(Teq, au.quantity.Quantity):
            Teq = Teq.to('K')
        else:
            Teq = Teq * au.K
        cs2=ac.k_B*Teq/self.muft(Teq)/ac.m_p
        return self.get_rhoLP(dx, cs2, asnH=asnH)

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    lp = LPthres()

    heat_ratios = [1e0,1e1,1e2,1e3]
    dxs = [8*au.pc, 4*au.pc, 2*au.pc]
    N=1000
    nH = np.logspace(-1,5,N)

    Teqs = [[],[],[],[]]
    for Teq, heat_ratio in zip(Teqs, heat_ratios):
        for _nH in nH:
            Teq.append(lp.get_Teq(heat_ratio, _nH))
    Teq = np.array(Teqs)
    Peq = lp.get_prs(nH, Teq)

    plt.figure(figsize=(14,6))

    # plot n-P equilibrium curve
    plt.subplot(121)
    for i, heat_ratio in enumerate(heat_ratios):
        plt.loglog(nH, Peq[i], 'k-')
    plt.loglog(nH,lp.get_prs(nH, 184),'k:')

    plt.xlim(1e-1,1e5)
    plt.ylim(1e3,1e7)
    plt.xlabel(r'$n_{\rm H}\,[{\rm cm}^{-3}]$')
    plt.ylabel(r'$P/k_{\rm B}\,[{\rm K\,cm^{-3}}]$')
#    plt.text(5e1, 2e4, r"$\Gamma=\Gamma_0=2\times 10^{-26}\,{\rm erg\,s^{-1}}$",
#            fontsize=13, rotation=37)
#    plt.text(5e2, 8e4, r"$\Gamma=10\Gamma_0$", fontsize=13, rotation=40)
#    plt.text(3e3, 7e5, r"$\Gamma=10^2\Gamma_0$", fontsize=13, rotation=38)
#    plt.text(0.8e2, 3.3e6, r"$\Gamma=10^3\Gamma_0$", fontsize=13, rotation=48)
#    plt.text(0.8e1, 0.8e4, r"$T=184\,{\rm K}$", fontsize=13, rotation=52)

    # plot n-T equilibrium curve
    plt.subplot(122)
    for i, heat_ratio in enumerate(heat_ratios):
        plt.loglog(nH, Teq[i], 'k-')
    plt.loglog(nH,184*np.ones(len(nH)),'k:')

    # plot density threshold on n-T plane
    T = np.logspace(np.log10(12.95), 5)
    for dx in dxs:
        nth = lp.get_rhoLPeq(dx, T)
        plt.loglog(nth, T, 'k--')

    plt.xlim(1e-1,1e5)
    plt.ylim(1e1,1e5)
    plt.xlabel(r'$n_{\rm H}\,[{\rm cm}^{-3}]$')
    plt.ylabel(r'$T\,[{\rm K}]$')
    plt.text(3e3, 3e3, r"$\Delta x=8\,{\rm pc}$", fontsize=13, rotation=51)
    plt.text(6e3, 1.6e3, r"$\Delta x=4\,{\rm pc}$", fontsize=13, rotation=51)
    plt.text(1.2e4, 0.8e3, r"$\Delta x=2\,{\rm pc}$", fontsize=13, rotation=51)
    labels=[r"$\Gamma/\Gamma_0=1$",r"$\Gamma/\Gamma_0=10$",
            r"$\Gamma/\Gamma_0=10^2$",r"$\Gamma/\Gamma_0=10^3$"]
    plt.tight_layout()
    plt.show()
#    fig.savefig("phase.pdf",bbox_inches='tight')
