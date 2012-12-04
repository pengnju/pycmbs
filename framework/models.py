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



from pyCMBS import *
from utils import *
from cdo import *

'''
@todo: implement reading of air temperature fields
'''




class Model(Data):
    """
    This class is the main class, specifying a climate model or a particular run
    Sub-classes for particular models or experiments are herited from this class
    """
    def __init__(self,data_dir,dic_variables,name='',intervals=None,**kwargs):
        """
        constructor for Model class

        @param intervals: a dictionary from configuration, that specifies the temporal interval to be used within each analyis
        @type intervals: dict



        INPUT
        -----
        filename: name of the file to read data from (single file currently)
        could be improved later by more abstract class definitions

        dic_variables: dictionary specifiying variable names for a model
        e.g. 'rainfall','var4'
        """

        #--- check
        if intervals == None:
            raise ValueError, 'Invalid intervals for Model data: needs specification!'

        #--- set a list with different datasets for different models
        self.dic_vars = dic_variables
        self.intervals = intervals

        #--- set some metadata
        self.name = name
        self.data_dir = data_dir

        if 'start_time' in kwargs.keys():
            self.start_time = kwargs['start_time']
        else:
            self.start_time = None
        if 'stop_time' in kwargs.keys():
            self.stop_time = kwargs['stop_time']
        else:
            self.stop_time = None


    def get_data(self):
        """
        central routine to extract data for all variables
        using functions specified in derived class
        """

        self.variables={}
        for k in self.dic_vars.keys():
            routine = self.dic_vars[k] #get name of routine to perform data extraction
            interval = self.intervals[k]
            cmd = 'dat = self.' + routine
#            print cmd
#            print routine[0:routine.index('(')]
#            print hasattr(self,routine[0:routine.index('(')])
            #~ if hasattr(self,routine)
            if hasattr(self,routine[0:routine.index('(')]): #check if routine name is there
                exec(cmd)

                #if a tuple is returned, then it is the data + a tuple for the original global mean field
                if 'tuple' in str(type(dat)):
                    self.variables.update({ k : dat[0] }) #update field with data
                    self.variables.update({ k + '_org' : dat[1]}) #(time, meanfield, originalfield)
                else:
                    self.variables.update({ k : dat }) #update field with data

            else:
                print 'WARNING: unknown function to read data (skip!) '
                self.variables.update({ k : None })
                #~ sys.exit()




class CMIP5Data(Model):
    """
    Class for CMIP5 model simulations. This class is derived from C{Model}.
    """
    def __init__(self,data_dir,model,experiment,dic_variables,name='',shift_lon=False,**kwargs):
        """

        @param data_dir: directory that specifies the root directory where the data is located
        @param model: TBD tood
        @param experiment: specifies the ID of the experiment (str)
        @param dic_variables:
        @param name: TBD todo
        @param shift_lon: specifies if longitudes of data need to be shifted
        @param kwargs: other keyword arguments
        @return:
        """
        Model.__init__(self,None,dic_variables,name=model,shift_lon=shift_lon,**kwargs)

        self.model      = model; self.experiment = experiment
        self.data_dir   = data_dir; self.shift_lon  = shift_lon
        self.type       = 'CMIP5'

#-----------------------------------------------------------------------

    def get_faPAR(self):
        """
        Specifies how to read faPAR information for CMIP5 data
        @return: C{Data} object for faPAR
        """

        ddir = '/net/nas2/export/eo/workspace/m300028/GPA/'   #<<< todo: change this output directory !!!
        data_file = ddir + 'input/historical_r1i1p1-LR_fapar.nc' #todo set inputfilename interactiveley !!!! DUMMY so far for testnig


        #todo: which temporal resolution is needed?? preprocessing with CDO's needed ??? --> monthly

        return Data(data_file,'fapar')

#-----------------------------------------------------------------------

    def get_snow_fraction(self):
        """
        Specifies for CMIP5 class how to read SNOWFRACTION

        @return: C{Data} object for snow
        """
        data_file = '/net/nas2/export/eo/workspace/m300028/GPA/input/historical_r1i1p1-LR_snow_fract.nc' #todo change this !!!

        #todo: which temporal resolution is needed?? preprocessing with CDO's needed ??? --> monthly

        return Data(data_file,'snow_fract')


