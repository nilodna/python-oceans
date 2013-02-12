# -*- coding: utf-8 -*-
#
# ctd.py
#
# purpose:  Some classes and functions to work with CTD data.
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.tiddlyspot.com/
# created:  22-Jun-2012
# modified: Tue 12 Feb 2013 12:01:33 PM BRST
#
# obs: Instead of sub-classing I opted for a "Monkey Patch" approach
#      (Wes suggestion).
#

"""
TODO:
Methods:
  * Series
    - interpolate (FIXME: extrapolate).
    - find MLD (TODO: Add more methods).
    - find barrier (TODO: Check paper).
    - reindex from db to z and from z to db.
    - Use scipy.stats.binned_statistic for bindata.
  * DataFrame
    - plot_yy
    - compare two variables
  * Panel:
    - topography
    - plot section
    - geostrophic velocity
    - station map (lon, lat)
    - distance vector
"""

from __future__ import division

import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA

from scipy.interpolate import interp1d
from scipy.stats import nanmean, nanstd
from pandas import Index, Series, DataFrame
from mpl_toolkits.axes_grid1 import host_subplot

import gsw
from oceans.utilities import basename


degree = u"\u00b0"


# Utilities.
def normalize_names(name):
    name = name.strip()
    name = name.strip('*')  # Seabird only
    name = name.lower()
    #name = name.replace(' ', '_')
    return name


def find_outlier(point, window, n):
    return np.abs(point - nanmean(window)) >= n * nanstd(window)


def asof(self, label):
    if label not in self:
        loc = self.searchsorted(label, side='left')
        if loc > 0:
            return self[loc - 1]
        else:
            return np.nan

    return label


def check_index(ix0, ix1):
    if isinstance(ix0, Series) and isinstance(ix1, Series):
        ix0, ix1 = ix0.index.float_(), ix1.index.float_()
        if (ix0 == ix1).all():
            return ix0, ix1
    elif isinstance(ix0, float) and isinstance(ix1, float):
        if ix0 == ix1:
            return ix0, ix1
    else:
        raise ValueError("Series index must be the same.")


def get_maxdepth(self):
    valid_last_depth = self.apply(Series.notnull).values.T
    return np.float_(self.index * valid_last_depth).max(axis=1)


def plot_section(self, filled=False, **kw):
    # Contour key words.
    fmt = kw.pop('fnt', '%1.0f')
    extend = kw.pop('extend', 'both')
    fontsize = kw.pop('fontsize', 12)
    labelsize = kw.pop('labelsize', 11)
    cmap = kw.pop('cmap', plt.cm.rainbow)
    levels = kw.pop('levels', np.arange(np.floor(self.min().min()),
                    np.ceil(self.max().max()) + 0.5, 0.5))

    # Colorbar key words.
    pad = kw.pop('pad', 0.04)
    aspect = kw.pop('aspect', 40)
    shrink = kw.pop('shrink', 0.9)
    fraction = kw.pop('fraction', 0.05)

    # Topography mask key words.
    dx = kw.pop('dx', 1.)
    kind = kw.pop('kind', 'linear')

    # Station symbols key words.
    color = kw.pop('color', 'k')
    offset = kw.pop('offset', -5)

    # Get data for plotting.
    z = self.index.values
    h = self.get_maxdepth()
    data = ma.masked_invalid(self.values)
    if filled:
        data = extrap_sec(data.filled(fill_value=np.nan), self.lon, self.lat)

    x = np.append(0, np.cumsum(gsw.distance(self.lon, self.lat)[0] / 1e3))
    xm, hm = gen_topomask(h, self.lon, self.lat, dx=dx, kind=kind)

    # Figure.
    fig, ax = plt.subplots()
    ax.plot(xm, hm, color='black', linewidth=1.5, zorder=3)
    ax.fill_between(xm, hm, y2=hm.max(), color='0.9', zorder=3)

    ax.plot(x, [offset] * len(h), color=color, marker='v',
            alpha=0.5, zorder=5)
    ax.set_xlabel('Cross-shore distance [km]', fontsize=fontsize)
    ax.set_ylabel('Depth [m]', fontsize=fontsize)
    ax.set_ylim(offset, hm.max())
    ax.invert_yaxis()

    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    ax.yaxis.set_ticks_position('left')
    ax.yaxis.set_label_position('left')
    ax.xaxis.set_tick_params(tickdir='out', labelsize=labelsize, pad=1)
    ax.yaxis.set_tick_params(tickdir='out', labelsize=labelsize, pad=1)

    if 0:  # TODO: +/- Black-and-White version.
        cs = ax.contour(x, z, data, colors='grey', levels=levels,
                        extend=extend, linewidths=1., alpha=1., zorder=2)
        ax.clabel(cs, fontsize=8, colors='grey', fmt=fmt, zorder=1)
        cb = None
    if 1:  # Color version.
        cs = ax.contourf(x, z, data, cmap=cmap, levels=levels, alpha=1.,
                         extend=extend, zorder=2)  # manual=True
        # Colorbar.
        cb = fig.colorbar(mappable=cs, ax=ax, orientation='vertical',
                          aspect=aspect, shrink=shrink, fraction=fraction,
                          pad=pad)
        cb.ax.set_title(ur'$\theta$ [%s C]' % degree, fontsize=fontsize)
    return fig, ax, cb


