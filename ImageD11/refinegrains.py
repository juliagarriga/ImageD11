# Automatically adapted for numpy.oldnumeric Sep 06, 2007 by alter_codepy


# ImageD11_v1.0.6 Software for beamline ID11
# Copyright (C) 2008  Jon Wright
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import numpy

from ImageD11 import transform, indexing, parameters
from ImageD11 import grain, columnfile, closest

import simplex

print __file__

class refinegrains:
    
    """ 
    Class to refine the position and orientation of grains
    and also the detector parameters
    """

    # Default parameters
    pars = {"cell__a" : 4.1569162,
        "cell__b" :  4.1569162,
        "cell__c" : 4.1569162,
        "cell_alpha" : 90.0,
        "cell_beta" : 90.0,
        "cell_gamma" : 90.0,
        "cell_lattice_[P,A,B,C,I,F,R]" : 'P',
        "chi" : 0.0,
        "distance" : 7367.8452302,
        "fit_tolerance" : 0.5,
        "o11" : 1,
        "o12" : 0,
        "o21" : 0,
        "o22" : 1,
        "omegasign" : 1,
        "t_x" : 33.0198146824,
        "t_y" : 14.6384893741,
        "t_z" : 0.0 ,
        "tilt_x" : 0.0,
        "tilt_y" : 0.0623952920101,
        "tilt_z" : 0.00995011461696,
        "wavelength" : 0.2646,
        "wedge" : 0.0,
        "y_center" : 732.950204632,
        "y_size" : 4.6,
        "z_center" : 517.007049626,
        "z_size" : 4.6 }

    # Default stepsizes for the 
    stepsizes = {
        "wavelength" : 0.001,
        'y_center'   : 0.2,
        'z_center'   : 0.2,
        'distance'   : 200.,
        'tilt_y'     : transform.radians(0.1),
        'tilt_z'     : transform.radians(0.1),
        'tilt_x'     : transform.radians(0.1),
        'wedge'      : transform.radians(0.1),
        'chi'        : transform.radians(0.1),
        't_x' : 0.2,
        't_y' : 0.2,
        't_z' : 0.2,
        }

    def __init__(self, tolerance = 0.01, intensity_tth_range = (6.1, 6.3) , 
                 OmFloat=True, OmSlop=0.25 ):
        """

        """
        self.OMEGA_FLOAT=OmFloat
        self.slop=OmSlop
        if self.OMEGA_FLOAT:
            print "Using",self.slop,"degree slop"
        else:
            print "Omega is used as observed"
        self.tolerance=tolerance
        # list of ubi matrices (1 for each grain in each scan)
        self.grainnames = []
        self.ubisread = {}
        self.translationsread = {}
        # list of scans and corresponding data
        self.scannames=[]
        self.scantitles={}
        self.scandata={}
        # grains in each scan
        self.grains = {}
        self.grains_to_refine = []
        # ?
        self.drlv = None
        self.parameterobj = parameters.parameters(**self.pars)
        self.intensity_tth_range = intensity_tth_range
        self.recompute_xlylzl = False
        for k,s in self.stepsizes.items():
            self.parameterobj.stepsizes[k]=s

    def loadparameters(self, filename):
        self.parameterobj.loadparameters(filename)
        
    def saveparameters(self, filename):
        self.parameterobj.saveparameters(filename)

    def readubis(self, filename):
        """
        Read ubi matrices from a text file
        """
        try:
            ul = grain.read_grain_file(filename)
        except:
            print filename, type(filename)
            raise
        for i, g in enumerate(ul):
            name = filename + "_" + str(i)
            # Hmmm .... multiple grain files?
            name = i
            self.grainnames.append(i)
            self.ubisread[name] = g.ubi
            self.translationsread[name] = g.translation
        #print "Grain names",self.grainnames

    def savegrains(self, filename, sort_npks=True):
        """
        Save the refined grains
        
        """
        ks = self.grains.keys()
        # sort by number of peaks indexed to write out
        if sort_npks:
            #        npks in x array
            gl = [ (self.grains[k].npks, self.grains[k],k) for k in ks ]
            gl.sort()
            gl = [ (g[1],g[2]) for g in gl[::-1] ]
        else:
            ks.sort()
            gl = [ (self.grains[k],k) for k in ks ]
        grain.write_grain_file(filename, [g[0] for g in gl])

        # Update the datafile and grain names reflect indices in grain list
        for g,k in gl:
            name, fltname = g.name.split(":")
            assert self.scandata.has_key(fltname),"Sorry - logical flaw"
            assert len(self.scandata.keys())==1,"Sorry - need to fix for multi data"
            self.set_translation(k[0],fltname)
            self.compute_gv( g , update_columns = True )
            numpy.put( self.scandata[fltname].gx, g.ind, self.gv[:,0] )
            numpy.put( self.scandata[fltname].gy, g.ind, self.gv[:,1] )
            numpy.put( self.scandata[fltname].gz, g.ind, self.gv[:,2] )
            hkl_real = numpy.dot(g.ubi, self.gv.T)
            numpy.put( self.scandata[fltname].hr, g.ind, hkl_real[0,:] )
            numpy.put( self.scandata[fltname].kr, g.ind, hkl_real[1,:] )
            numpy.put( self.scandata[fltname].lr, g.ind, hkl_real[2,:] )
            hkl = numpy.floor(hkl_real + 0.5)
            numpy.put( self.scandata[fltname].h, g.ind, hkl[0,:] )
            numpy.put( self.scandata[fltname].k, g.ind, hkl[1,:] )
            numpy.put( self.scandata[fltname].l, g.ind, hkl[2,:] )
            




    def makeuniq(self, symmetry):
        """
        Flip orientations to a particular choice
        
        Be aware that if the unit cell is distorted and you do this,
        you might have problems...
        """
        from ImageD11.sym_u import find_uniq_u, getgroup
        g = getgroup( symmetry )()
        for k  in self.ubisread.keys():
            self.ubisread[k] = find_uniq_u(self.ubisread[k], g)
        for k in self.grains.keys():
            self.grains[k].set_ubi( find_uniq_u(self.grains[k].ubi, g) )
            

    def loadfiltered(self, filename):
        """
        Read in file containing filtered and merged peak positions
        """
        col = columnfile.columnfile(filename)
        self.scannames.append(filename)
        self.scantitles[filename] = col.titles
        if not "drlv2" in col.titles:
            col.addcolumn( numpy.ones(col.nrows, numpy.float),
                           "drlv2" )
        if not "labels" in col.titles:
            col.addcolumn( numpy.ones(col.nrows, numpy.float)-2,
                           "labels" )
        if not "sc" in col.titles:
            assert "xc" in col.titles
            col.addcolumn( col.xc.copy(), "sc")
        if not "fc" in col.titles:
            assert "yc" in col.titles
            col.addcolumn( col.yc.copy(), "fc")
        self.scandata[filename] = col
        
        


    def generate_grains(self):
        t = numpy.array([ self.parameterobj.parameters[s]
                          for s in ['t_x', 't_y','t_z']] )
        for grainname in self.grainnames:
            for scanname in self.scannames:
                try:
                    gr = self.grains[(grainname,scanname)]
                except KeyError:
                    if self.translationsread[grainname] is None:
                        self.grains[(grainname,scanname)] = grain.grain(
                            self.ubisread[grainname], translation = t )
                        self.grains[(grainname,scanname)].name = \
                            (str(grainname)+":"+scanname).replace(" ","_")
                    else:
                        self.grains[(grainname,scanname)] = grain.grain(
                            self.ubisread[grainname],
                            translation = self.translationsread[grainname] )
                        self.grains[(grainname,scanname)].name = \
                            (str(grainname)+":"+scanname).replace(" ","_")
        for scanname in self.scannames:
            self.reset_labels(scanname)

    def reset_labels(self, scanname):
        print "resetting labels"
        try:
            x = self.scandata[scanname].xc
            y = self.scandata[scanname].yc
        except AttributeError:
            x = self.scandata[scanname].sc
            y = self.scandata[scanname].fc
        om = self.scandata[scanname].omega
        # only for this grain
        self.scandata[scanname].labels = self.scandata[scanname].labels*0 - 2 
        self.scandata[scanname].drlv2 = self.scandata[scanname].drlv2*0 + 1
        for g in self.grainnames:
            self.grains[(g,scanname)].x = x
            self.grains[(g,scanname)].y = y
            self.grains[(g,scanname)].om = om

            

    def compute_gv(self, thisgrain , update_columns = False  ):
        """
        Makes self.gv refer be g-vectors computed for this grain in this scan
        """
        peaks_xyz  = thisgrain.peaks_xyz
        om = thisgrain.om
        try:
            sign = self.parameterobj.parameters['omegasign']
        except:
            sign = 1.0
        # translation should match grain translation here...
        self.tth,self.eta = transform.compute_tth_eta_from_xyz( peaks_xyz,
                                      omega = om * sign,
                                      **self.parameterobj.parameters)
        
        gv = transform.compute_g_vectors(self.tth, self.eta, om*sign,
                                float(self.parameterobj.parameters['wavelength']),
                                self.parameterobj.parameters['wedge'],
                                self.parameterobj.parameters['chi'])
        # update tth_per_grain and eta_per_grain
        if update_columns:
            name = thisgrain.name.split(":")[1]
            numpy.put( self.scandata[name].tth_per_grain,  
                    thisgrain.ind,
                    self.tth)
            numpy.put( self.scandata[name].eta_per_grain ,
                    thisgrain.ind,  
                    self.eta)
                    
        if not self.OMEGA_FLOAT:
            self.gv = gv.T
        if self.OMEGA_FLOAT:
            mat = thisgrain.ubi.copy()
            junk = closest.score_and_refine(mat , gv.T,
                                            self.tolerance)
            hklf = numpy.dot( mat, gv )
            hkli = numpy.floor( hklf + 0.5 )
            
            gcalc = numpy.dot( numpy.linalg.inv(mat) , hkli ) 
            tth,[eta1,eta2],[omega1,omega2] = transform.uncompute_g_vectors(
                gcalc , float(self.parameterobj.parameters['wavelength']),
                self.parameterobj.parameters['wedge'],
                self.parameterobj.parameters['chi'])

            e1e = numpy.abs(eta1 - self.eta)
            e2e = numpy.abs(eta2 - self.eta)
            try:
                eta_err = numpy.array( [ e1e, e2e ] )
            except:
                print e1e.shape, e2e.shape, e1e
                
                raise
            
            best_fitting = numpy.argmin( eta_err, axis = 0 )

            # These are always 1 or zero
            # pick the right omega (confuddled by take here)
            omega_calc = best_fitting * omega2 + ( 1 - best_fitting ) * omega1
            # Take a weighted average within the omega error of the observed
            omerr = (om*sign - omega_calc)
            # print omerr[0:5]
            omega_calc = om*sign - numpy.clip( omerr, -self.slop , self.slop ) 
            # print omega_calc[0], om[0]


            # Now recompute with improved omegas... (tth, eta do not change much)
            #self.tth, self.eta = transform.compute_tth_eta(
            #    numpy.array([x, y]),
            #    omega = omega_calc, 
            #    **self.parameterobj.parameters)
            self.tth,self.eta = transform.compute_tth_eta_from_xyz( peaks_xyz,
                                                            omega = om * sign,
                                                **self.parameterobj.parameters)

            gv = transform.compute_g_vectors(self.tth, self.eta, omega_calc,
                        float(self.parameterobj.parameters['wavelength']),
                        self.parameterobj.parameters['wedge'],
                        self.parameterobj.parameters['chi'])
            self.gv = gv.T
        return


    def refine(self, ubi, quiet=True):
        """
        Fit the matrix without changing the peak assignments
        
        """
        mat=ubi.copy()
        # print "In refine",self.tolerance, self.gv.shape
        self.npks, self.avg_drlv2 = closest.score_and_refine(mat, self.gv, 
                                                             self.tolerance)
        if not quiet:
            import math
            try:
                print "%-8d %.6f"%(self.npks,math.sqrt(self.avg_drlv2))
            except:
                print self.npks,self.avg_drlv2, mat, self.gv.shape, self.tolerance
