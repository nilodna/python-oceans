#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# colormaps.py
#
# purpose:  create colormaps for matplotlib
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.tiddlyspot.com/
# created:  11-Oct-2010
# modified: Thu 02 May 2013 10:52:04 AM BRT
#
# obs:
#

from __future__ import division

from colorsys import hsv_to_rgb

import numpy as np
import matplotlib as mpl
from scipy.signal import sawtooth


def cpt2seg(file_name, sym=False, discrete=False):
    r"""Reads a .cpt palette and returns a segmented colormap.

    sym : If True, the returned colormap contains the palette and a mirrored
    copy.  For example, a blue-red-green palette would return a
    blue-red-green-green-red-blue colormap.

    discrete : If true, the returned colormap has a fixed number of uniform
    colors.  That is, colors are not interpolated to form a continuous range.

    Example
    -------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.colors import LinearSegmentedColormap
    >>> data = cpt2seg('palette.cpt')
    >>> palette = LinearSegmentedColormap('palette', data, 100)
    >>> plt.imshow(X, cmap=palette)

    http://matplotlib.1069221.n5.nabble.com/
    function-to-create-a-colormap-from-cpt-palette-td2165.html
    """

    dic = {}
    rgb = np.loadtxt(file_name)
    rgb = rgb / 255.
    s = rgb.shape
    colors = ['red', 'green', 'blue']
    for c in colors:
        i = colors.index(c)
        x = rgb[:, i + 1]
        if discrete:
            if sym:
                dic[c] = np.zeros((2 * s[0] + 1, 3), dtype=np.float_)
                dic[c][:, 0] = np.linspace(0, 1, 2 * s[0] + 1)
                vec = np.concatenate((x, x[::-1]))
            else:
                dic[c] = np.zeros((s[0] + 1, 3), dtype=np.float_)
                dic[c][:, 0] = np.linspace(0, 1, s[0] + 1)
                vec = x
            dic[c][1:, 1] = vec
            dic[c][:-1, 2] = vec

        else:
            if sym:
                dic[c] = np.zeros((2 * s[0], 3), dtype=np.float_)
                dic[c][:, 0] = np.linspace(0, 1, 2 * s[0])
                vec = np.concatenate((x, x[::-1]))
            else:
                dic[c] = np.zeros((s[0], 3), dtype=np.float_)
                dic[c][:, 0] = np.linspace(0, 1, s[0])
                vec = x
            dic[c][:, 1] = vec
            dic[c][:, 2] = vec
    return dic


class Bunch(dict):
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self


def cmat2cmpl(rgb):
    r"""Convert RGB matplotlib colormap."""
    rgb = np.asarray(rgb)
    return mpl.colors.ListedColormap(rgb)


def _reverse_cm(cm):
    return np.flipud(cm)


def phasemap_cm(m=256):
    r"""Colormap periodic/circular data (phase)."""

    theta = 2 * np.pi * np.arange(m) / m
    circ = np.exp(1j * theta)

    # Vertices of color triangle
    vred, vgreen, vblue = -2, 1 - np.sqrt(3) * 1j, 1 + np.sqrt(3) * 1j
    vredc = vred - circ
    vgreenc = vgreen - circ
    vbluec = vblue - circ

    red = np.abs(np.imag(vgreenc * np.conj(vbluec)))
    green = np.abs(np.imag(vbluec * np.conj(vredc)))
    blue = np.abs(np.imag(vredc * np.conj(vgreenc)))

    cmap = (1.5 * np.vstack([red, green, blue]) /
                np.abs(np.imag((vred - vgreen) * np.conj(vred - vblue))))

    return cmap.T / 255.