def extrap_sec(data, lon, lat, fd=1.):
    r"""Extrapolates `data` to zones where the shallow stations are shadowed by
    the deep stations.  The shadow region usually cannot be extrapolates via
    linear interpolation.

    The extrapolation is applied using the gradients of the `data` at a certain
    level.

    Parameters
    ----------
    data : array_like
          Data to be extrapolated
    lon : array_like
          Stations longitude
    lat : array_like
          Stations latitude
    fd : float
         Decay factor [0-1]


    Returns
    -------
    Sec_extrap : array_like
                 Extrapolated variable

    Examples
    --------
    Sec_extrap = extrap_sec(data, lon, lat, fd=1.)
    """
    lon, lat = map(np.asanyarray, (lon, lat))

    dist = np.r_[0, np.cumsum(gsw.distance(lon, lat)[0] / 1e3)]
    fnan = np.isnan(data[:, -2])
    data[fnan, -2] = data[fnan, -1]
    for col in range(lon.size - 2, 0, -1):
        if np.isnan(data[-1, col]):
            a = np.where(np.isnan(data[:, col]))
            data[a, col] = data[a, col + 1] - fd * ((((data[a, col + 2]) -
            data[a, col + 1]) / (dist[col + 2] - dist[col + 1])) *
            (dist[col + 1] - dist[col]))
    return data


def gen_topomask(h, lon, lat, dx=1., kind='linear', plot=False):
    r"""Generates a topography mask from an oceanographic transect taking the
    deepest CTD scan as the depth of each station.

    Inputs
    ------
    h : array
        Pressure of the deepest CTD scan for each station [dbar].
    lons : array
           Longitude of each station [decimal degrees east].
    lat : Latitude of each station. [decimal degrees north].
    dx : float
         Horizontal resolution of the output arrays [km].
    kind : string, optional
           Type of the interpolation to be performed.
           See scipy.interpolate.interp1d documentation for details.
    plot : bool
           Whether to plot mask for visualization.

    Outputs
    -------
    xm : array
         Horizontal distances [km].
    hm : array
         Local depth [m].

    Examples
    --------
    >>> xm, hm = gen_topomask(h, lon, lat, dx=1., kind='linear', plot=False')
    >>> fig, ax = plt.subplots()
    >>> ax.plot(xm, hm, 'k', linewidth=1.5)
    >>> ax.plot(x, h, 'ro')
    >>> ax.set_xlabel('Distance [km]')
    >>> ax.set_ylabel('Depth [m]')
    >>> ax.grid(True)
    >>> plt.show()

    Author
    ------
    André Palóczy Filho (paloczy@gmail.com) --  October/2012
    """

    h, lon, lat = map(np.asanyarray, (h, lon, lat))
    # Distance in km.
    x = np.append(0, np.cumsum(gsw.distance(lon, lat)[0] / 1e3))
    h = -gsw.z_from_p(h, lat.mean())
    Ih = interp1d(x, h, kind=kind, bounds_error=False, fill_value=h[-1])
    xm = np.arange(0, x.max() + dx, dx)
    hm = Ih(xm)

    return xm, hm


