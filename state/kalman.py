##############################################################################
##############################################################################
# Example code for
# quasi-Newton particle Metropolis-Hastings
# for a linear Gaussian state space model
#
# Please cite:
#
# J. Dahlin, F. Lindsten, T. B. Sch\"{o}n
# "Quasi-Newton particle Metropolis-Hastings"
# Proceedings of the 17th IFAC Symposium on System Identification,
# Beijing, China, October 2015.
#
# (c) 2015 Johan Dahlin
# johan.dahlin (at) liu.se
#
# Distributed under the MIT license.
#
##############################################################################
##############################################################################

import numpy as np

##############################################################################
# Main class
##############################################################################

class kalmanMethods(object):
    ##########################################################################
    # Initalisation
    ##########################################################################

    # Initial state for the particles
    Po               = None;
    xo               = None;

    ##########################################################################
    # Kalman filter
    ##########################################################################
    def kf(self,sys):

        #=====================================================================
        # Initialisation
        #=====================================================================

        # Check settings and apply defaults otherwise
        self.xo = 0.0;
        self.Po = 1e-5;


        self.filterType = "kf";

        # Initialise variables for the filter
        S       = np.zeros((sys.T,1));
        K       = np.zeros((sys.T,));
        xhatp   = np.zeros((sys.T+1,1));
        xhatf   = np.zeros((sys.T,1));
        yhatp   = np.zeros((sys.T,1));
        Pf      = np.zeros((sys.T,1));
        Pp      = np.zeros((sys.T+1,1));
        ll      = np.zeros(sys.T);

        self.m  = sys.par[0];
        self.A  = sys.par[1];
        self.C  = 1.0;
        self.Q  = sys.par[2]**2;
        self.q  = sys.par[2];
        self.R  = sys.par[3]**2;
        self.r  = sys.par[3];

        # Set initial covariance and state
        Pp[0]     = self.Po;
        xhatp[0]  = self.xo;

        #=====================================================================
        # Run main loop
        #=====================================================================

        for tt in range(0, sys.T):

            # Calculate the Kalman Gain
            S[tt] = self.C * Pp[tt] * self.C + self.R;
            K[tt] = Pp[tt] * self.C / S[tt];

            # Compute the state estimate
            yhatp[tt]   = self.C * xhatp[tt];
            xhatf[tt]   = xhatp[tt] + K[tt] * ( sys.y[tt] - yhatp[tt] );
            xhatp[tt+1] = self.A * xhatf[tt] + self.m * ( 1.0 - self.A ) + sys.u[tt];

            # Update covariance
            Pf[tt]      = Pp[tt] - K[tt] * S[tt] * K[tt];
            Pp[tt+1]    = self.A * Pf[tt] * self.A + self.Q;

            # Estimate loglikelihood
            ll[tt]      = -0.5 * np.log(2.0 * np.pi * S[tt]) - 0.5 * ( sys.y[tt] - yhatp[tt] ) * ( sys.y[tt] - yhatp[tt] ) / S[tt];

        #=====================================================================
        # Compile output
        #=====================================================================

        self.ll    = np.sum(ll);
        self.llt   = ll;
        self.xhatf = xhatf;
        self.xhatp = xhatp;
        self.K     = K;
        self.Pp    = Pp;
        self.Pf    = Pf;

    ##########################################################################
    # RTS smoother
    ##########################################################################

    def rts(self,sys):

        #=====================================================================
        # Initialisation
        #=====================================================================
        self.smootherType    = "rts"

        # Run the preliminary Kalman filter
        self.kf(sys);

        # Initalise variables
        J       = np.zeros((sys.T,1));
        M       = np.zeros((sys.T,1));
        xhats   = np.zeros((sys.T,1));
        Ps      = np.zeros((sys.T,1));

        # Set last smoothing covariance and state estimate to the filter solutions
        Ps[sys.T-1]     = self.Pf[sys.T-1];
        xhats[sys.T-1]  = self.xhatf[sys.T-1];

        #=====================================================================
        # Run main loop
        #=====================================================================

        for tt in range((sys.T-2),0,-1):
            J[tt]       = self.Pf[tt] * self.A / self.Pp[tt+1]
            xhats[tt]   = self.xhatf[tt] + J[tt] * ( xhats[tt+1] - self.xhatp[tt+1] )
            Ps[tt]      = self.Pf[tt] + J[tt] * ( Ps[tt+1] - self.Pp[tt+1] ) * J[tt];

        #=====================================================================
        # Calculate the M-matrix (Smoothing covariance between states at t and t+1)
        #=====================================================================

        M[sys.T-1]  = ( 1 - self.K[sys.T-1] ) * self.A * self.Pf[sys.T-1];
        for tt in range((sys.T-2),0,-1):
            M[tt]   = self.Pf[tt] * J[tt-1] + J[tt-1] * ( M[tt+1] - self.A * self.Pf[tt] ) * J[tt-1];

        #=====================================================================
        # Gradient estimation
        #=====================================================================

        gradient = np.zeros((4,sys.T));

        for tt in range(1,sys.T):
            kappa = xhats[tt]   * sys.y[tt];
            eta   = xhats[tt]   * xhats[tt]   + Ps[tt];
            eta1  = xhats[tt-1] * xhats[tt-1] + Ps[tt-1];
            psi   = xhats[tt-1] * xhats[tt]   + M[tt];

            px = xhats[tt] - self.m - self.A * ( xhats[tt-1] - self.m ) + sys.u[tt];
            Q1 = self.q**(-1)
            Q2 = self.q**(-2)
            Q3 = self.q**(-3)

            gradient[0,tt] = Q2 * px * ( 1.0 - self.A );
            gradient[1,tt] = Q2 * ( psi - self.m * xhats[tt-1] * ( 1.0 - self.A ) - self.A * eta1 ) - Q2 * self.m * px;
            gradient[2,tt] = Q3 * ( eta - 2.0 * self.A * psi + self.A**2 * eta1 - 2.0*(xhats[tt]-self.A*xhats[tt-1])*self.m*(1.0-self.A) + self.m**2 * (1.0-self.A)**2 ) - Q1;
            gradient[3,tt] = self.r**(-3) * ( sys.y[tt]**2 - 2 * kappa + eta ) - self.r**(-1);

            # Estimate the gradient
            gradient0 = np.sum(gradient[0:sys.nParInference,:], axis=1);

        # Add the log-prior derivatives
        for nn in range(0,sys.nParInference):
            gradient0[nn]     = sys.dprior1(nn) + gradient0[nn];

        #=====================================================================
        # Compile output
        #=====================================================================

        self.Ps        = Ps;
        self.xhats     = xhats;

        self.gradient  = gradient0[0:sys.nParInference];
        self.gradient1 = gradient[0:sys.nParInference,:];

##############################################################################
##############################################################################
# End of file
##############################################################################
##############################################################################
