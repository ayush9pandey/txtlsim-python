# cds_tetr.py -  TetR protein definition
# RMM, 11 Aug 2018
#
# This file contains the model for the TetR protein.
#
# Copyright (c) 2018, Build-A-Cell. All rights reserved.
# See LICENSE file in the project root directory for details.

from ..dna import ProteinCDS

#! TODO: decide if this should be CDS_tetr
class cds_tetr(ProteinCDS):
    "DNA for TetR protein"
    def __init__(self, name='TetR', *args, **kwargs):
        ProteinCDS.__init__(self, name=name, *args, **kwargs, dimerize=True)

# Define a shorthand version for convenience
tetr = cds_tetr