def zebra_cm(a=4, n=1, m=0.5):
    r"""Zebra palette colormap with NBANDS broad bands and NENTRIES rows in
    the color map.

    The default is 4 broad bands

    cmap = zebra(nbands, nentries)

    see Hooker, S. B. et al, Detecting Dipole Ring Separatrices with Zebra
    Palettes, IEEE Transactions on Geosciences and Remote Sensing, vol. 33,
    1306-1312, 1995

    Notes
    -----
    Saturation and value go from m to 1 don't use m = 0.
    a = 4 -> there are this many large bands in the palette
    """

    x = np.arange(0, n)
    hue = np.exp(-3. * x / n)
    sat = m + (1. - m) * (0.5 * (1. + sawtooth(2. * np.pi * x / (n / a))))
    val = m + (1. - m) * 0.5 * (1. + np.cos(2. * np.pi * x / (n / a / 2.)))

    cmap = [hsv_to_rgb(h, s, v) for h, s, v in zip(hue, sat, val)]
    cmap = np.asarray(cmap)

    return cmap.T / 255.


def ctopo_pos_neg_cm(m=256):
    r"""Colormap for positive/negative data with gray scale only
    original from cushman-roisin book cd-rom."""
    dx = (1. - 0.) * 1. / (m - 1.)
    values = np.arange(0., 1., dx)
    cmap = np.r_[values, values, values]

    return cmap.T


def avhrr_cm(m=256):
    r"""AHVRR colormap used by NOAA Coastwatch."""

    x = np.arange(0, m - 1.) / (m - 1.)

    xr = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    rr = [0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5]
    r = np.interp(x, xr, rr)

    xg = [0.0, 0.4, 0.6, 1.0]
    gg = [0.0, 1.0, 1.0, 0.0]
    g = np.interp(x, xg, gg)

    xb = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    bb = [0.0, 0.0, 0.5, 0.5, 1.0, 1.0, 0.5]
    b = np.interp(x, xb, bb)

    return np.flipud(np.r_[r, g, b]).T


# List of colormaps.

phasemap = phasemap_cm()
zebra = zebra_cm()
avhrr = avhrr_cm()

cbathy = np.array([[8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9,
                9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 10,
                9, 8, 8, 7, 6, 5, 5, 4, 3, 2, 2, 1, 0, 0],
                [241, 237, 234, 231, 228, 225, 222, 218, 215, 212, 209,
                204, 199, 194, 190, 185, 180, 175, 171, 166, 161, 160,
                158, 157, 156, 154, 153, 152, 150, 149, 148, 146, 145,
                144, 142, 141, 140, 134, 129, 124, 119, 114, 109, 103,
                98, 93, 88, 83, 77, 72, 67, 62, 57, 51, 46, 41, 36, 31,
                25, 20, 15, 10, 5, 0],
                [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                255, 255, 255, 255, 255, 247, 240, 232, 225, 217, 210,
                202, 195, 188, 180, 173, 165, 158, 150, 143]]).T / 255.