# TEOS-10 and other functions.
def SP_from_C(C, t):
    p = check_index(C, t)[0]
    return Series(gsw.SP_from_C(C, t, p), index=p, name='Salinity')


def CT_from_t(SA, t):
    p = check_index(SA, t)[0]
    return Series(gsw.CT_from_t(SA, t, p), index=p,
                  name='Conservative_temperature')


def sigma0_CT_exact(SA, CT):
    return Series(gsw.sigma0_CT_exact(SA, CT), index=SA.index,
                  name='Sigma_theta')


def mixed_layer_depth(t, verbose=True):
    mask = t[0] - t < 0.5
    if verbose:
        print("MLD: %3.2f " % t.index[mask][-1])
    return Series(mask, index=t.index, name='MLD')


def barrier_layer_depth(SA, CT, verbose=True):
    sigma_theta = sigma0_CT_exact(SA, CT)
    # Density difference from the surface to the "expected" using the
    #temperature at the base of the mixed layer.
    mask = mixed_layer_depth(CT)
    mld = np.where(mask)[0][-1]
    sig_surface = sigma_theta[0]
    sig_bottom_mld = gsw.sigma0_CT_exact(SA[0], CT[mld])
    d_sig_t = sig_surface - sig_bottom_mld
    d_sig = sigma_theta - sig_bottom_mld
    mask = d_sig < d_sig_t  # Barrier layer.
    if verbose:
        if mask.any():
            print("Barrier layer: %3.2f." % SA.index[mask][-1])
        else:
            print("No barrier layer present.")
    return Series(mask, index=SA.index, name='Barrier_layer')


# Index methods.
def float_(self):
    return np.float_(self.values)


# Series methods.
# TODO: variable window_len (5 <100, 11 100--500, 21 > 500)
def smooth(self, window_len=11, window='hanning'):
    r"""Smooth the data using a window with requested size."""

    windows = dict(flat=np.ones, hanning=np.hanning, hamming=np.hamming,
                   bartlett=np.bartlett, blackman=np.blackman)
    data = self.values.copy()

    if window_len < 3:
        return Series(data, index=self.index, name=self.name)

    if not window in windows.keys():
        raise ValueError("""Window is on of 'flat', 'hanning', 'hamming',
                         'bartlett', 'blackman'""")

    s = np.r_[2 * data[0] - data[window_len:1:-1], data, 2 *
              data[-1] - data[-1:-window_len:-1]]

    w = windows[window](window_len)

    data = np.convolve(w / w.sum(), s, mode='same')
    data = data[window_len - 1:-window_len + 1]
    return Series(data, index=self.index, name=self.name)


def despike(self, n=3, windowsize=10, verbose=False):
    r"""Replace spikes with np.NaN.  Removing spikes that are >= n * std.
    default n = 3."""

    data = self.values.copy()
    for k, point in enumerate(data):
        if k <= windowsize:
            window = data[k:k + windowsize]
            if find_outlier(point, window, n):
                data[k] = np.NaN
        elif k >= len(data) - windowsize:
            window = data[k - windowsize:k]
            if find_outlier(point, window, n):
                data[k] = np.NaN
        else:
            window = data[k - windowsize:k + windowsize]
            if find_outlier(point, window, n):
                data[k] = np.NaN

    return Series(data, index=self.index, name=self.name)


# DataFrame.
@classmethod
def from_fsi(cls, fname, verbose=True):
    r"""Read FSI CTD ASCII columns. NOTE: This might break!"""
    dtype = [('SCANS', 'f4'),
             ('PRES', 'f4'),
             ('TEMP', 'f4'),
             ('COND', 'f4'),
             ('OXCU', 'f4'),
             ('OXTM', 'f4'),
             ('FLUO', 'f4'),
             ('OBS', 'f4'),
             ('SAL', 'f4'),
             ('DEN', 'f4'),
             ('SV', 'f4'),
             ('DEPTH', 'f4')]

    recarray = np.loadtxt(fname, dtype=dtype, skiprows=10)
    #exclude* = ['SCANS', 'OBS', 'SV', 'DEPTH', 'SAL']
    cast = cls.from_records(recarray, index='PRES',
                            exclude=None,  # exclude*
                            coerce_float=True)
    try:
        cast.name = basename(fname)[0]
    except:
        cast.name = None

    return cast