#                raise

        #print self.tolerance
#        self.npks, self.avg_drlv2 = closest.score_and_refine(mat, self.gv,
#                                                             self.tolerance)
        #tm = indexing.refine(ubi,self.gv,self.tolerance,quiet=quiet)
        #print ubi, tm,ubi-tm,mat-tm

        return mat

    def applyargs(self,args):
        self.parameterobj.set_variable_values(args)
        
    def printresult(self,arg):
        # print self.parameterobj.parameters
        # return
        for i in range(len(self.parameterobj.varylist)):
            item = self.parameterobj.varylist[i]
            value = arg[i]
            try:
                self.parameterobj.parameters[item]=value
                print item,value
            except:
                # Hopefully a crystal translation
                pass


    def gof(self,args):
        """
        <drlv> for all of the grains in all of the scans
        """
        self.applyargs(args)
        diffs = 0.
        contribs = 0.

        # defaulting to fitting all grains
        for key in self.grains_to_refine:

            g = self.grains[key]
            grainname = key[0]
            scanname = key[1]

            # Compute gv using current parameters
            # Keep labels fixed
            if self.recompute_xlylzl:
                
                g.peaks_xyz = transform.compute_xyz_lab([ g.sc, 
                                                          g.fc ],
                                                        **self.parameterobj.parameters)

            self.compute_gv( g )
            #print self.gv.shape
            #print self.gv[0:10,i:]

            # For stability, always start refining the read in one
            g.set_ubi( self.refine( self.ubisread[grainname] ) )
            #print self.npks,self.avg_drlv2 # number of peaks it got
            
            #print self.gv.shape
            

            diffs +=  self.npks*self.avg_drlv2
            contribs+= self.npks
        if contribs > 0:
            return 1e6*diffs/contribs
        else:
            print "No contribs???", self.grains_to_refine
            return 1e6


    def estimate_steps(self, gof, guess, steps):
        assert len(guess) == len(steps)
        cen = self.gof(guess)
        deriv = []
        print "Estimating step sizes"
        for i in range(len(steps)):
            print self.parameterobj.varylist[i],    
            newguess = [g for g in guess]
            newguess[i] = newguess[i] + steps[i]
            here = self.gof(newguess)
            print "npks, avgdrlv" ,  self.npks, self.avg_drlv2,
            deriv.append(here - cen)
            print "D_gof, d_par, dg/dp",here-cen, steps[i],here-cen/steps[i]
        # Make all match the one which has the biggest impact
        j = numpy.argmax(numpy.absolute(deriv))
        print "Max step size is on", self.parameterobj.varylist[j]
        inc  =  [ s * abs(deriv[j]) / abs(d) for d, s in zip(deriv, steps) ]
        print "steps",steps
        print "inc",inc
        return inc
    




    def fit(self, maxiters=100):
        """
        Fit the global parameters
        """
        self.assignlabels()
        guess = self.parameterobj.get_variable_values()
        inc = self.parameterobj.get_variable_stepsizes()
        names = self.parameterobj.varylist
        self.printresult(guess)
        self.grains_to_refine = self.grains.keys()
        self.recompute_xlylzl = False
        for n in names:
            if n not in ['t_x', 't_y', 't_z']:
                self.recompute_xlylzl = True
        inc = self.estimate_steps(self.gof, guess, inc)
        s=simplex.Simplex(self.gof, guess, inc)
        newguess,error,iter=s.minimize(maxiters=maxiters , monitor=1)
        print 
        print "names",names
        print "ng",newguess
        for p,v in zip(names,newguess):
            # record results
            self.parameterobj.set(p,v)    
            print "Setting parameter",p,v
        trans =["t_x","t_y","t_z"]
        for t in trans:
            if t in names:
                i = trans.index(t)
                # imply that we are using this translation value, not the 
                # per grain values
                # This is a f*cking mess - translations should never have been
                # diffractometer parameters
                for g in self.getgrains():
                    self.grains[g].translation[i] = newguess[names.index(t)]
                    print g, t,i,newguess[names.index(t)]
        print
        self.printresult(newguess)

    def getgrains(self):
        return self.grains.keys()


    def set_translation(self,gr,sc):
        self.parameterobj.parameters['t_x'] = self.grains[(gr,sc)].translation[0]
        self.parameterobj.parameters['t_y'] = self.grains[(gr,sc)].translation[1]
        self.parameterobj.parameters['t_z'] = self.grains[(gr,sc)].translation[2]


    def refinepositions(self, quiet=True, maxiters=100):
        self.assignlabels()
        ks  = self.grains.keys()
        ks.sort()
        # assignments are now fixed
        tolcache = self.tolerance
        self.tolerance = 1.0
        for key in ks:
            g = key[0]
            self.grains_to_refine = [key]
            self.parameterobj.varylist = [ 't_x', 't_y', 't_z' ]
            self.set_translation(key[0],key[1])
            guess = self.parameterobj.get_variable_values()
            inc =   self.parameterobj.get_variable_stepsizes()

            s =     simplex.Simplex(self.gof, guess, inc)

            newguess, error, iter = s.minimize(maxiters=maxiters,monitor=1)

            self.grains[key].translation[0] = self.parameterobj.parameters['t_x']
            self.grains[key].translation[1] = self.parameterobj.parameters['t_y'] 
            self.grains[key].translation[2] = self.parameterobj.parameters['t_z'] 
            print key,self.grains[key].translation,
            self.refine(self.grains[key].ubi,quiet=False)
        self.tolerance = tolcache

 
    def refineubis(self, quiet=True, scoreonly=False):
        #print quiet
        ks = self.grains.keys()
        ks.sort()
        if not quiet:
            print "%10s %10s"%("grainname","scanname"),
            print "npeak   <drlv> "
        for key in ks:
            g = self.grains[key]
            grainname = key[0]
            scanname = key[1]
            if not quiet:
                print "%10s %10s"%(grainname,scanname),
            # Compute gv using current parameters, including grain position
            self.set_translation(key[0],key[1])
            self.compute_gv(g)
            res = self.refine(g.ubi , quiet=quiet)
            if not scoreonly:
                g.set_ubi( res )


    def assignlabels(self):
        """
        Fill out the appropriate labels for the spots
        """
        print "Assigning labels with XLYLZL"
        import time
        start = time.time()
        for s in self.scannames:
            self.scandata[s].labels = self.scandata[s].labels*0 - 2 # == -1
            drlv2 = self.scandata[s].drlv2*0 + 1  # == 1
            nr = self.scandata[s].nrows
            sc = self.scandata[s].sc
            fc = self.scandata[s].fc
            # Looks like this in one dataset only
            ng = len(self.grainnames)
            int_tmp = numpy.zeros(nr , numpy.int32 )-1
            if 0: # this is pretty slow
                tth_tmp = numpy.zeros((ng, nr) ,numpy.float32 ) - 1
                eta_tmp = numpy.zeros((ng, nr) ,numpy.float32 )
            
            peaks_xyz = transform.compute_xyz_lab([ self.scandata[s].sc, 
                                                    self.scandata[s].fc ],
                                                  **self.parameterobj.parameters)
            print "Start first grain loop",time.time()-start
            start = time.time()
            for g, ig in zip(self.grainnames, range(ng)):
                assert g == ig, "sorry - a bug in program"
                gr = self.grains[ ( g, s) ]                
                self.set_translation( g, s)
                gr.peaks_xyz = peaks_xyz
                gr.om = self.scandata[s].omega
                self.compute_gv( gr )
                # self.tth and self.eta hold the current tth and eta values
                if 0:
                    tth_tmp[int(g),:] = self.tth
                    eta_tmp[int(g),:] = self.eta
