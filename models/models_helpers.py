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

import numpy as np;

#=============================================================================
# Copy data from an instance of this struct to another
#=============================================================================
def template_copyData(model,sys):
    model.T             = np.copy( sys.T )
    model.y             = np.copy( sys.y )
    model.u             = np.copy( sys.u )
    model.nPar          = np.copy( sys.nPar )
    model.filePrefix    = sys.filePrefix

    # Check if nQInference and nParInference are set and use default otherwise
    if ( model.nQInference == None ):
        model.nQInference = np.int( 0 );
        print("model: assuming that Q-function should not be estimated for this model.");

    if ( model.nParInference == None ):
        model.nParInference = np.int( 2 );
        print("model: assuming that " + str(model.nParInference) + " parameters should be inferred.");

    # Copy parameters
    model.par = np.zeros(sys.nPar);
    for kk in range(0,sys.nPar):
        model.par[kk] = np.array(sys.par[kk], copy=True)

#=============================================================================
# Store the parameters into the struct
#=============================================================================
def template_storeParameters(model,newParm,sys):
    model.par = np.zeros(sys.nPar);

    for kk in range(0,model.nParInference):
        model.par[kk] = np.array(newParm[kk], copy=True)

    for kk in range(model.nParInference,sys.nPar):
        model.par[kk] = sys.par[kk];

#=============================================================================
# Returns the current parameters stored in this struct
#=============================================================================
def template_returnParameters(model):
    out = np.zeros(model.nParInference);

    for kk in range(0,model.nParInference):
        out[kk]  = model.par[kk];
    return(out);

#=============================================================================
# Templates if no transforms are used for the model
#=============================================================================
def empty_transform(model):
    return 0.0;

def empty_invTransform(model):
    return 0.0;

def empty_Jacobian(model):
    return 0.0;

#=============================================================================
# Templates if Q-funcations are not calculated for the model
#=============================================================================
def empty_Qfunc(model, xtt, xt, st, at, tt):
    raise NameError("No Q-function calculated for this model, cannot use the EM algorithm.");

def empty_Mstep(model, qfunc):
    raise NameError("No Q-function calculated for this model, cannot use the EM algorithm.");

#=============================================================================
# Templates if faPF cannot be used for this model
#=============================================================================
def empty_generateStateFA(model, xt, tt):
    raise NameError("faPF cannot be used for this model.");

def empty_evaluateObservationFA(model, xt, tt):
    raise NameError("faPF cannot be used for this model.");

def empty_generateObservationFA(model, xt, tt):
    raise NameError("faPF cannot be used for this model.");

#=============================================================================
# Templates for simple prior structure
#=============================================================================
def empty_priorUniform(model):
    return(1.0);

def empty_prior(model):
    return(0.0);

def empty_dprior1(model, v1):
    return(0.0);

def empty_ddprior1(model, v1, v2):
    return(0.0);

#=============================================================================
# Standard template for generating data
#=============================================================================
def template_generateData(model,u=None,fileName=None,order=None):

    # Set input to zero if not given
    if ( u==None ):
        u = np.zeros(model.T);

    model.u       = u;
    model.x       = np.zeros((model.T+1,1));
    model.y       = np.zeros((model.T,1));
    model.x[0]    = model.xo;

    if (fileName == None):
        # No input file given so generate observations and states
        for tt in range(0, model.T):
            model.y[tt]   = model.generateObservation( model.x[tt],  tt);
            model.x[tt+1] = model.generateState(       model.x[tt],  tt);

        model.x  = model.x[0:model.T]
    else:
        # Try to import data
        tmp   = np.loadtxt(fileName,delimiter=",")

        if ( order == None ):
            model.y = np.array(tmp[0:model.T], copy=True).reshape((model.T,1));
            model.u = u;
        elif ( order == "y" ):
            model.y = np.array(tmp[0:model.T], copy=True).reshape((model.T,1));
            model.u = u;
        elif ( order == "xy" ):
            model.x = np.array(tmp[0:model.T,0], copy=True).reshape((model.T,1));
            model.y = np.array(tmp[0:model.T,1], copy=True).reshape((model.T,1));
            model.u = u;
        elif ( order == "xuy" ):
            model.x = np.array(tmp[0:model.T,0], copy=True).reshape((model.T,1));
            model.u = np.array(tmp[0:model.T,1], copy=True).reshape((model.T,1));
            model.y = np.array(tmp[0:model.T,2], copy=True).reshape((model.T,1));
        else:
            raise NameError("generateData, import data: cannot import that order.");

##############################################################################
##############################################################################
# End of file
##############################################################################
##############################################################################