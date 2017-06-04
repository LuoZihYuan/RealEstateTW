""" Shared constants and functions accross modules """

import os

__all__ = ["__config__", "__hidden__", "__resources__"]

__config__ = os.path.abspath(os.path.join(__file__, os.pardir, "config"))
__hidden__ = os.path.abspath(os.path.join(__file__, os.pardir, ".RealEstate"))
__resources__ = os.path.abspath(os.path.join(__file__, os.pardir, "resources"))