#-----------------------------------------------------------------------

    def get_rainfall_data(self):

        '''
        return data object of
        a) seasonal means for precipitation
        b) global mean timeseries for PR at original temporal resolution
        '''

        #original data
        filename1 = self.data_dir + 'pr/' +  self.model + '/' + 'pr_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'

        force_calc = False

        if self.start_time == None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time == None:
            raise ValueError, 'Stop time needs to be specified'

        s_start_time = str(self.start_time)[0:10]
        s_stop_time = str(self.stop_time)[0:10]

        tmp  = pyCDO(filename1,s_start_time,s_stop_time,force=force_calc).seldate()
        tmp1 = pyCDO(tmp,s_start_time,s_stop_time).seasmean()
        filename = pyCDO(tmp1,s_start_time,s_stop_time).yseasmean()

        if not os.path.exists(filename):
            return None

        pr = Data(filename,'pr',read=True,label=self.model,unit='mm/day',lat_name='lat',lon_name='lon',shift_lon=False,scale_factor=86400.)

        prall  = Data(filename1,'pr',read=True,label=self.model,unit='mm/day',lat_name='lat',lon_name='lon',shift_lon=False,scale_factor=86400.)
        prmean = prall.fldmean()

        retval = (prall.time,prmean); del prall

        pr.data = np.ma.array(pr.data,mask=pr.data < 0.)

        return pr,retval

#-----------------------------------------------------------------------

    def get_temperature_2m(self):

        '''
        return data object of
        a) seasonal means for air temperature
        b) global mean timeseries for TAS at original temporal resolution
        '''

        #original data
        filename1 = self.data_dir + 'tas/' +  self.model + '/' + 'tas_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'

        force_calc = False

        if self.start_time == None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time == None:
            raise ValueError, 'Stop time needs to be specified'

        s_start_time = str(self.start_time)[0:10]
        s_stop_time = str(self.stop_time)[0:10]

        tmp  = pyCDO(filename1,s_start_time,s_stop_time,force=force_calc).seldate()
        tmp1 = pyCDO(tmp,s_start_time,s_stop_time).seasmean()
        filename = pyCDO(tmp1,s_start_time,s_stop_time).yseasmean()

        if not os.path.exists(filename):
            return None

        tas = Data(filename,'tas',read=True,label=self.model,unit='K',lat_name='lat',lon_name='lon',shift_lon=False)

        tasall = Data(filename1,'tas',read=True,label=self.model,unit='K',lat_name='lat',lon_name='lon',shift_lon=False)
        tasmean = tasall.fldmean()

        retval = (tasall.time,tasmean); del tasall

        tas.data = np.ma.array(tas.data,mask=tas.data < 0.)

        return tas,retval