@classmethod
def from_cnv(cls, fname, verbose=True, cast_type='down'):
    r"""Read ASCII CTD file from Seabird model cnv file.
    Return two DataFrames with up/down casts."""
    header, config, names = [], [], []
    with open(fname, 'r') as f:
        for k, line in enumerate(f.readlines()):
            line = line.strip()
            if '# name' in line:  # Get columns names.
                name, unit = line.split('=')[1].split(':')
                name, unit = map(normalize_names, (name, unit))
                names.append(name)
            if line.startswith('*'):  # Get header.
                header.append(line)
            if line.startswith('#'):  # Get configuration file.
                config.append(line)
            if line == '*END*':  # Get end of header.
                header_length = k + 1

    if verbose:
        print("\nHEADER\n")
        print('\n'.join(header))
        print("\nCONFIG\n")
        print('\n'.join(config))

    dtype = []
    for col in names:
        dtype.append((col, 'f4'))

    # Read as a record array and load it as a DataFrame.
    recarray = np.loadtxt(fname, dtype=dtype, skiprows=header_length)
    # FIXME: index column name is Hard-coded.
    cast = cls.from_records(recarray, index='prdm',
                                    exclude=None, coerce_float=True)
    cast.index.name = 'Pressure [db]'

    # Get profile under 5 meters (after the CTD stabilization).
    cast = cast[cast.index >= 5]

    # Separate casts.
    if cast_type == 'down':
        cast = cast.ix[:cast.index.argmax()]
    elif cast_type == 'up':
        cast = cast.ix[cast.index.argmax():]
    else:
        print("Cast type %s not understood" % cast_type)
        cast = None

    try:
        cast.name = basename(fname)[0]
    except:
        cast.name = None
    return cast


@classmethod
def from_edf(cls, fname, depth=None, verbose=True):
    header, names = [], []
    with open(fname) as f:
        for k, line in enumerate(f.readlines()):
            line = line.strip()
            header.append(line)
            if line.startswith('Latitude'):
                hemisphere = line[-1]
                lat = line.strip(hemisphere).split(':')[1].strip()
                lat = np.float_(lat.split())
                if hemisphere == 'S':
                    lat = -(lat[0] + lat[1] / 60.)
                elif hemisphere == 'N':
                    lat = lat[0] + lat[1] / 60.
                else:
                    print("Latitude not recognized.")
                    break
            elif line.startswith('Serial Number'):
                serial = line.strip().split(':')[1].strip()
            elif line.startswith('Longitude'):
                hemisphere = line[-1]
                lon = line.strip(hemisphere).split(':')[1].strip()
                lon = np.float_(lon.split())
                if hemisphere == 'W':
                    lon = -(lon[0] + lon[1] / 60.)
                elif hemisphere == 'E':
                    lon = lon[0] + lon[1] / 60.
                else:
                    print("Longitude not recognized.")
                    break
            elif line.startswith('Field'):
                col, unit = [l.strip().lower() for l in line.split(':')]
                names.append(unit.split()[0])
            elif line.startswith('// Data'):
                header_length = k + 1
            else:
                continue

    if verbose:  # FIXME: Header is capturing the data.
        print("\nHEADER\n")
        print('\n'.join(header))
        print("\nLongitude: %s, Latitude %s\n" % (lon, lat))

    dtype = []
    for name in names:
        dtype.append((name, 'f4'))
    # Read as a record array and load it as a DataFrame.
    recarray = np.loadtxt(fname, dtype=dtype, skiprows=header_length)
    # FIXME: Depth column is Hard-coded.
    cast = cls.from_records(recarray, index='depth',
                                exclude=None, coerce_float=True)

    # Get profile under 5 meters (after the XBT surface spike).
    cast = cast[cast.index >= 5]
    # Cut at specified depth.
    if depth:
        cast = cast[cast.index <= depth]
    cast.lon = lon
    cast.lat = lat
    cast.serial = serial
    cast.depth = depth

    try:
        cast.name = basename(fname)[0]
    except:
        cast.name = None

    return cast


