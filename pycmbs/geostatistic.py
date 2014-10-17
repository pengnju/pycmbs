# -*- coding: utf-8 -*-

"""
This file is part of pyCMBS. (c) 2012-2014
For COPYING and LICENSE details, please refer to the file
COPYRIGHT.md
"""

from pycmbs.data import Data
import matplotlib.pyplot as plt
import numpy as np

class Geostatistic(object):
    def __init__(self, x, range_bins=None):
        """
        Geostatistical calculations on a data object

        Parameters
        ----------
        x : Data
            data to be analyzed
        range_bins : list
            list of bins to perform analysis
        """
        assert isinstance(x, Data)
        if range_bins is None:
            raise ValueError('ERROR: you need to specifiy the range bins!')
        self.x = x
        self.range_bins = np.asarray(range_bins)
        self._check()
        self.statistic = {}

    def _check(self):
        if np.any(np.diff(self.range_bins) < 0.):
            raise ValueError('Bins are not in ascending order!')
        if self.x.data.ndim != 2:
            raise ValueError('Currently only support for 2D data')

    def set_center_position(self, lon, lat):
        """
        set position of location to be used for analysis as center
        lon : float
            longitude of center position [deg]
        lat : float
            latitude of center position [deg]
        """
        self.lon_center = lon
        self.lat_center = lat

    def _get_center_pos(self):
        """
        get indices of position of center coordinate within grid
        """
        if not hasattr(self, 'lon_center'):
            raise ValueError('ERROR: You need to specify first the center position!')
        d = np.abs((self.x.lon - self.lon_center) ** 2. + (self.x.lat - self.lat_center) ** 2.)
        dmin = d.min()
        m = d == dmin

        idx = np.indices(d.shape)
        i = idx[0][m][0]
        j = idx[1][m][0]

        if (np.abs(1. - self.x.lon[i, j] / self.lon_center) > 0.05) or (np.abs(1. - self.x.lat[i, j] / self.lat_center) > 0.05):  # at least 5% acc.
            print 'lon: ', self.x.lon[i, j], self.lon_center
            print 'lat: ', self.x.lat[i, j], self.lat_center
            i = None
            j = None
        return i, j

    def plot_semivariogram(self, ax=None, color='red', logy=False, ref_lags=None):
        """
        plot semivariogram

        Parameters
        ----------
        ref_lags : list
            list of reference lags. If given, then these lags are plotted in the figure as well
        """
        if not hasattr(self, '_distance'):
            self._calculate_distance()

        f, ax = self._get_figure_ax(ax)
        self.calc_semivariance()
        r = self.statistic['semivariogram']['r']
        sigma = self.statistic['semivariogram']['sigma']

        if logy:
            ax.semilogy(r, sigma, 'x', color=color)
        else:
            ax.plot(r, sigma, 'x', color=color)
        ax.set_ylabel('$\sigma^2$ / 2 (isotropic)')
        ax.set_xlabel('distance from center [km]')
        ax.grid()

        if ref_lags is not None:
            for d in ref_lags:
                ax.plot([d,d],ax.get_ylim(), color='grey')

        return ax

    def plot_percentiles(self, p, ax=None, logy=False, ref_lags=None):
        """
        plot percentiles

        p : list
            list of percentiles [0 ... 1]
        """
        f, ax = self._get_figure_ax(ax)
        for e in p:
            self.calc_percentile(e)
            r = self.statistic['percentiles'][e]['r']
            v = self.statistic['percentiles'][e]['value']
            if logy:
                ax.semilogy(r, v, 'x-', label='p=' + str(e))
            else:
                ax.plot(r, v, 'x-', label='p=' + str(e))
        ax.set_ylabel(self.x._get_unit())
        ax.set_xlabel('distance [km]')
        ax.grid()
        ax.legend(loc='upper left', prop={'size': 10}, ncol=3)
        if ref_lags is not None:
            for d in ref_lags:
                ax.plot([d,d],ax.get_ylim(), color='grey')

        return ax

    def calc_percentile(self, p):
        """
        p [0 ... 1]
        """
        bounds = self.range_bins
        r = []
        v = []
        for b in bounds:
            d = self._get_data_distance(0., b)
            if d is None:
                continue
            if len(d) < 1:
                continue
            r.append(b)
            v.append(np.percentile(d, p * 100.))  # percentile value

        r = np.asarray(r)
        np.asarray(v)

        o = {'r': np.asarray(r), 'value': np.asarray(v)}
        if 'percentiles' not in self.statistic.keys():
            self.statistic.update({'percentiles': {}})

        self.statistic['percentiles'].update({p: o})

    def _get_data_distance(self, lb, ub):
        """
        get data for distance where

        lb<= r < ub
        """
        if not hasattr(self, '_distance'):
            self._calculate_distance()
        m = (self._distance >= lb) & (self._distance < ub)
        if m.sum() == 0:
            return None
        o = self.x.data[m].flatten()
        if isinstance(o, np.ma.core.MaskedArray):
            o = o.data[~o.mask]  # ensure that nparray is returned
        return o

    def calc_semivariance(self):
        """
        calculate semivariance for selected range bins
        """
        bounds = self.range_bins
        r = []
        v = []
        for b in bounds:
            d = self._get_data_distance(0., b)
            if d is None:
                r.append(b)
                v.append(np.nan)
            else:
                r.append(b)
                v.append(0.5 * np.ma.var(d))  # semivariance
        o = {'r': np.asarray(r), 'sigma': np.asarray(v)}
        self.statistic.update({'semivariogram': o})

    def _get_figure_ax(self, ax):
        if ax is None:
            f = plt.figure()
            ax = f.add_subplot(111)
        else:
            f = ax.figure
        return f, ax

    def _calculate_distance(self, data=None):
        """
        calculate distance [km]

        Parameters
        ----------
        data : Data
            if given, then this object is taken for distance calculations instead of self.x
        """
        if not hasattr(self, 'lon_center'):
            raise ValueError('ERROR: You need to specify first the center position!')
        if data is None:
            ref = self.x
        else:
            ref = data

        self._distance = ref.distance(self.lon_center, self.lat_center) / 1000.

    def get_coordinates_at_distance(self, d, N=360, dist_threshold=None, oversampling_factor=None):
        """
        return an ordered list of coordinates that are closest to the
        specified radius.

        This can be used to generate e.g. a Polygon for plotting.
        The approach is that a circle is drawn around the center location
        and the all points with cloes radius in each direction is stored

        Parameters
        ----------
        d : float
            distance [km]
        N : int
            number of samples
        dist_threshold : float
            threshold [km] to identify closest points
        oversampling_factor : float
            if None, then nothing happens. If > 1. then the distance
            calculations will be done on an oversampled grid. This allows
            to plot e.g. nicer overlays (e.g. circles) with the data
        """

        if not hasattr(self, 'lon_center'):
            raise ValueError('Missing coordinate!')
        if not hasattr(self, 'lat_center'):
            raise ValueError('Missing coordinate!')
        if dist_threshold is None:
            raise ValueError('You need to provide a distance threshold!')

        if oversampling_factor is None:
            refobj = self.x
            if not hasattr(self, '_distance'):
                self._calculate_distance()
        else:
            if oversampling_factor < 1.:
                raise ValueError('Oversampling factor needs to be > 1!')
            refobj = self.x.copy()
            ny = int(refobj.ny*oversampling_factor)
            nx = int(refobj.nx*oversampling_factor)

            lonn = np.linspace(refobj.lon.min(), refobj.lon.max(), nx)
            latn = np.linspace(refobj.lat.min(), refobj.lat.max(), ny)
            refobj.lon, refobj.lat = np.meshgrid(lonn, latn)

            self._calculate_distance(data=refobj)

        # get closest points as preselection
        #di = np.round(np.abs(self._distance-d),0).astype('int')
        di = np.abs(self._distance-d)
        #msk = di == 0
        msk = di < dist_threshold
        lons = refobj.lon[msk].flatten()
        lats = refobj.lat[msk].flatten()
        dist = self._distance[msk].flatten()

        if len(lons) == 0:
            return None, None

        theta = np.linspace(0., 2.*np.pi, N)  # angle
        LON = []
        LAT = []
        for t in theta:
            x = self.lon_center + d*np.cos(t)
            y = self.lat_center + d*np.sin(t)

            # search for closest point
            dd = np.sqrt((lons-x)**2. + (lats-y)**2.)

            LON.append(lons[dd.argmin()])
            LAT.append(lats[dd.argmin()])

        return LON, LAT





