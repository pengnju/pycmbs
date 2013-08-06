#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alexander Loew"
__version__ = "0.1"
__date__ = "2012/10/29"
__email__ = "alexander.loew@zmaw.de"

'''
# Copyright (C) 2012 Alexander Loew, alexander.loew@zmaw.de
# See COPYING file for copying and redistribution conditions.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
'''

import os

class pyCDO():
    '''
    class to use cdo commands via the shell
    alternative might be to use class cdo.py developed by Ralf Mueller

    @todo: put examples how to run pyCDO
    '''

    def __init__(self,filename,date1,date2,force=False,verbose=False):
        '''
        constructor of the pyCDO class

        @param filename: input file that should be processed
        @type filename: str

        @param date1: start date to extract data from
        @type date1: str of format like 2001-12-01

        @param date2: stop date to extract data from
        @type date2: str of format like 2001-12-01

        @param force: always run cdo (even if output file already existing)
        @type force: bool

        '''


        raise ValueError, 'The usage of pyCDO is obsolete! It should not be used any more and replace by the generic cdo-python interface!'


        if 'CDOTEMPDIR' in os.environ.keys():
            self.tempdir = os.environ['CDOTEMPDIR']
        else:
            self.tempdir = './'
        if self.tempdir[-1] != '/':
            self.tempdir = self.tempdir + '/'

        self.baseoutname = self.tempdir + os.path.basename(filename) #basename of file in temporary directory (used for generation of intermediate filenames)
        self.filename = filename

        if not os.path.exists(self.filename):
            print 'WARNING: file not existing ', self.filename
        self.date1=date1; self.date2=date2
        self.options = '-f nc'
        self.force = force
        self.verbose = verbose

#-----------------------------------------------------------------------

    def seasmean_djf(self,force=False):
        '''
        calculate seasmean for DJF season

        @param force: force calculations to be performed
        @type force: bool
        '''

        oname = self.baseoutname[:-3] + '_' + self.date1 + '_' + self.date2 + '_' + 'seasmean_djf' + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'seasmean' + ' -selseas,djf '  + self.filename + ' ' + oname
        self.run(cmd,oname,force)
        return oname


#-----------------------------------------------------------------------


    def seasmean(self,force=False):
        """
        calculate seasmean

        @param force: force calculations to be performed
        @type force: bool
        """

        oname = self.baseoutname[:-3] + '_' + self.date1 + '_' + self.date2 + '_' + 'seasmean' + '.nc'
        cmd1   = 'seasmean'
        cmd = 'cdo ' + self.options + ' ' + 'seasmean' + ' '  + self.filename + ' ' + oname
        self.run(cmd,oname,force)
        return oname


#-----------------------------------------------------------------------

    def gridarea(self,force=False):
        """
        calculate gridarea [m**2]

        @param force: force calculations to be performed
        @type force: bool
        """
        oname = self.baseoutname[:-3] + '_cell_area.nc'
        cmd = 'cdo ' + self.options + ' ' + 'gridarea' + ' '  + self.filename + ' ' + oname
        self.run(cmd,oname,force)
        return oname

#-----------------------------------------------------------------------

    def div(self,file2,force=False,output=None):
        """
        divide by file 2

        @param force: force calculations to be performed
        @type force: bool

        @param output: optional argument to specify output filename.
                       if names are too long (e.g. contain path names!)
        @type output: str

        @return: returns name of output file
        @rtype: str
        """



        if output != None:
            oname = output
        else:
            oname = self.baseoutname[:-3] + '_' + self.date1 + '_' + self.date2 + '_div_' + file2[:-3] + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'div' + ' '  + self.filename + ' ' + file2 + ' ' + oname
        self.run(cmd,oname,force)
        return oname

#-----------------------------------------------------------------------

    def selmon(self,months,force=False):
        """
        select months from a dataset (cdo selmon)

        @param months: list with months; e.g. [1,2,3,4] for JFMA
        @type months: list

        @param force: force execution also if file already existing
        @type force: bool

        """

        s=''
        if 1 in months:
            s=s+'J'
        if 2 in months:
            s=s+'F'
        if 3 in months:
            s=s+'M'
        if 4 in months:
            s=s+'A'
        if 5 in months:
            s=s+'M'
        if 6 in months:
            s=s+'J'
        if 7 in months:
            s=s+'J'
        if 8 in months:
            s=s+'A'
        if 9 in months:
            s=s+'S'
        if 10 in months:
            s=s+'O'
        if 11 in months:
            s=s+'N'
        if 12 in months:
            s=s+'D'

        arg = str(months).replace('[','').replace(']','').replace(' ','')

        oname = self.baseoutname[:-3] + '_'  + s + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'selmon,' + arg + ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)

        return oname

#-----------------------------------------------------------------------

    def remap(self,method='remapcon',force=False,target_grid='t63grid'):
        '''
        cdo remap command

        @param method: method to be performed (remapcon,remapbil,remapnn)
        @type method: str

        @param force: force execution also if file already existing
        @type force: bool

        @param target_grid: specification of the target grid
        @type target_grid: str
        '''

        if method == 'remapcon':
            remap_str = 'remapcon'
        elif method == 'remapnn':
            remap_str = 'remapnn'
        else:
            raise ValueError, 'Unknown remapping method'

        oname = self.baseoutname[:-3] + '_'  + remap_str + '.nc'
        cmd = 'cdo ' + self.options + ' ' + remap_str + ',' + target_grid +  ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)

        return oname

#-----------------------------------------------------------------------

    def yearmean(self,force=False):
        """
        cdo yearmean

        @param force: force calculation
        @type force: bool

        @param force: force execution also if file already existing
        @type force: bool
        """
        oname = self.baseoutname[:-3] + '_'  + 'yearmean' + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'yearmean' + ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)
        return oname

#-----------------------------------------------------------------------

    def yseasmean(self,force=False):
        '''
        cdo yearseasmean

        @param force: force execution also if file already existing
        @type force: bool
        '''
        oname = self.baseoutname[:-3] + '_'  + 'yseasmean' + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'yseasmean' + ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)

        return oname

#-----------------------------------------------------------------------

    def yseasstd(self,force=False):
        """
        cdo yseasstd

        @param force: force execution also if file already existing
        @type force: bool
        """

        oname = self.baseoutname[:-3] + '_'  + 'yseasstd' + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'yseasstd' + ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)

        return oname

#-----------------------------------------------------------------------

    def run(self,cmd,oname,force=False):
        """
        run command using shell command of CDO

        @param cmd: command to run
        @type cmd: str

        @param oname: output file name
        @type oname: str

        @param force: force execution also if file already existing
        @type force: bool

        @todo: generate output filename such that data is written to temporary directory

        """

        f_calc=False
        if os.path.exists(oname):
            if force:
                f_calc = True
            if self.force:
                f_calc = True
        else:
            f_calc = True

        if f_calc:
            print cmd; os.system(cmd)
        else:
            if self.verbose:
                print 'INFO - File existing, no calculations will be performed ', oname

#-----------------------------------------------------------------------

    def seldate(self,force=False):
        '''
        cdo seldate command
        returns a string for seldate command

        @param force: force execution also if file already existing
        @type force: bool

        @return: str with seldate command
        @rtype: str
        '''
        oname = self.baseoutname[:-3] + '_' + self.date1 + '_' + self.date2 + '.nc'
        cmd = 'cdo ' + self.options + ' ' + 'seldate,' + str(self.date1) + ',' + str(self.date2) + ' ' + self.filename + ' ' + oname
        self.run(cmd,oname,force)
        return oname

#-----------------------------------------------------------------------




