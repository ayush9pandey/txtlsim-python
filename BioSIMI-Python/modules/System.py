# Import all required libraries
from modules.Subsystem import *

latestLevel = 3
latestVersion = 1

class System(object):
    # latest SBML level and version
    def __init__(self, SystemName):
        self.SystemName = SystemName
        self.ListOfInternalSubsystems = []
        self.ListOfExternalSubsystems = []
        self.ListOfMembraneSubsystems = [] 
        self.ListOfSharedResources = []
        self.Size = 0
        self.ExternalSystemFlag = 'external'
        self.ExternalSystem = self
    
    def getSystemName(self):
        ''' 
        Returns the system name attribute
        '''
        return self.SystemName

    def setSystemName(self, name):
        ''' 
        Renames the system name and puts all subsystems 
        currently in the system inside the compartment with 
        this new name 
        '''
        for subsystem in self.ListOfInternalSubsystems:
            subsystem.setCompartments([name])
        self.SystemName = name

    def getListOfSubsystems(self):
        ''' 
        Returns the list of subsystem objects in 
        the system 
        '''
        return self.ListOfInternalSubsystems
    
    def getListOfSharedResources(self):
        ''' 
        Returns the list of shared resources
        '''
        return self.ListOfSharedResources

    def appendSharedResources(self, list):
        ''' 
        Append the list of resources to the 
        self.ListOfSharedResources 
        '''
        for element in list:
            if type(element) is str: 
                self.ListOfSharedResources.append(element)
            else:
                raise ValueError('List element {0} is not a string'.format(element))
    
    def removeSharedResource(self, resource):
        ''' 
        Remove the given resource name from
        self.ListOfSharedResources
        '''
        if type(resource) is str and resource in self.ListOfSharedResources:
            self.ListOfSharedResources.remove(resource)

    def setSize(self, size):
        '''
        Sets the size of the System compartment to given size (float)
        ''' 
        self.Size = size
    
    def getSize(self):
        '''
        Returns the size of the System compartment
        '''
        return self.Size

    def setSharedResources(self, mode = 'virtual'):
        ''' 
        Returns a new Subsystem object containing the 
        model which shares the self.ListOfSharedResources among 
        self.ListOfSubsystems
        '''
        ListOfResources = self.ListOfSharedResources
        ListOfSubsystems = self.ListOfInternalSubsystems
        shared_subsystem =  createNewSubsystem()
        shared_subsystem.setSystem(self)
        # Usage - self.shareSubsystems(ListOfSubsystems, ListOfSharedResources)
        shared_subsystem.shareSubsystems(ListOfSubsystems, ListOfResources, mode)
        return shared_subsystem

    def createSubsystem(self, filename, subsystemName = ''):
        ''' 
        Creates a new Subsystem object inside the System
        with the SubsystemName suffixed to all elements of the given SBML filename
        '''
    # 1. Read the SBML model
    # 2. Create an object of the Subsystem class with the SBMLDocument read in Step 1
        name = self.getSystemName()
        sbmlDoc = getFromXML(filename)
        model = sbmlDoc.getModel()
        subsystem = Subsystem(sbmlDoc)
        subsystem.setSystem(self)
        if subsystem.getSubsystemDoc().getLevel() != latestLevel or subsystem.getSubsystemDoc().getVersion() != latestVersion:
            warnings.warn('Subsystem SBML model is not the latest. Converting to SBML level 3, version 1')
            subsystem.convertSubsystemLevelAndVersion(latestLevel,latestVersion)
        subsystem.suffixAllElementIds(subsystemName)
        if model.getNumCompartments() == 0:
            warnings.warn('No compartments in the Subsystem model, the System compartment will be used. Compartment Size will be set to zero for this Subsystem.')
        elif model.getNumCompartments() > 1:
            warnings.warn('More than 1 compartments in the Subsystem model. Check resulting models for consistency.')

        if not model.getCompartment(0).isSetSize():
            warnings.warn('Compartment Size is not set. Setting to one.')
            model.getCompartment(0).setSize(1)
    
        subsystem.setCompartments([name])
        self.ListOfInternalSubsystems.append(subsystem)
        self.Size += model.getCompartment(0).getSize()
        return subsystem 

    def createNewSubsystem(self, level = latestLevel, version = latestVersion):
        '''
        Creates a new empty Subsystem object with SBMLDocument 
        of given level and version
        '''
        newDocument = createSbmlDoc(level,version)
        subsystem = Subsystem(newDocument)
        subsystem.setSystem(self)
        return subsystem
    
    def setInternal(self,ListOfSubsystems):
        if type(ListOfSubsystems) is not list:
            if type(ListOfSubsystems) is not Subsystem:
                raise SyntaxError('The ListOfSubsystems argument should be a Subsystem object.')
            elif type(ListOfSubsystems) is Subsystem:
                sub = ListOfSubsystems
                ListOfSubsystems = []
                ListOfSubsystems.append(sub)
            else:
                raise SyntaxError('The ListOfSubsystems argument should either be a list of Subsystem objects or a single Subsystem object.')

        for sub in ListOfSubsystems:
            if type(sub) is not Subsystem:
                raise SyntaxError('All items of argument to setInternal must be Subsystem objects.')
            model = sub.getSubsystemDoc().getModel()
            compartments = model.getNumCompartments()
            if compartments > 1:
                raise SyntaxError('The subsystem model has more than one compartments. This may lead to errors as it is expected that a subsystem model only has one compartment. To model multiple compartments, make different system objects for different compartment names. Refer to the wiki for more information')
            sub.setSystem(self)
            sub.setCompartments(self.SystemName + '_internal')
            self.ListOfInternalSubsystems.append(sub)
    
    def setExternal(self, ListOfSubsystems):
        if type(ListOfSubsystems) is System:
            externalSystem = ListOfSubsystems
            self.ListOfExternalSubsystems = externalSystem.ListOfInternalSubsystems
            # Set the external compartment of the membrane of this system equal to the internal of the 'externalSubsystem' variable
            self.ExternalSystemFlag = 'system'
            self.ExternalSystem = externalSystem 
            return self.ListOfExternalSubsystems
        
        if type(ListOfSubsystems) is not list:
                if type(ListOfSubsystems) is not Subsystem:
                    raise SyntaxError('The ListOfSubsystems argument should be a Subsystem object.')
                elif type(ListOfSubsystems) is Subsystem:
                    sub = ListOfSubsystems
                    ListOfSubsystems = []
                    ListOfSubsystems.append(sub)
                else:
                    raise SyntaxError('The ListOfSubsystems argument should either be a list of Subsystem objects or a single Subsystem object.')

        for sub in ListOfSubsystems:
            if type(sub) is not Subsystem:
                raise SyntaxError('All elements of the ListOfSubsystem argument should be Subsystem objects')
            model = sub.getSubsystemDoc().getModel()
            compartments = model.getNumCompartments()
            if compartments > 1:
                raise SyntaxError('The subsystem model has more than one compartments. This may lead to errors as it is expected that a subsystem model only has one compartment. To model multiple compartments, make different system objects for different compartment names. Refer to the wiki for more information')
            sub.setCompartments(self.SystemName + '_external')
            self.ListOfExternalSubsystems.append(sub)

    def setMembrane(self, subsystem):
        if type(subsystem) is not Subsystem:
            raise SyntaxError('The argument should be a Subsystem object.')
        self.ListOfMembraneSubsystems.append(subsystem)
        model = subsystem.getSubsystemDoc().getModel()
        numComp = model.getNumCompartments()
        if numComp != 2:
            raise SyntaxError('A membrane subsystem must have exactly two compartments')
        elif numComp == 2:
            comp1 = model.getCompartment(0)
            comp2 = model.getCompartment(1)
            if comp1.getName() == 'internal' and comp2.getName() == 'external':
                if self.ExternalSystemFlag == 'system':
                    subsystem.setCompartments([self.SystemName + '_internal',self.ExternalSystem.SystemName + '_internal'])
                else:
                    subsystem.setCompartments([self.SystemName + '_internal',self.SystemName + '_external'])
            elif comp2.getName() == 'internal' and comp1.getName() == 'external':
                if self.ExternalSystemFlag == 'system':
                    subsystem.setCompartments([self.ExternalSystem.SystemName + '_internal',self.SystemName + '_internal'])
                else:
                    subsystem.setCompartments([self.SystemName + '_external',self.SystemName + '_internal'])
            else:
                raise SyntaxError('The two compartments of the membrane subsystem must each have a name attribute, with names "internal" and "external"')

    def getModel(self, mode='virtual'):
        system_sbml = createNewSubsystem()
        internal_subsystems = self.ListOfInternalSubsystems
        external_subsystems = self.ListOfExternalSubsystems
        membranes = self.ListOfMembraneSubsystems
        system_sbml.combineSubsystems([internal_subsystems, external_subsystems, membranes],mode)
        return system_sbml.getSubsystemDoc()