def bindata(self, db=1.):
    r"""Bin average the index (pressure) to a given interval in decibars [db].
    default db = 1.
    This method assumes that the profile start at the surface (0) and "ceils"
    the last depth.

    Note that this method does not drop NA automatically.  Therefore, one can
    check the quality of the binned data."""

    start = np.floor(self.index[0])
    end = np.ceil(self.index[-1])
    shift = db / 2.  # To get centered bins.
    new_index = np.arange(start, end, db) - shift

    new_index = Index(new_index)
    newdf = self.groupby(new_index.asof).mean()
    newdf.index += shift  # Not shifted.

    return newdf


def plot(self, **kwds):
    r"""Plot a CTD variable against the index (pressure or depth)."""
    fig, ax = plt.subplots()
    ax.plot(self.values, self.index, **kwds)
    ax.set_ylabel(self.index.name)
    ax.set_xlabel(self.name)
    ax.invert_yaxis()
    offset = 0.01
    x1, x2 = ax.get_xlim()[0] - offset, ax.get_xlim()[1] + offset
    ax.set_xlim(x1, x2)
    return fig, ax


def plot_vars(self, variables=None, **kwds):
    r"""Plot CTD temperature and salinity."""

    fig = plt.figure(figsize=(8, 10))
    ax0 = host_subplot(111, axes_class=AA.Axes)
    ax1 = ax0.twiny()

    # Axis location.
    host_new_axis = ax0.get_grid_helper().new_fixed_axis
    ax0.axis["bottom"] = host_new_axis(loc="top", axes=ax0, offset=(0, 0))
    par_new_axis = ax1.get_grid_helper().new_fixed_axis
    ax1.axis["top"] = par_new_axis(loc="bottom", axes=ax1, offset=(0, 0))

    ax0.plot(self[variables[0]], self.index, 'r-.', label='Temperature')
    ax1.plot(self[variables[1]], self.index, 'b-.', label='Salinity')

    ax0.set_ylabel("Pressure [db]")
    ax0.set_xlabel("Temperature [%sC]" % degree)
    ax1.set_xlabel("Salinity [kg g$^{-1}$]")
    ax1.invert_yaxis()

    if cast.name:
        fig.suptitle(r"Station %s profile" % cast.name)

    ax0.legend(shadow=True, fancybox=True,
               numpoints=1, loc='lower right')

    offset = 0.01
    x1, x2 = ax0.get_xlim()[0] - offset, ax0.get_xlim()[1] + offset
    ax0.set_xlim(x1, x2)

    offset = 0.01
    x1, x2 = ax1.get_xlim()[0] - offset, ax1.get_xlim()[1] + offset
    ax1.set_xlim(x1, x2)

    return fig, (ax0, ax1)


Series.plot = plot
Series.smooth = smooth
Series.despike = despike
Series.bindata = bindata

DataFrame.from_cnv = from_cnv
DataFrame.from_edf = from_edf
DataFrame.from_fsi = from_fsi
DataFrame.plot_vars = plot_vars
DataFrame.get_maxdepth = get_maxdepth
DataFrame.plot_section = plot_section

Index.asof = asof
Index.float_ = float_