#-----------------------------------------------------------------------



    def get_surface_shortwave_radiation_down(self,interval = 'season'):

        """
        return data object of
        a) seasonal means for SIS
        b) global mean timeseries for SIS at original temporal resolution
        """

        #original data
        filename1 = self.data_dir + 'rsds/' +  self.model + '/' + 'rsds_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'

        force_calc = False

        if self.start_time == None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time == None:
            raise ValueError, 'Stop time needs to be specified'



        #/// PREPROCESSING ///
        cdo = Cdo()
        s_start_time = str(self.start_time)[0:10]
        s_stop_time = str(self.stop_time)[0:10]

        #1) select timeperiod and generate monthly mean file
        file_monthly = filename1[:-3] + '_' + s_start_time + '_' + s_stop_time + '_T63_monmean.nc'
        file_monthly = get_temporary_directory() + os.path.basename(file_monthly)
        cdo.monmean(options='-f nc',output=file_monthly,input = '-remapcon,t63grid -seldate,' + s_start_time + ',' + s_stop_time + ' ' + filename1,force=force_calc)

        #2) calculate monthly or seasonal climatology
        if interval == 'monthly':
            sis_clim_file     = file_monthly[:-3] + '_ymonmean.nc'
            sis_sum_file      = file_monthly[:-3] + '_ymonsum.nc'
            sis_N_file        = file_monthly[:-3] + '_ymonN.nc'
            sis_clim_std_file = file_monthly[:-3] + '_ymonstd.nc'
            cdo.ymonmean(options='-f nc -b 32',output = sis_clim_file,input=file_monthly, force=force_calc)
            cdo.ymonsum(options='-f nc -b 32',output = sis_sum_file,input=file_monthly, force=force_calc)
            cdo.ymonstd(options='-f nc -b 32',output = sis_clim_std_file,input=file_monthly, force=force_calc)
            cdo.div(options='-f nc',output = sis_N_file,input=sis_sum_file + ' ' + sis_clim_file, force=force_calc) #number of samples
        elif interval == 'season':
            sis_clim_file     = file_monthly[:-3] + '_yseasmean.nc'
            sis_sum_file      = file_monthly[:-3] + '_yseassum.nc'
            sis_N_file        = file_monthly[:-3] + '_yseasN.nc'
            sis_clim_std_file = file_monthly[:-3] + '_yseasstd.nc'
            cdo.yseasmean(options='-f nc -b 32',output = sis_clim_file,input=file_monthly, force=force_calc)
            cdo.yseassum(options='-f nc -b 32',output = sis_sum_file,input=file_monthly, force=force_calc)
            cdo.yseasstd(options='-f nc -b 32',output = sis_clim_std_file,input=file_monthly, force=force_calc)
            cdo.div(options='-f nc -b 32',output = sis_N_file,input=sis_sum_file + ' ' + sis_clim_file, force=force_calc) #number of samples
        else:
            print interval
            raise ValueError, 'Unknown temporal interval. Can not perform preprocessing! '

        if not os.path.exists(sis_clim_file):
            return None

        #3) read data
        sis = Data(sis_clim_file,'rsds',read=True,label=self.model,unit='$W m^{-2}$',lat_name='lat',lon_name='lon',shift_lon=False)
        sis_std = Data(sis_clim_std_file,'rsds',read=True,label=self.model+ ' std',unit='-',lat_name='lat',lon_name='lon',shift_lon=False)
        sis.std = sis_std.data.copy(); del sis_std
        sis_N = Data(sis_N_file,'rsds',read=True,label=self.model+ ' std',unit='-',lat_name='lat',lon_name='lon',shift_lon=False)
        sis.n = sis_N.data.copy(); del sis_N

        #ensure that climatology always starts with January, therefore set date and then sort
        sis.adjust_time(year=1700,day=15) #set arbitrary time for climatology
        sis.timsort()

        #4) read monthly data
        sisall = Data(file_monthly,'rsds',read=True,label=self.model,unit='W m^{-2}',lat_name='lat',lon_name='lon',shift_lon=False,time_cycle=12) #todo check timecycle
        sismean = sisall.fldmean()

        #/// return data as a tuple list
        retval = (sisall.time,sismean,sisall); del sisall

        #/// mask areas without radiation (set to invalid): all data < 1 W/m**2
        sis.data = np.ma.array(sis.data,mask=sis.data < 1.)

        return sis,retval

