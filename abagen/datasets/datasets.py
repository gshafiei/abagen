# -*- coding: utf-8 -*-
"""
Functions for downloading the Allen Brain Atlas human microarray dataset.
"""

import os
from pkg_resources import resource_filename

from nibabel.volumeutils import Recoder

from .. import io
from .utils import _get_dataset_dir, _fetch_files

WELL_KNOWN_IDS = Recoder(
    (('9861', 'H0351.2001', '178238387', '157722636'),
     ('10021', 'H0351.2002', '178238373', '157723301'),
     ('12876', 'H0351.1009', '178238359', '157722290'),
     ('15496', 'H0351.1015', '178238266', '162021642'),
     ('14380', 'H0351.1012', '178238316', '157721937'),
     ('15697', 'H0351.1016', '178236545', '157682966')),
    fields=('subj', 'uid', 'url', 't1w',)
)

VALID_DONORS = sorted(WELL_KNOWN_IDS.value_set('subj')
                      | WELL_KNOWN_IDS.value_set('uid'))


def fetch_microarray(data_dir=None, donors=['9861'], resume=True, verbose=1,
                     convert=True):
    """
    Downloads the Allen Human Brain Atlas microarray expression dataset

    Parameters
    ----------
    data_dir : str, optional
        Directory where data should be downloaded and unpacked. Default:
        current directory
    donors : list, optional
        List of donors to download; can be either donor number or UID. Can also
        specify 'all' to download all available donors. Default: 9861
    resume : bool, optional
        Whether to resume download of a partly-downloaded file. Default: True
    verbose : int, optional
        Verbosity level (0 means no message). Default: 1
    convert : bool, optional
        Whether to convert downloaded CSV files into parquet format for faster
        loading in the future; only available if ``fastparquet`` and ``python-
        snappy`` are installed. Default: True

    Returns
    -------
    data : dict
        Dictionary with keys ['microarray', 'ontology', 'pacall', 'probes',
        'annotation'], where corresponding values are lists of filepaths to
        downloaded CSV files.

    References
    ----------
    Hawrylycz, M. J., Lein, E. S., Guillozet-Bongaarts, A. L., Shen, E. H., Ng,
    L., Miller, J. A., ... & Abajian, C. (2012). An anatomically comprehensive
    atlas of the adult human brain transcriptome. Nature, 489(7416), 391.
    """

    url = "https://human.brain-map.org/api/v2/well_known_file_download/{}"

    dataset_name = 'allenbrain'
    data_dir = _get_dataset_dir(dataset_name, data_dir=data_dir,
                                verbose=verbose)

    sub_files = ('MicroarrayExpression.csv',
                 'Ontology.csv', 'PACall.csv',
                 'Probes.csv', 'SampleAnnot.csv')
    n_files = len(sub_files)

    if donors is not None and (isinstance(donors, (list, tuple))):
        for n, sub_id in enumerate(donors):
            if sub_id not in VALID_DONORS:
                raise ValueError('You provided invalid subject id {0} in a'
                                 'list. Subjects must be selected in {1}.'
                                 .format(sub_id, VALID_DONORS))
            donors[n] = WELL_KNOWN_IDS[sub_id]  # convert to ID system
    elif donors == 'all':
        donors = WELL_KNOWN_IDS.value_set('subj')
    else:
        donors = []
    donors = sorted(set(donors), key=lambda x: int(x))  # avoid duplicates

    files = [
        (os.path.join('normalized_microarray_donor{}'.format(sub), fname),
         url.format(WELL_KNOWN_IDS.url[sub]),
         dict(uncompress=True,
              move=os.path.join('normalized_microarray_donor{}'.format(sub),
                                'donor{}.zip'.format(sub))))
        for sub in donors
        for fname in sub_files
    ]

    files = _fetch_files(data_dir, files, resume=resume, verbose=verbose)

    # if we want to convert files to parquet format it's good to do that now
    # this step is _already_ super long, so an extra 1-2 minutes is negligible
    if convert and io.use_parq:
        for fn in files[0::n_files] + files[2::n_files]:
            io._make_parquet(fn, convert_only=True)

    return dict(
        microarray=files[0::n_files],
        ontology=files[1::n_files],
        pacall=files[2::n_files],
        probes=files[3::n_files],
        annotation=files[4::n_files]
    )


def fetch_mri(data_dir=None, donors=['9861'], resume=True, verbose=1):
    """
    Downloads the Allen Human Brain Atlas T1w MRI images

    Parameters
    ----------
    data_dir : str, optional
        Directory where data should be downloaded and unpacked. Default:
        current directory
    donors : list, optional
        List of donors to download; can be either donor number or UID.
        Default: donor9861
    resume : bool, optional
        Whether to resume download of a partly-downloaded file. Default: True
    verbose : int, optional
        Verbosity level (0 means no message). Default: 1
    """

    raise NotImplementedError


def fetch_desikan_killiany(*args, **kwargs):
    """
    Fetches Desikan-Killiany atlas shipped with `abagen`

    Returns
    -------
    atlas : dict
        Dictionary with keys ['image', 'info'] pointing to atlas image
        (.nii.gz) and information (.csv) files

    References
    ----------
    Desikan, R. S., Ségonne, F., Fischl, B., Quinn, B. T., Dickerson, B. C.,
    Blacker, D., ... & Albert, M. S. (2006). An automated labeling system
    for subdividing the human cerebral cortex on MRI scans into gyral based
    regions of interest. Neuroimage, 31(3), 968-980.
    """
    # grab resource filenames
    image = resource_filename('abagen', 'data/atlas-desikankilliany.nii.gz')
    info = resource_filename('abagen', 'data/atlas-desikankilliany.csv')

    return dict(image=image, info=info)