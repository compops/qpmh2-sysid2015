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

#=============================================================================
# Model structure
#=============================================================================
# xtt = par[0] + par[1] * ( xt - par[0] ) + par[2] * vt,
# yt  = xt + par[3] * et.
#
# vt  ~ N(0,1)
# et  ~ N(0,1)

import numpy          as     np
from   scipy.stats    import norm
from   models_helpers import *
from   models_dists   import *

class ssm(object):

    #=========================================================================
    # Define model settings
    #=========================================================================
    nPar          = 4;
    par           = np.zeros(nPar);
    modelName     = "Linear Gaussian system with four parameters"
    filePrefix    = "lgss";
    supportsFA    = True;
    nParInference = None;
    nQInference   = None;
    version       = "standard"

    #=========================================================================
    # Define the model
    #=========================================================================
    def generateInitialState( self, nPart ):
        return self.par[0] + np.random.normal(size=(1,nPart)) * self.par[2] / np.sqrt( 1 - self.par[1]**2 );

    def generateState(self, xt, tt):
        return self.par[0] + self.par[1] * ( xt - self.par[0] ) + self.par[2] * np.random.randn(1,len(xt));

    def evaluateState(self, xtt, xt, tt):
        return norm.pdf( xtt, self.par[0] + self.par[1] * ( xt - self.par[0] ), self.par[2] );

    def generateObservation(self, xt, tt):
        return xt + self.par[3] * np.random.randn(1,len(xt));

    def evaluateObservation(self, xt, tt):
        return norm.logpdf( self.y[tt], xt, self.par[3] );

    def generateStateFA(self, xt, tt):
        delta = self.par[2]**(-2) + self.par[3]**(-2); delta = 1.0 / delta;
        part1 = delta * ( self.y[tt+1] * self.par[3]**(-2) + self.par[2]**(-2) * ( self.par[0] + self.par[1] * ( xt - self.par[0] )  + self.u[tt] ) );
        part2 = np.sqrt(delta) * np.random.randn(1,len(xt));
        return part1 + part2;

    def evaluateStateFA(self, condPath, xt, tt):
        delta = self.par[2]**(-2) + self.par[3]**(-2); delta = 1.0 / delta;
        fa = delta * ( self.y[tt] * self.par[3]**(-2) + self.par[2]**(-2) * ( self.par[0] + self.par[1] * ( xt - self.par[0] )  + self.u[tt] ) );
        return norm.logpdf(condPath, fa, np.sqrt( delta ) );

    def generateObservationFA(self,xt, tt):
        return self.par[0] + self.par[1] * ( xt - self.par[0] ) + self.u[tt] + np.sqrt( self.par[2]**2 + self.par[3]**2 ) * np.random.randn(1,len(xt));

    def evaluateObservationFA(self, xt, tt, condPath=None):
        return norm.logpdf(self.y[tt+1], self.par[0] + self.par[1] * ( xt - self.par[0] ) + self.u[tt], np.sqrt( self.par[2]**2 + self.par[3]**2 ) );

    #=========================================================================
    # Define gradients of logarithm of complete data-likelihood
    #=========================================================================
    def Dparm(self, xtt, xt, st, at, tt):

        nOut = len(xtt);
        gradient = np.zeros(( nOut, self.nParInference ));
        Q1 = self.par[2]**(-1);
        Q2 = self.par[2]**(-2);
        Q3 = self.par[2]**(-3);
        R1 = self.par[3]**(-1);
        R3 = self.par[3]**(-3);
        px = xtt - self.par[0] - self.par[1] * ( xt - self.par[0] ) - self.u[tt-1];
        py = self.y[tt] - xt;

        for v1 in range(0,self.nParInference):
            if v1 == 0:
                gradient[:,v1] = ( 1.0 - self.par[1] ) * Q2 * px;
            elif v1 == 1:
                gradient[:,v1] = ( xt - self.par[0] ) * Q2 * px;
            elif v1 == 2:
                gradient[:,v1] = Q3 * px**2 - Q1
            elif v1 == 3:
                gradient[:,v1] = R3 * py**2 - R1;
            else:
                gradient[:,v1] = 0.0;

        return(gradient);

    #=========================================================================
    # Define Hessians of logarithm of complete data-likelihood
    #=========================================================================
    def DDparm(self, xtt, xt,  st, at, tt):
        nOut = len(xtt);
        hessian = np.zeros( (nOut, self.nParInference,self.nParInference) );
        return(hessian);

    #=========================================================================
    # Define hard priors for the PMH sampler
    #=========================================================================
    def priorUniform(self):
        out = 1.0;

        if( np.abs( self.par[1] ) > 1.0 ):
            out = 0.0;

        if( self.par[2] < 0.0 ):
            out = 0.0;

        if( self.par[3] < 0.0 ):
            out = 0.0;

        return( out );

    #=========================================================================
    # Define log-priors for the PMH sampler
    #=========================================================================
    def prior(self):
        out = 0.0;

        # Normal prior for mu
        out += normalLogPDF( self.par[0], 0, 0.2 );

        # Truncated normal prior for phi (truncation by hard prior)
        out += normalLogPDF( self.par[1], 0.9, 0.05 );

        # Gamma prior for sigmav
        out += gammaLogPDF( self.par[2], a=0.2, b=0.2 );

        # Gamma prior for sigmae
        out += gammaLogPDF( self.par[3], a=2.0, b=2.0 )

        return( out );

    #=========================================================================
    # Define gradients of log-priors for the PMH sampler
    #=========================================================================
    def dprior1(self,v1):

        if ( v1 == 0 ):
            # Normal prior for mu
            return normalLogPDFgradient( self.par[0], 0, 0.2 );
        elif ( v1 == 1):
            # Truncated normal prior for phi (truncation by hard prior)
            return normalLogPDFgradient( self.par[1], 0.9, 0.05 );
        elif ( v1 == 2):
            # Gamma prior for sigmav
            return gammaLogPDFgradient( self.par[2], a=0.2, b=0.2 );
        elif ( v1 == 3):
            # Gamma prior for sigmae
            return gammaLogPDFgradient( self.par[3], a=2.0, b=2.0 )
        else:
            return 0.0;

    #=========================================================================
    # Define standard methods for the model struct
    #=========================================================================

    # Standard operations on struct
    copyData                = template_copyData;
    storeParameters         = template_storeParameters;
    returnParameters        = template_returnParameters

    # Standard data generation for this model
    generateData            = template_generateData;

    # No tranformations available
    transform               = empty_transform;
    invTransform            = empty_invTransform;
    Jacobian                = empty_Jacobian;

    # No EM algorithm available for this model
    Qfunc                   = empty_Qfunc;
    Mstep                   = empty_Mstep;

    ddprior1                = empty_ddprior1

##############################################################################
##############################################################################
# End of file
##############################################################################
##############################################################################