#-----------------------------------------------------------------------

    def get_surface_shortwave_radiation_up(self):
        filename1 = self.data_dir + 'rsus/' +  self.model + '/' + 'rsus_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'

        if self.start_time == None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time == None:
            raise ValueError, 'Stop time needs to be specified'

        s_start_time = str(self.start_time)[0:10]
        s_stop_time  = str(self.stop_time)[0:10]

        tmp  = pyCDO(filename1,s_start_time,s_stop_time).seldate()
        tmp1 = pyCDO(tmp,s_start_time,s_stop_time).seasmean()
        filename = pyCDO(tmp1,s_start_time,s_stop_time).yseasmean()

        if not os.path.exists(filename):
            return None

        sis = Data(filename,'rsus',read=True,label=self.model,unit='W/m**2',lat_name='lat',lon_name='lon',shift_lon=False)
        print 'Data read!'

        return sis

    def get_albedo_data(self):
        """
        calculate albedo as ratio of upward and downwelling fluxes
        first the monthly mean fluxes are used to calculate the albedo,
        """

        force_calc = False

        #--- read land-sea mask
        ls_mask = get_T63_landseamask(self.shift_lon)

        if self.start_time == None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time == None:
            raise ValueError, 'Stop time needs to be specified'

        s_start_time = str(self.start_time)[0:10]; s_stop_time  = str(self.stop_time )[0:10]

        file_down = self.data_dir + 'rsds/' +  self.model + '/' + 'rsds_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'
        file_up   = self.data_dir + 'rsus/' +  self.model + '/' + 'rsus_Amon_' + self.model + '_' + self.experiment + '_ensmean.nc'

        if not os.path.exists(file_down):
            print 'File not existing: ', file_down
            return None
        if not os.path.exists(file_up):
            print 'File not existing: ', file_up
            return None

        #/// calculate ratio on monthly basis
        # CAUTION: it might happen that latitudes are flipped. Therefore always apply remapcon!

        #select dates
        Fu = pyCDO(file_up,s_start_time,s_stop_time,force=force_calc).seldate()
        Fd = pyCDO(file_down,s_start_time,s_stop_time,force=force_calc).seldate()

        #remap to T63
        tmpu = pyCDO(Fu,s_start_time,s_stop_time,force=force_calc).remap()
        tmpd = pyCDO(Fd,s_start_time,s_stop_time,force=force_calc).remap()

        #calculate monthly albedo
        if 'CDOTEMPDIR' in os.environ.keys(): #check for temp. directory to write albedo file to
            tdir = os.environ['CDOTEMPDIR']
        else:
            tdir = './'
        albmon = pyCDO(tmpu,s_start_time,s_stop_time,force=force_calc).div(tmpd,output=tdir + self.model + '_' + self.experiment + '_albedo_tmp.nc')

        #calculate seasonal mean albedo
        tmp1 = pyCDO(albmon,s_start_time,s_stop_time,force=force_calc).seasmean()
        albfile = pyCDO(tmp1,s_start_time,s_stop_time,force=force_calc).yseasmean()

        alb = Data(albfile,'rsus',read=True,label=self.model + ' albedo',unit='-',lat_name='lat',lon_name='lon',shift_lon=True)
        alb._set_valid_range(0.,1.)

        alb._apply_mask(ls_mask.data)

        return alb





#####################################################