#                print "about to assign"
                closest.score_and_assign( gr.ubi,
                                          self.gv,
                                          self.tolerance,
                                          drlv2,
                                          int_tmp,
                                          int(g))
#                print "assigned"
                
                 
            # Second loop after checking all grains
            print "End first grain loop",time.time()-start
            start = time.time()

            print self.scandata[s].labels.shape, \
                  numpy.minimum.reduce(self.scandata[s].labels),\
                  numpy.maximum.reduce(self.scandata[s].labels)
            
            self.scandata[s].addcolumn( int_tmp , "labels" )
            self.scandata[s].addcolumn( drlv2 , "drlv2" )
            print self.scandata[s].labels.shape, \
                  numpy.minimum.reduce(self.scandata[s].labels),\
                  numpy.maximum.reduce(self.scandata[s].labels)
            
            tth = numpy.zeros( nr, numpy.float32 )-1
            eta = numpy.zeros( nr, numpy.float32 )

            self.scandata[s].addcolumn( tth, "tth_per_grain" )
            self.scandata[s].addcolumn( eta, "eta_per_grain" )
            self.scandata[s].addcolumn( self.gv[:,0], "gx")
            self.scandata[s].addcolumn( self.gv[:,1], "gy")
            self.scandata[s].addcolumn( self.gv[:,2], "gz")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "hr")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "kr")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "lr")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "h")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "k")
            self.scandata[s].addcolumn( numpy.zeros(nr, numpy.float32), "l")


            print "Start second grain loop",time.time()-start
            start = time.time()

            # We have the labels set in self.scandata!!!
            for g in self.grainnames:
                gr = self.grains[ ( g, s) ]
                
                ind = numpy.compress(int_tmp == g,
                                     range(nr) )
                #print 'x',gr.x[:10]
                #print 'ind',ind[:10]
                gr.ind = ind # use this to push back h,k,l later
                gr.peaks_xyz = numpy.take( peaks_xyz, ind, axis=1 )
                gr.sc = numpy.take( sc, ind)
                gr.fc = numpy.take( fc, ind)
                gr.om = numpy.take(self.scandata[s].omega , ind)
                gr.npks = len(gr.ind)
                self.set_translation( g, s)
                try:
                    sign = self.parameterobj.parameters['omegasign']
                except:
                    sign = 1.0

                tth, eta = transform.compute_tth_eta_from_xyz( gr.peaks_xyz,
                                                       omega = gr.om * sign,
                                              **self.parameterobj.parameters)

                self.scandata[s].tth_per_grain[ind] = tth
                self.scandata[s].eta_per_grain[ind] = eta
                gr.intensity_info = compute_total_intensity( self.scandata[s] ,
                                                            ind,
                                                            self.intensity_tth_range )
                self.grains[ ( g, s) ] = gr
                print "Grain",g,"Scan",s,"npks=",len(ind)
                #print 'x',gr.x[:10]
            # Compute the total integrated intensity if we have enough
            # information available
            compute_lp_factor( self.scandata[s] ) 
            print "End second grain loop",time.time()-start
            print
            start = time.time()