coolavhrrmap = np.array([[255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        250, 250, 245, 245, 237, 237, 212, 212, 187, 187,
                        162, 162, 137, 137, 112, 112, 87, 87, 62, 62, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 3, 7, 11, 15, 19, 23, 27, 31, 35, 39,
                        43, 47, 51, 55, 59, 63, 67, 71, 75, 79, 83, 87,
                        91, 95, 99, 103, 107, 111, 115, 119, 123, 127,
                        131, 135, 139, 143, 147, 151, 155, 159, 163, 167,
                        171, 175, 179, 183, 187, 191, 195, 199, 203, 207,
                        211, 215, 219, 223, 227, 231, 235, 239, 243, 247,
                        251, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 250, 246, 241, 237,
                        233, 228, 224, 219, 215, 211, 206, 202, 197, 193,
                        189, 184, 180, 175, 171, 167, 162, 158, 153, 149,
                        145, 140, 136, 131, 131],
                        [45, 41, 37, 34, 30, 26, 23, 19, 30, 19, 30, 19,
                        30, 19, 30, 19, 30, 19, 30, 19, 30, 19, 30, 19,
                        30, 19, 30, 19, 30, 19, 0, 0, 0, 0, 3, 7, 11, 15,
                        19, 23, 27, 31, 35, 39, 43, 47, 51, 55, 59, 63,
                        67, 71, 75, 79, 83, 87, 91, 95, 99, 103, 107,
                        111, 115, 119, 123, 127, 131, 135, 139, 143, 147,
                        151, 155, 159, 163, 167, 171, 175, 179, 183, 187,
                        191, 195, 199, 203, 207, 211, 215, 219, 223, 227,
                        231, 235, 239, 243, 247, 251, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 251, 247, 243, 239, 235, 231, 227, 223,
                        219, 215, 211, 207, 203, 199, 195, 191, 187, 183,
                        179, 175, 171, 167, 163, 159, 155, 151, 147, 143,
                        139, 135, 131, 127, 123, 119, 115, 111, 107, 103,
                        99, 95, 91, 87, 83, 79, 75, 71, 67, 63, 59, 55,
                        51, 47, 43, 39, 35, 31, 27, 23, 19, 15, 11, 7, 3,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [142, 155, 168, 181, 194, 206, 219, 232, 194, 232,
                        194, 232, 194, 232, 194, 232, 194, 232, 194, 232,
                        194, 232, 194, 232, 194, 232, 194, 232, 194, 232,
                        247, 251, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255, 251,
                        247, 243, 239, 235, 231, 227, 223, 219, 215, 211,
                        207, 203, 199, 195, 191, 187, 183, 179, 175, 171,
                        167, 163, 159, 155, 151, 147, 143, 139, 135, 131,
                        127, 123, 119, 115, 111, 107, 103, 99, 95, 91,
                        87, 83, 79, 75, 71, 67, 63, 59, 55, 51, 47, 43,
                        39, 35, 31, 27, 23, 19, 15, 11, 7, 3, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]).T / 255.

rscolmap = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 30, 45, 60, 75, 90,
                    105, 120, 128, 136, 144, 152, 160, 168, 176, 184,
                    188, 192, 196, 200, 204, 208, 212, 217, 219, 221,
                    223, 226, 228, 230, 232, 235, 236, 238, 239, 241,
                    243, 244, 246, 248, 248, 249, 250, 251, 251, 252,
                    253, 254, 254, 254, 254, 254, 254, 254, 254, 255,
                    255, 255, 255, 254, 254, 254, 254, 253, 252, 251,
                    250, 249, 248, 247, 246, 244, 243, 241, 240, 238,
                    237, 235, 234, 232, 231, 229, 228, 226, 224, 223,
                    221, 219, 218, 216, 214, 212, 210, 208, 206, 204,
                    202, 200, 198, 196, 194, 192, 190, 188, 187, 186,
                    185, 183, 182, 181, 180, 178, 177, 176, 175, 173,
                    172, 171, 170, 168],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 9,
                    12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 49,
                    52, 56, 60, 64, 68, 72, 76, 80, 83, 87, 91, 95, 98,
                    102, 106, 110, 114, 119, 124, 129, 133, 138, 143,
                    148, 151, 155, 158, 162, 166, 169, 173, 177, 180,
                    183, 186, 190, 193, 196, 199, 203, 204, 205, 207,
                    208, 209, 211, 212, 214, 213, 212, 211, 209, 208,
                    207, 206, 204, 203, 202, 200, 199, 198, 196, 195,
                    193, 193, 192, 191, 190, 189, 188, 187, 186, 186,
                    186, 186, 186, 186, 186, 186, 187, 188, 189, 190,
                    191, 192, 193, 194, 196, 198, 200, 202, 204, 206,
                    208, 210, 213, 214, 216, 218, 220, 221, 223, 225,
                    227, 228, 230, 232, 234, 236, 238, 240, 242, 243,
                    245, 246, 248, 249, 251, 252, 254, 254, 254, 254,
                    254, 254, 254, 254, 254, 253, 251, 250, 248, 247,
                    245, 244, 242, 240, 238, 236, 233, 231, 229, 227,
                    224, 222, 220, 218, 216, 214, 212, 210, 208, 206,
                    203, 201, 198, 196, 193, 191, 188, 186, 183, 180,
                    177, 175, 172, 169, 166, 164, 161, 159, 156, 153,
                    151, 148, 145, 143, 140, 138, 135, 132, 130, 127,
                    124, 122, 119, 117, 114, 111, 109, 106, 103, 101, 98,
                    95, 92, 89, 86, 83, 80, 77, 74, 71, 67, 64, 61, 58,
                    54, 51, 48, 44, 41, 38, 34, 31, 27, 24, 21, 17, 14,
                    11, 7, 4,   0],
                    [123, 124, 125, 126, 128, 129, 131,
                    132, 134, 135, 137, 139, 140, 142, 144, 146, 148,
                    150, 152, 154, 156, 158, 160, 162, 165, 167, 170,
                    172, 175, 177, 180, 183, 186, 190, 193, 196, 200,
                    203, 207, 210, 214, 217, 221, 224, 228, 231, 235,
                    237, 239, 241, 244, 246, 248, 250, 253, 253, 253,
                    253, 254, 254, 254, 254, 255, 254, 252, 251, 249,
                    247, 246, 244, 242, 237, 232, 227, 222, 217, 212,
                    207, 202, 198, 193, 188, 183, 179, 174, 169, 164,
                    160, 155, 150, 145, 141, 136, 131, 126, 122, 118,
                    113, 109, 105, 100, 96, 91, 88, 85, 81, 78, 75, 71,
                    68, 64, 61, 58, 55, 52, 49, 46, 43, 40, 38, 35, 32,
                    29, 27, 24, 21, 18, 16, 14, 12, 9, 7, 5, 3, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]).T / 255.