class JSBACH_BOT(Model):

    def __init__(self,filename,dic_variables,experiment,name='',shift_lon=False,**kwargs):

        Model.__init__(self,filename,dic_variables,name=name,**kwargs)
        self.experiment = experiment
        self.shift_lon = shift_lon
        self.get_data()
        self.type = 'JSBACH_BOT'

    def get_albedo_data(self):
        """
        get albedo data for JSBACH

        returns Data object
        """

        v = 'var176'

        filename = self.data_dir + 'data/model1/' + self.experiment + '_echam6_BOT_mm_1979-2006_albedo_yseasmean.nc' #todo: proper files
        ls_mask = get_T63_landseamask()

        albedo = Data(filename,v,read=True,
        label='MPI-ESM albedo ' + self.experiment, unit = '-',lat_name='lat',lon_name='lon',
        shift_lon=shift_lon,
        mask=ls_mask.data.data)

        return albedo



    def get_tree_fraction(self):
        """
        todo implement this for data from a real run !!!
        """

        ls_mask = get_T63_landseamask()

        filename = '/home/m300028/shared/dev/svn/trstools-0.0.1/lib/python/pyCMBS/framework/external/vegetation_benchmarking/VEGETATION_COVER_BENCHMARKING/example/historical_r1i1p1-LR_1850-2005_forest_shrub.nc'
        v = 'var12'
        tree = Data(filename,v,read=True,
        label='MPI-ESM tree fraction ' + self.experiment, unit = '-',lat_name='lat',lon_name='lon',
        shift_lon=shift_lon,
        mask=ls_mask.data.data,start_time = pl.num2date(pl.datestr2num('2001-01-01')),stop_time=pl.num2date(pl.datestr2num('2001-12-31')))

        return tree

    def get_grass_fraction(self):
        """
        todo implement this for data from a real run !!!
        """

        ls_mask = get_T63_landseamask()

        filename = '/home/m300028/shared/dev/svn/trstools-0.0.1/lib/python/pyCMBS/framework/external/vegetation_benchmarking/VEGETATION_COVER_BENCHMARKING/example/historical_r1i1p1-LR_1850-2005_grass_crop_pasture_2001.nc'
        v = 'var12'
        grass = Data(filename,v,read=True,
        label='MPI-ESM tree fraction ' + self.experiment, unit = '-',lat_name='lat',lon_name='lon',
        #shift_lon=shift_lon,
        mask=ls_mask.data.data,start_time = pl.num2date(pl.datestr2num('2001-01-01')),stop_time=pl.num2date(pl.datestr2num('2001-12-31')) , squeeze=True  )


        return grass









    def get_surface_shortwave_radiation_down(self,interval = 'season'):
        """
        get surface shortwave incoming radiation data for JSBACH

        returns Data object
        """

        v = 'var176'

        y1 = '1979-01-01'; y2 = '2006-12-31'
        rawfilename = self.data_dir + 'data/model/' + self.experiment + '_echam6_BOT_mm_1979-2006_srads.nc'

        if not os.path.exists(rawfilename):
            return None


        #--- read data
        cdo = pyCDO(rawfilename,y1,y2)
        if interval == 'season':
            seasfile = cdo.seasmean(); del cdo
            print 'seasfile: ', seasfile
            cdo = pyCDO(seasfile,y1,y2)
            filename = cdo.yseasmean()
        else:
            raise ValueError, 'Invalid interval option ', interval

        #--- read land-sea mask
        ls_mask = get_T63_landseamask()

        #--- read SIS data
        sis = Data(filename,v,read=True,
        label='MPI-ESM SIS ' + self.experiment, unit = '-',lat_name='lat',lon_name='lon',
        #shift_lon=shift_lon,
        mask=ls_mask.data.data)

        return sis


    def get_rainfall_data(self,interval='season'):
        """
        get rainfall data for JSBACH
        returns Data object
        """

        if interval == 'season':
            pass
        else:
            raise ValueError, 'Invalid value for interval: ' + interval

        #/// PREPROCESSING: seasonal means ///
        s_start_time = str(self.start_time)[0:10]
        s_stop_time = str(self.stop_time)[0:10]

        filename1 = self.data_dir + 'data/model/' + self.experiment + '_echam6_BOT_mm_1982-2006_sel.nc'
        tmp  = pyCDO(filename1,s_start_time,s_stop_time).seldate()
        tmp1 = pyCDO(tmp,s_start_time,s_stop_time).seasmean()
        filename = pyCDO(tmp1,s_start_time,s_stop_time).yseasmean()

        #/// READ DATA ///

        #1) land / sea mask
        ls_mask = get_T63_landseamask(self.shift_lon)

        #2) precipitation data
        try: #todo this is silly; need to adapt in the edn
            v = 'var4'
            rain = Data(filename,v,read=True,scale_factor = 86400.,
            label='MPI-ESM ' + self.experiment, unit = 'mm/day',lat_name='lat',lon_name='lon',
            shift_lon=self.shift_lon,
            mask=ls_mask.data.data)
        except:
            v='var142'
            rain = Data(filename,v,read=True,scale_factor = 86400.,
            label='MPI-ESM ' + self.experiment, unit = 'mm/day',lat_name='lat',lon_name='lon',
            shift_lon=self.shift_lon,
            mask=ls_mask.data.data)

        return rain



#-----------------------------------------------------------------------