def compute_lp_factor( colfile, **kwds ):
    """
    We'll assume for simplicity that wedge, chi, tilts are all zero
    Of course we should put that in sometime in the near future

    Try using:

    Table  6.2.1.1 in Volume C of international tables :
    (h) Rotation photograph of small crystal, volume V
        1. Beam normal to axis
        rho = \frac{ N^2 e^4 \lambda^3 V} { 4 \pi m^2 c^4} .
              \frac{ 1 + \cos^2{\theta} }  { \sin{2\theta } .
              \frac{ cos{\theta} { \sqrt{ \cos^2{\psi} - \sin^2{\theta} } }
              p' |F|^2
              
    rho is Integrated reflection power ratio from a crystal element
    e, m 	Electronic charge and mass
    c 	Speed of light
    \lambda 	Wavelength of radiation
    2\theta 	Angle between incident and diffracted beams
    \psi  in (h), latitude of reciprocal-lattice point relative to axis of rotation
    V 	Volume of crystal, or of irradiated part of powder sample
    N 	Number of unit cells per unit volume
    F 	Structure factor of hkl reflection
    p' 	Multiplicity factor for single-crystal methods
         nb - what is this ? Hopefully would be 1 ?


    From this we will take the (1+cos^2(2t))cos(2t)/sqrt(cos^2p-sin^2t)/sin2t
    """
    if "tth" in colfile.titles and "eta" in colfile.titles:
        lp  = lf( colfile.tth, colfile.eta )
        assert len(lp) == len(colfile.tth)
        try:
            colfile.addcolumn(lp, "Lorentz")
        except:
            print lp.shape, colfile.tth.shape, colfile.nrows, "?"
            raise
        
    if "tth_per_grain" in colfile.titles and \
       "eta_per_grain" in colfile.titles:
        lpg = lf( colfile.tth_per_grain, colfile.eta_per_grain )
        assert len(lpg) == len(colfile.tth_per_grain)
        colfile.addcolumn(lpg, "Lorentz_per_grain")
    
    
