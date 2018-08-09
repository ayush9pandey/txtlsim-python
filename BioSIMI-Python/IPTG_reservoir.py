##### Creating a membrane model for IPTG transport####

from modules.System import *
from modules.Subsystem import *
from modules.SimpleModel import *
from modules.NewReaction import *

IPTG = createNewSubsystem()

model = IPTG.createNewModel('IPTG_reservoir','second','mole','count')
simpleModel = SimpleModel(model)
per_second = simpleModel.createNewUnitDefinition('per_second',UNIT_KIND_SECOND,-1,0,1)
count = simpleModel.createNewUnitDefinition('count',UNIT_KIND_DIMENSIONLESS, 1, 0, 1)

simpleModel.createNewCompartment('env','env',1,'litre',True)


simpleModel.createNewSpecies( 'IPTG','env',100000,False,'count')


# Write to XML file 
writeSBML(IPTG.getSubsystemDoc(),'models/IPTG_reservoir.xml')