class JSBACH_RAW(Model):
    """
    Class for RAW JSBACH model output
    """

    def __init__(self,filename,dic_variables,experiment,name='',shift_lon=False,**kwargs):

        Model.__init__(self,filename,dic_variables,name=name,**kwargs)
        self.experiment = experiment
        self.shift_lon = shift_lon
        self.get_data()
        self.type = 'JSBACH_RAW'

    def get_albedo_data(self):
        """
        calculate albedo as ratio of upward and downwelling fluxes
        first the monthly mean fluxes are used to calculate the albedo,
        """

        if self.start_time is None:
            raise ValueError, 'Start time needs to be specified'
        if self.stop_time is None:
            raise ValueError, 'Stop time needs to be specified'

        sw_down = self.get_surface_shortwave_radiation_down()
        sw_up   = self.get_surface_shortwave_radiation_up()
        alb     = sw_up.div(sw_down)
        alb.label = self.experiment + ' albedo'
        alb.unit = '-'

        return alb




    def get_surface_shortwave_radiation_down(self,interval = 'season'):
        """
        get surface shortwave incoming radiation data for JSBACH

        @param interval: specifies the aggregation interval. Possible options: ['season']
        @type interval: str

        @return: returns a C{Data} object
        @rtype: C{Data}
        """

        v = 'swdown_acc'

        y1 = '1992-01-01'; y2 = '2001-12-31'
        rawfilename = self.data_dir + 'yseasmean_' + self.experiment + '_jsbach_' + y1[0:4] + '_' + y2[0:4] + '.nc'

        if not os.path.exists(rawfilename):
            print 'File not existing: ', rawfilename
            return None

        filename = rawfilename

        #--- read land-sea mask
        ls_mask = get_T63_landseamask(self.shift_lon)

        #--- read SIS data
        sw_down = Data(filename,v,read=True,
        label=self.experiment + ' ' + v, unit = 'W/m**2',lat_name='lat',lon_name='lon',
        shift_lon=self.shift_lon,
        mask=ls_mask.data.data)

        return sw_down


#-----------------------------------------------------------------------

    def get_surface_shortwave_radiation_up(self,interval = 'season'):
        """
        get surface shortwave upward radiation data for JSBACH

        returns Data object

        todo CDO preprocessing of seasonal means
        todo temporal aggregation of data --> or leave it to the user!
        """

        v = 'swdown_reflect_acc'

        y1 = '1992-01-01'; y2 = '2001-12-31' #@todo years !!
        rawfilename = self.data_dir + 'yseasmean_' + self.experiment + '_jsbach_' + y1[0:4] + '_' + y2[0:4] + '.nc'

        if not os.path.exists(rawfilename):
            print 'File not existing: ', rawfilename
            return None

        filename = rawfilename

        #--- read land-sea mask
        ls_mask = get_T63_landseamask(self.shift_lon)

        #--- read SW up data
        sw_up = Data(filename,v,read=True,
        label=self.experiment + ' ' + v, unit = 'W/m**2',lat_name='lat',lon_name='lon',
        shift_lon=self.shift_lon,
        mask=ls_mask.data.data)

        return sw_up

#-----------------------------------------------------------------------

    def get_rainfall_data(self,interval = 'season'):
        """
        get surface rainfall data for JSBACH

        returns Data object

        todo CDO preprocessing of seasonal means
        todo temporal aggregation of data --> or leave it to the user!
        """

        v = 'precip_acc'

        y1 = '1992-01-01'; y2 = '2001-12-31' #todo years
        rawfilename = self.data_dir + 'yseasmean_' + self.experiment + '_jsbach_' + y1[0:4] + '_' + y2[0:4] + '.nc'

        if not os.path.exists(rawfilename):
            return None

        filename = rawfilename

        #--- read land-sea mask
        ls_mask = get_T63_landseamask(self.shift_lon)

        #--- read SW up data
        rain = Data(filename,v,read=True,
        label=self.experiment + ' ' + v, unit = 'mm/day',lat_name='lat',lon_name='lon',
        shift_lon=self.shift_lon,
        mask=ls_mask.data.data,scale_factor = 86400.)

        return rain


#-----------------------------------------------------------------------