import math

def cosd(x): return numpy.cos( x * math.pi/180 )
def sind(x): return numpy.sin( x * math.pi/180 )

def lf( tth, eta ):

    sin_2t  = sind( tth )
    sin_eta = sind( numpy.abs( eta ) )
    sin2_t  = sind( tth/2 )*sind( tth/2 )
    # pure guesswork
    return  sin_2t * ( sin_eta + sin2_t )

    # unreachable code here:
    #  ... problem that cos^2_p - sin^2 can be < 0
    #       must mean that p is NOT eta 
    
    cos_2t = cosd( tth )
    
    cos_t  = cosd( tth/2 )
    sin_t  = sind( tth/2 )
    # our eta is their psi + 90 degrees
    cos_p  = cosd( eta + 90 )
    
    bot = sin_2t * numpy.sqrt( cos_p * cos_p - sin_t * sin_t )
    
    top = (1 + cos_2t * cos_2t)*cos_2t
    # Wondering if there is a div0 to fear
    # Certainly lf can be infinite, so mask this problem as 1e6
    bot = numpy.where( numpy.abs ( bot ) > 1e-6 , bot, 1e-6 )
    return top / bot
    
    
def compute_total_intensity( colfile, indices, tth_range, ntrim = 2 ):
    """
    Add up the intensity in colfile for peaks given in indices
    """
    if "sum_intensity" in colfile.titles:
        raw_intensities = colfile.sum_intensity
    else:
        if ("Number_of_pixels" in colfile.titles) and \
           ("avg_intensity"    in colfile.titles):
            raw_intensities = colfile.Number_of_pixels * colfile.avg_intensity
        else:
            try:
                raw_intensities = colfile.npixels * colfile.avg_intensity
            except:
                raw_intensities = numpy.ones(colfile.nrows)
    # Lorentz factor requires eta per grain. This would be tedious to
    # compute, but should eventually be added
    if "Lorentz_per_grain" in colfile.titles:
        lor = colfile.Lorentz_per_grain
        print "lorentz per grain for ints",
    elif "Lorentz" in colfile.titles:
        lor = colfile.Lorentz
        print "lorentz for ints",
    else:
        print "lost the lorentz",
        lor = numpy.ones( colfile.nrows, numpy.float32 )

    # risk divide by zero here...
    intensities = numpy.take( raw_intensities * lor , indices )
    sigma_i = numpy.sum(intensities)
    if tth_range is not None:
        if "tth_per_grain" in colfile.titles:
            tth = colfile.tth_per_grain
            print "tth_per_grain for",
        elif "tth" in colfile.titles:
            tth = colfile.tth
            print "tth for range",
        else:
            # bugger
            tth = numpy.ones(colfile.nrows)
        tth_vals = numpy.take(tth, indices )

        intensities = numpy.compress( ( tth_vals > min(tth_range) )&
                                      ( tth_vals < max(tth_range) ) ,
                                      intensities )
        print "range %.5f %.5f"%tuple(tth_range),


    if len(intensities) < 1:
        return "no peaks"
    # min, max, med, mean, stddev, n
    intensities.sort()
    
    if(len(intensities)) > ntrim*2+1:
        intensities = intensities[ntrim:-ntrim]
    try:
        ret = "sum_of_all = %f , middle %d from %f to %f in tth: median = %f , min = %f , max = %f , mean = %f , std = %f , n = %d"%(
        sigma_i,
        len(intensities),
        min(tth_range),
        max(tth_range),
        intensities[ len(intensities)/2 ],
        intensities.min(),
        intensities.max(),
        intensities.mean(),
        intensities.std(),
        intensities.shape[0])
    except:
        print intensities
        raise
    print ret
    return ret
    