def createNewSubsystem(level = latestLevel, version = latestVersion):
    '''
    Creates a new empty Subsystem object with SBMLDocument 
    of given level and version
    '''
    newDocument = createSbmlDoc(level,version)
    subsystem = Subsystem(newDocument)
    return subsystem

def createSubsystem(filename, subsystemName = ''):
    ''' 
    Creates a new Subsystem object inside the System
    with the SubsystemName suffixed to all elements of the given SBML filename
    '''
    # 1. Read the SBML model
    # 2. Create an object of the Subsystem class with the SBMLDocument read in Step 1
    sbmlDoc = getFromXML(filename)
    model = sbmlDoc.getModel()
    subsystem = Subsystem(sbmlDoc)
    if subsystem.getSubsystemDoc().getLevel() != latestLevel or subsystem.getSubsystemDoc().getVersion() != latestVersion:
        warnings.warn('Subsystem SBML model is not the latest. Converting to the latest SBML level and version')
        subsystem.convertSubsystemLevelAndVersion(latestLevel,latestVersion)
    subsystem.suffixAllElementIds(subsystemName)
    if model.getNumCompartments() == 0:
        warnings.warn('No compartments in the Subsystem model, the System compartment will be used. Compartment Size will be set to zero for this Subsystem.')
    elif model.getNumCompartments() > 1:
        print('The subsystem from ' + filename + ' has multiple compartments')
        warnings.warn('More than 1 compartments found in the Subsystem model. Check resulting models for consistency.')

    if not model.getCompartment(0).isSetSize():
        warnings.warn('Compartment Size attribute is not set. Setting to one.')
        model.getCompartment(0).setSize(1)

    return subsystem 