redgreen = np.array([[127, 128, 128, 129, 129, 130, 130, 131, 131, 132,
                    132, 133, 133, 134, 134, 135, 135, 136, 136, 137,
                    137, 138, 138, 139, 139, 140, 140, 141, 141, 142,
                    142, 143, 143, 144, 144, 145, 145, 146, 146, 147,
                    147, 148, 148, 149, 149, 150, 150, 151, 151, 152,
                    152, 153, 153, 154, 154, 155, 155, 156, 156, 157,
                    157, 158, 158, 159, 159, 160, 160, 161, 161, 162,
                    162, 163, 163, 164, 164, 165, 165, 166, 166, 167,
                    167, 168, 168, 169, 169, 170, 170, 171, 171, 172,
                    172, 173, 173, 174, 174, 175, 175, 176, 176, 177,
                    177, 178, 178, 179, 179, 180, 180, 181, 181, 182,
                    182, 183, 183, 184, 184, 185, 185, 186, 186, 187,
                    187, 188, 188, 189, 189, 190, 190, 191, 191, 192,
                    192, 193, 193, 194, 194, 195, 195, 196, 196, 197,
                    197, 198, 198, 199, 199, 200, 200, 201, 201, 202,
                    202, 203, 203, 204, 204, 205, 205, 206, 206, 207,
                    207, 208, 208, 209, 209, 210, 210, 211, 211, 212,
                    212, 213, 213, 214, 214, 215, 215, 216, 216, 217,
                    217, 218, 218, 219, 219, 220, 220, 221, 221, 222,
                    222, 223, 223, 224, 224, 225, 225, 226, 226, 227,
                    227, 228, 228, 229, 229, 230, 230, 231, 231, 232,
                    232, 233, 233, 234, 234, 235, 235, 236, 236, 237,
                    237, 238, 238, 239, 239, 240, 240, 241, 241, 242,
                    242, 243, 243, 244, 244, 245, 245, 246, 246, 247,
                    247, 248, 248, 249, 249, 250, 250, 251, 251, 252,
                    252, 253, 253, 254, 255],
                    [255, 253, 252, 251, 250, 249, 248, 247, 246, 245,
                    244, 243, 242, 241, 240, 239, 238, 237, 236, 235,
                    234, 233, 232, 231, 230, 229, 228, 227, 226, 225,
                    224, 223, 222, 221, 220, 219, 218, 217, 216, 215,
                    214, 213, 212, 211, 210, 209, 208, 207, 206, 205,
                    204, 203, 202, 201, 200, 199, 198, 197, 196, 195,
                    194, 193, 192, 191, 190, 189, 188, 187, 186, 185,
                    184, 183, 182, 181, 180, 179, 178, 177, 176, 175,
                    174, 173, 172, 171, 170, 169, 168, 167, 166, 165,
                    164, 163, 162, 161, 160, 159, 158, 157, 156, 155,
                    154, 153, 152, 151, 150, 149, 148, 147, 146, 145,
                    144, 143, 142, 141, 140, 139, 138, 137, 136, 135,
                    134, 133, 132, 131, 130, 129, 128, 127, 126, 125,
                    124, 123, 122, 121, 120, 119, 118, 117, 116, 115,
                    114, 113, 112, 111, 110, 109, 108, 107, 106, 105,
                    104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93,
                    92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80,
                    79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67,
                    66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54,
                    53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41,
                    40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28,
                    27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15,
                    14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                    [127, 126, 126, 125, 125, 124, 124, 123, 123, 122,
                     122, 121, 121, 120, 120, 119, 119, 118, 118, 117,
                     117, 116, 116, 115, 115, 114, 114, 113, 113, 112,
                     112, 111, 111, 110, 110, 109, 109, 108, 108, 107,
                     107, 106, 106, 105, 105, 104, 104, 103, 103, 102,
                     102, 101, 101, 100, 100, 99, 99, 98, 98, 97, 97,
                     96, 96, 95, 95, 94, 94, 93, 93, 92, 92, 91, 91, 90,
                     90, 89, 89, 88, 88, 87, 87, 86, 86, 85, 85, 84, 84,
                     83, 83, 82, 82, 81, 81, 80, 80, 79, 79, 78, 78, 77,
                     77, 76, 76, 75, 75, 74, 74, 73, 73, 72, 72, 71, 71,
                     70, 70, 69, 69, 68, 68, 67, 67, 66, 66, 65, 65, 64,
                     64, 63, 63, 62, 62, 61, 61, 60, 60, 59, 59, 58, 58,
                     57, 57, 56, 56, 55, 55, 54, 54, 53, 53, 52, 52, 51,
                     51, 50, 50, 49, 49, 48, 48, 47, 47, 46, 46, 45, 45,
                     44, 44, 43, 43, 42, 42, 41, 41, 40, 40, 39, 39, 38,
                     38, 37, 37, 36, 36, 35, 35, 34, 34, 33, 33, 32, 32,
                     31, 31, 30, 30, 29, 29, 28, 28, 27, 27, 26, 26, 25,
                     25, 24, 24, 23, 23, 22, 22, 21, 21, 20, 20, 19, 19,
                     18, 18, 17, 17, 16, 16, 15, 15, 14, 14, 13, 13, 12,
                     12, 11, 11, 10, 10, 9, 9, 8, 8, 7, 7, 6, 6, 5, 5,
                     4, 4, 3, 3, 2, 2, 1, 1, 0, 0]]).T / 255.

redblue_light = np.array([[127, 136, 145, 154, 163, 173, 182, 191, 200,
                        209, 218, 227, 236, 245, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 255, 255, 255, 255, 255, 255,
                        255, 255, 255, 246, 238, 230, 222, 213, 205,
                        197, 189, 180, 172, 164, 156, 148, 139, 131,
                        123, 115, 106, 98, 90, 82, 74, 65, 57, 49, 41,
                        32, 24, 16, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            8, 16, 24, 32, 41, 49, 57, 65, 74, 82, 90, 98,
                            106, 115, 123, 131, 139, 148, 156, 164, 172,
                            180, 189, 197, 205, 213, 222, 230, 238, 246,
                            255, 255, 246, 238, 230, 222, 213, 205, 197,
                            189, 180, 172, 164, 156, 148, 139, 131, 123,
                            115, 106, 98, 90, 82, 74, 65, 57, 49, 41, 32,
                            24, 16, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            8, 16, 24, 32, 41, 49, 57, 65, 74, 82, 90, 98,
                            106, 115, 123, 131, 139, 148, 156, 164, 172,
                            180, 189, 197, 205, 213, 222, 230, 238, 246,
                            255, 255, 255, 255, 255, 255, 255, 255, 255,
                            255, 255, 255, 255, 255, 255, 255, 255, 255,
                            255, 255, 255, 255, 255, 255, 255, 255, 255,
                            255, 255, 255, 255, 255, 255, 255, 245, 236,
                            227, 218, 209, 200, 191, 182, 173, 163, 154,
                            145, 136, 127]]).T / 255.

redblue_dark = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26,
                        28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50,
                        52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74,
                        76, 78, 80, 82, 85, 87, 89, 91, 93, 95, 97, 99,
                        101, 103, 105, 107, 109, 111, 113, 115, 117, 119,
                        121, 123, 125, 127, 129, 131, 133, 135, 137, 139,
                        141, 143, 145, 147, 149, 151, 153, 155, 157, 159,
                        161, 163, 165, 167, 170, 172, 174, 176, 178, 180,
                        182, 184, 186, 188, 190, 192, 194, 196, 198, 200,
                        202, 204, 206, 208, 210, 212, 214, 216, 218, 220,
                        222, 224, 226, 228, 230, 232, 234, 236, 238, 240,
                        242, 244, 246, 248, 250, 252, 255],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [255, 252, 250, 248, 246, 244, 242, 240, 238,
                            236, 234, 232, 230, 228, 226, 224, 222, 220,
                            218, 216, 214, 212, 210, 208, 206, 204, 202,
                            200, 198, 196, 194, 192, 190, 188, 186, 184,
                            182, 180, 178, 176, 174, 172, 170, 167, 165,
                            163, 161, 159, 157, 155, 153, 151, 149, 147,
                            145, 143, 141, 139, 137, 135, 133, 131, 129,
                            127, 125, 123, 121, 119, 117, 115, 113, 111,
                            109, 107, 105, 103, 101, 99, 97, 95, 93, 91,
                            89, 87, 85, 82, 80, 78, 76, 74, 72, 70, 68, 66,
                            64, 62, 60, 58, 56, 54, 52, 50, 48, 46, 44, 42,
                            40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18,
                            16, 14, 12, 10, 8, 6, 4, 2, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]).T / 255.

