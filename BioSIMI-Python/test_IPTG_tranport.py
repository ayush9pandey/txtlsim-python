import numpy as np
from modules.utilityFunctions import *
timepoints = np.linspace(0,14*60*60,100)
plotSbmlWithBioscrape('models/GFP.xml',0,timepoints,['protein deGFP*','protein lacItetramer'])