def combineSystems(ListOfSystems, mode = 'virtual'):
    newSS = createNewSubsystem()
    ListOfAllSubsystems = []
    if type(ListOfSystems) is not list:
        raise SyntaxError('The argument ListOfSystems should be a list of System objects')
    for sys in ListOfSystems:
        if type(sys) is not System:
            raise SyntaxError('All items of ListOfSystems argument should be System objects')
        ListOfAllSubsystems.append(sys.ListOfInternalSubsystems)
        ListOfAllSubsystems.append(sys.ListOfExternalSubsystems)
        ListOfAllSubsystems.append(sys.ListOfMembraneSubsystems)
    # Flatten the list out
    ListOfSubsystems = []
    for sublist in ListOfAllSubsystems:
        for sub in sublist:
            if type(sub) is Subsystem:
                ListOfSubsystems.append(sub)
            elif type(sub) is list:
                for s in sub:
                    if type(s) is not Subsystem:
                        raise SyntaxError('All items in list of subsystems should be Subsystem objects')
                    ListOfSubsystems.append(s)
            else:
                raise SyntaxError('All items in list of subsystems should be Subsystem object')
                
    # Remove duplicate elements from ListOfSubsystems
    subsystem_list_final = []
    for subsystem in ListOfSubsystems:
        if subsystem not in subsystem_list_final:
            subsystem_list_final.append(subsystem)
    newSS.combineSubsystems(subsystem_list_final, mode)
    return newSS.getSubsystemDoc()