ctopo = np.array([[255, 251, 247, 243, 240, 236, 232, 228, 225, 221, 217,
                213, 210, 206, 202, 198, 195, 191, 187, 183, 180, 176,
                172, 168, 165, 161, 157, 153, 150, 146, 142, 138, 135,
                131, 127, 124, 120, 116, 112, 109, 105, 101, 97, 94, 90,
                86, 82, 79, 75, 71, 67, 64, 60, 56, 52, 49, 45, 41, 37,
                34, 30, 26, 22, 19, 15, 11],
                [253, 251, 249, 246, 244, 242, 240, 238, 236, 234, 232,
                 230, 227, 225, 223, 221, 219, 217, 215, 213, 211, 208,
                 206, 204, 202, 200, 198, 196, 194, 192, 190, 187, 185,
                 183, 181, 179, 177, 175, 173, 171, 168, 166, 164, 162,
                 160, 158, 156, 154, 152, 149, 147, 145, 143, 141, 139,
                 137, 135, 133, 131, 128, 126, 124, 122, 120, 118, 116],
                 [145, 143, 140, 138, 136, 134, 131, 129, 127, 125, 122,
                 120, 118, 116, 114, 111, 109, 107, 105, 102, 100, 98,
                 96, 93, 91, 89, 87, 84, 82, 80, 78, 76, 73, 71, 69,
                 67, 64, 62, 60, 58, 55, 53, 51, 49, 46, 44, 42, 40,
                 38, 35, 33, 31, 29, 26, 24, 22, 20, 17, 15, 13, 11,
                 8, 6, 4, 2, 0]]).T / 255.