if __name__ == '__main__':
    import re
    from glob import glob
    from pandas import HDFStore
    from collections import OrderedDict

    if 0:  # FSI.
        fname = 'data/d3_7165.txt'
        cast = DataFrame.from_fsi(fname, verbose=False)
        cast.plot_vars(['TEMP', 'SAL'])
    if 0:  # XBT-T5 EDF.
        fname = '/home/filipe/Dropbox/Work/LaDO/Projetos/AMBES/AMB09_data'
        fname += '/DATA_SJ/XBT/AMB09_037_XBT_rad3.EDF'
        cast = DataFrame.from_edf(fname, depth=13., verbose=False)
        cast['temperature'].plot()
    if 0:  # Seabird.
        fname = '/home/filipe/Dropbox/Work/LaDO/Projetos/AMBES/AMB09_data'
        fname += '/DATA_SJ/CTD/AMB09_059_CTD_rad3.cnv'
        cast = DataFrame.from_cnv(fname, verbose=False)
        fig, ax = cast.plot_vars(['t090c', 'sal00'])
        if 0:  # Remove spikes.
            # Using the apply method.
            kw = dict(n=3, windowsize=5, verbose=True)
            despiked = cast.t090c.despike(**kw)
            fig, ax = plt.subplots()
            ax.plot(cast.t090c, cast.index, 'r', label='Original')
            ax.plot(despiked, despiked.index, 'k.', alpha=0.5,
                    label='de-spiked')
            ax.set_title("De-spiked vs Original data")
            ax.set_ylabel("Pressure [db]")
            ax.set_xlabel("Temperature [%sC]" % degree)
            ax.legend(shadow=True, fancybox=True, numpoints=1, loc='best')
            ax.invert_yaxis()
            offset = 0.05
            x1, x2 = ax.get_xlim()[0] - offset, ax.get_xlim()[1] + offset
            ax.set_xlim(x1, x2)
        if 0:  # Bin average.
            binned = cast.apply(Series.bindata, db=1.)
            # TODO: Add salinity at the same plot.
            fig, ax = plt.subplots()
            ax.plot(cast.t090c, cast.index, 'k-.', label='Original')
            ax.plot(binned.t090c, binned.index, 'r.', label='Binned')
            ax.set_title("Binned vs Original data")
            ax.set_ylabel("Pressure [db]")
            ax.set_xlabel("Temperature [%sC]" % degree)
            ax.legend(shadow=True, fancybox=True, numpoints=1, loc='best')
            ax.invert_yaxis()
            ax.grid(True)
            offset = 0.05
            x1, x2 = ax.get_xlim()[0] - offset, ax.get_xlim()[1] + offset
            ax.set_xlim(x1, x2)
        if 0:  # Smooth.
            t090c_smoo = cast.t090c.smooth(window_len=111, window='hanning')
            fig, ax = plt.subplots()
            ax.plot(cast.t090c, cast.index, 'r', linewidth=2.0,
                    label='Original')
            ax.plot(t090c_smoo, t090c_smoo.index, 'k', alpha=0.5,
                    label='Smoothed')
            ax.set_title("Smoothed vs Original data")
            ax.set_ylabel("Pressure [db]")
            ax.set_xlabel("Temperature [%sC]" % degree)
            ax.legend(shadow=True, fancybox=True, numpoints=1, loc='best')
            ax.invert_yaxis()
            offset = 0.05
            x1, x2 = ax.get_xlim()[0] - offset, ax.get_xlim()[1] + offset
            ax.set_xlim(x1, x2)

    if 0:  # Read a radial.
        digits = re.compile(r'(\d+)')

        def tokenize(fname):
            return tuple(int(token) if match else token for token, match in
                        ((frag, digits.search(frag)) for frag in
                        digits.split(fname)))

        pattern = '/home/filipe/Dropbox/Work/LaDO/Projetos/AMBES/AMB09_data'
        pattern += '/DATA_SJ/CTD/AMB09_*_CTD_rad1.cnv'
        fnames = sorted(glob(pattern), key=tokenize)

        Temp = OrderedDict()
        lon, lat = [], []
        for fname in fnames:
            cast = DataFrame.from_cnv(fname, verbose=False)
            print(fname)
            temp = cast['t090c'].bindata()
            lon.append(cast.longitude.values[0])
            lat.append(cast.latitude.values[0])
            Temp.update({cast.name: temp})

        Temp = DataFrame.from_dict(Temp)
        Temp.lon = lon
        Temp.lat = lat

    if 0:  # Save radial
        store = HDFStore("radial_01.h5", 'w')
        store['temperature'] = Temp
        store.close()
        # FIXME: Need to find a way to serial the metadata!
        np.savez("radial_01.npz", lon=lon, lat=lat)

    if 1:  # Plot sections.
        store = HDFStore("radial_01.h5", 'r')
        Temp = store['temperature']
        store.close()
        npz = np.load("radial_01.npz")
        Temp.lon = npz['lon']
        Temp.lat = npz['lat']

        fig, ax, cb = Temp.plot_section()
        fig, ax, cb = Temp.plot_section(filled=True)
