"""Texture segmentation based on

Jain and Farrokhnia, "Unsupervised texture segmentation using Gabor filters" (1991)

"""

from __future__ import division

import numpy as np
from scipy import ndimage as nd

from skimage.filter import gabor_kernel
from skimage.filter import gaussian_filter


def make_filter_bank(frequencies, thetas, bandwidths):
    """prepare filter bank of kernels"""
    # TODO: set MTF of each filter at (u, v) to 0
    # TODO: set sigma_x and sigma_y correctly
    kernels = []
    all_freqs = []
    for frequency in frequencies:
        for theta in thetas:
            for bandwidth in bandwidths:
                theta = theta * np.pi / 4.0
                kernel = np.real(gabor_kernel(frequency, theta=theta,
                                              bandwidth=bandwidth))
                kernels.append(kernel)
                all_freqs.append(frequency)
    return kernels, np.array(all_freqs)


def filter_image(image, kernels, frequencies, r2=0.95, select=True):
    """Computes all convolutions and discards some filtered images.

    Returns filtered images with the largest energies so that the
    coefficient of determiniation is >= ``r2``.

    """
    # TODO: faster in fourier domain?
    filtered = np.dstack(nd.convolve(image, kernel, mode='wrap')
                         for kernel in kernels)
    if not select:
        return filtered, frequencies
    energies = filtered.sum(axis=0).sum(axis=0)

    # sort from largest to smallest energy
    idx = np.argsort(energies)[::-1]
    filtered = filtered[:, :, idx]
    energies = energies[idx]
    total_energy = energies.sum()

    r2s = np.cumsum(energies) / energies.sum()
    k = np.searchsorted(r2s, r2)
    n_start = filtered.shape[2]
    return filtered[:, :, :k], frequencies[idx][:k]


def compute_features(filtered, frequencies,
                     proportion=0.5,
                     alpha=0.25):
    """Compute features for each filtered image.

    ``frequencies[i]`` is the center frequency of the Gabor filter
    that generated ``filtered[i]``.

    """
    # TODO: is this really what the paper means in formula 6?
    nonlinear = np.tanh(alpha * filtered)
    ncols = filtered.shape[1]
    sigmas = proportion * ncols / np.array(frequencies)
    features = np.dstack(gaussian_filter(nonlinear[:, :, i], sigmas[i])
                         for i in range(len(sigmas)))
    return features


def add_coordinates(features, spatial_importance=1.0):
    """Adds coordinates to each feature vector and normalizes."""
    n_rows, n_cols = features.shape[:2]
    coords = np.mgrid[:n_rows, :n_cols].swapaxes(0, 2).swapaxes(0, 1)
    features = np.dstack((features, coords))
    n_feats = features.shape[2]

    means = np.array(list(features[:, :, i].mean() for i in range(n_feats)))
    stds = np.array(list(features[:, :, i].std(ddof=1) for i in range(n_feats)))

    means = means.reshape(1, 1, -1)
    stds = stds.reshape(1, 1, -1)

    features = (features - means) / stds
    features[:, :, -2:] *= spatial_importance
    return features


def _get_freqs(img):
    n_cols = img.shape[1]
    next_pow2 = 2 ** int(np.ceil(np.log2(n_cols)))
    min_freq = next_pow2 / 4
    n_freqs = int(np.log2(min_freq)) + 2
    return list((2 ** i) * np.sqrt(2) for i in range(n_freqs))


def segment_textures(img, model):
    # TODO: these filter parameters are not correct
    frequencies = _get_freqs(img)
    thetas = np.arange(4)
    bandwidths = (0.1, 0.5, 1, 1.5, 2)
    kernels, all_freqs = make_filter_bank(frequencies, thetas, bandwidths)
    filtered, all_freqs = filter_image(img, kernels, all_freqs)
    features = compute_features(filtered, all_freqs)
    features = add_coordinates(features)
    n_feats = features.shape[-1]
    model.fit(features.reshape(-1, n_feats))
    return model.labels_.reshape(img.shape)