odv = np.array([0.9360, 0.7790, 0.9390,
                0.9200, 0.6910, 0.9160,
                0.9040, 0.5740, 0.8900,
                0.8880, 0.4750, 0.8650,
                0.8720, 0.3960, 0.8410,
                0.8580, 0.3100, 0.8190,
                0.8450, 0.2840, 0.8010,
                0.8300, 0.3190, 0.7790,
                0.8140, 0.4120, 0.7600,
                0.7930, 0.4870, 0.7500,
                0.7730, 0.5640, 0.7510,
                0.7380, 0.6060, 0.7630,
                0.6920, 0.6150, 0.7910,
                0.6210, 0.5900, 0.8310,
                0.5430, 0.5260, 0.8780,
                0.4490, 0.4420, 0.9170,
                0.3500, 0.3400, 0.9610,
                0.2760, 0.2630, 0.9930,
                0.2000, 0.2370, 1.0000,
                0.1470, 0.2450, 0.9920,
                0.1070, 0.2690, 0.9660,
                0.0970, 0.3160, 0.9450,
                0.1030, 0.3790, 0.9290,
                0.1310, 0.4490, 0.9220,
                0.1690, 0.5360, 0.9300,
                0.2170, 0.6030, 0.9500,
                0.2710, 0.6880, 0.9730,
                0.3260, 0.7550, 0.9900,
                0.3760, 0.8100, 0.9910,
                0.4180, 0.8710, 0.9690,
                0.4500, 0.9110, 0.9390,
                0.4680, 0.9380, 0.8960,
                0.4720, 0.9490, 0.8580,
                0.4620, 0.9440, 0.8150,
                0.4390, 0.9260, 0.7640,
                0.4030, 0.8940, 0.7040,
                0.3570, 0.8560, 0.6380,
                0.3060, 0.8170, 0.5730,
                0.2520, 0.7830, 0.5140,
                0.2000, 0.7580, 0.4630,
                0.1510, 0.7470, 0.4190,
                0.1080, 0.7500, 0.3790,
                0.0720, 0.7700, 0.3420,
                0.0440, 0.8020, 0.3060,
                0.0230, 0.8440, 0.2660,
                0.0150, 0.8750, 0.2360,
                0.0180, 0.8960, 0.2100,
                0.0300, 0.9070, 0.1890,
                0.0530, 0.9050, 0.1740,
                0.0860, 0.8900, 0.1660,
                0.1260, 0.8660, 0.1670,
                0.1710, 0.8400, 0.1750,
                0.2180, 0.8160, 0.1920,
                0.2650, 0.7970, 0.2160,
                0.3110, 0.7850, 0.2460,
                0.3550, 0.7790, 0.2790,
                0.3970, 0.7800, 0.3130,
                0.4380, 0.7870, 0.3450,
                0.4770, 0.8020, 0.3720,
                0.5160, 0.8240, 0.3940,
                0.5550, 0.8510, 0.4070,
                0.5960, 0.8810, 0.4110,
                0.6400, 0.9100, 0.4060,
                0.6860, 0.9330, 0.3930,
                0.7360, 0.9470, 0.3720,
                0.7860, 0.9490, 0.3440,
                0.8350, 0.9350, 0.3110,
                0.8900, 0.9040, 0.2680,
                0.9300, 0.8640, 0.2320,
                0.9600, 0.8220, 0.1990,
                0.9790, 0.7910, 0.1700,
                0.9890, 0.7570, 0.1460,
                0.9940, 0.7330, 0.1250,
                0.9970, 0.7100, 0.1070,
                0.9990, 0.6820, 0.0910,
                1.0000, 0.6550, 0.0760,
                1.0000, 0.6330, 0.0630,
                0.9990, 0.6040, 0.0510,
                0.9930, 0.5800, 0.0400,
                0.9830, 0.5560, 0.0310,
                0.9670, 0.5310, 0.0220,
                0.9460, 0.5080, 0.0160,
                0.9220, 0.4800, 0.0100,
                0.8980, 0.4500, 0.0050,
                0.8770, 0.4180, 0.0020,
                0.8640, 0.3840, 0.0000,
                0.8630, 0.3480, 0.0000,
                0.8790, 0.3040, 0.0010,
                0.9080, 0.2680, 0.0030,
                0.9430, 0.2260, 0.0080,
                0.9730, 0.1700, 0.0140,
                0.9920, 0.1200, 0.0210,
                0.9970, 0.0710, 0.0300,
                0.9880, 0.0310, 0.0400,
                0.9650, 0.0050, 0.0510,
                0.9310, 0.0000, 0.0650,
                0.8940, 0.0000, 0.0810,
                0.8630, 0.0050, 0.0980,
                0.8440, 0.0160, 0.1180,
                0.8360, 0.0320, 0.1400,
                0.8370, 0.0540, 0.1650,
                0.8430, 0.0840, 0.1930,
                0.8530, 0.1240, 0.2240,
                0.8670, 0.1740, 0.2560,
                0.8840, 0.2330, 0.2890,
                0.9050, 0.3010, 0.3200,
                0.9290, 0.3770, 0.3520,
                0.9530, 0.4590, 0.3870,
                0.9770, 0.5460, 0.4280,
                0.9970, 0.6340, 0.4730,
                1.0000, 0.7140, 0.5190,
                1.0000, 0.7750, 0.5610,
                1.0000, 0.7840, 0.5680]).reshape((-1, 3))


