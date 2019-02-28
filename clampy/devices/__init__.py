from warnings import warn
from .ni import *
# Maybe these imports should not be automatic
try:
    from .multiclamp import *
except:
    warn('Failed to import the Multiclamp module')
try:
    from .axoclamp900A import *
except:
    warn('Failed to import the Axoclamp 900A module')