def test_benoit():
    o=refinegrains()
    o.loadparameters("start.prm")
    scans  = ["0N.flt" ,"811N.flt" ,  "2211N.flt" , "3311N.flt" , "4811N.flt" ]
    for name in scans:
        o.loadfiltered(name)
    o.readubis("ubitest")
    o.generate_grains()
    o.tolerance = 0.1
    #o.varytranslations()
    for o.tolerance in [0.1,0.2,0.15,0.1,0.075,0.05]:
        o.refineubis(quiet=False)
    print "***"
    o.refineubis(quiet=False)
    o.varylist = ['y-center','z-center','distance','tilt-y','tilt-z','wedge','chi']
    o.fit()
    o.refineubis(quiet=False)


def test_nac():
    import sys
    o = refinegrains()
    o.loadparameters(sys.argv[1])
    print "got pars"
    o.loadfiltered(sys.argv[2])
    print "got filtered"
    o.readubis(sys.argv[3])
    print "got ubis"
    o.tolerance = float(sys.argv[4])
    print "generating"
    o.generate_grains()
    print "Refining posi too"
    o.refineubis(quiet = False , scoreonly = True)
    print "Refining positions too"
    o.refinepositions()
    print "Refining positions too"    
    o.refineubis(quiet = False , scoreonly = True)
    
    


if __name__ == "__main__":
    test_nac()