cm = Bunch()
cm['phasemap'] = cmat2cmpl(phasemap)
cm['phasemap_r'] = cmat2cmpl(_reverse_cm(phasemap))
cm['zebra'] = cmat2cmpl(zebra)
cm['zebra_r'] = cmat2cmpl(_reverse_cm(zebra))
cm['avhrr'] = cmat2cmpl(avhrr)
cm['avhrr_r'] = cmat2cmpl(_reverse_cm(avhrr))
cm['cbathy'] = cmat2cmpl(cbathy)
cm['cbathy_r'] = cmat2cmpl(_reverse_cm(cbathy))
cm['coolavhrrmap'] = cmat2cmpl(coolavhrrmap)
cm['coolavhrrmap_r'] = cmat2cmpl(_reverse_cm(coolavhrrmap))
cm['rscolmap'] = cmat2cmpl(rscolmap)
cm['rscolmap_r'] = cmat2cmpl(_reverse_cm(rscolmap))
cm['redgreen'] = cmat2cmpl(redgreen)
cm['redgreen_r'] = cmat2cmpl(_reverse_cm(redgreen))
cm['redblue_light'] = cmat2cmpl(redblue_light)
cm['redblue_light_r'] = cmat2cmpl(_reverse_cm(redblue_light))
cm['redblue_dark'] = cmat2cmpl(redblue_dark)
cm['redblue_dark_r'] = cmat2cmpl(_reverse_cm(redblue_dark))
cm['ctopo'] = cmat2cmpl(ctopo)
cm['ctopo_r'] = cmat2cmpl(_reverse_cm(ctopo))
cm['odv'] = cmat2cmpl(odv)
cm['odv_r'] = cmat2cmpl(_reverse_cm(odv))
