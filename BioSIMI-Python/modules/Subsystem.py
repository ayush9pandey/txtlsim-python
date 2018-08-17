import libsbml 
import time
from modules.SimpleReaction import *
from modules.SimpleModel import *
from modules.setIdFromNames import *
from modules.utilityFunctions import *

class Subsystem(object):

    '''
    The Subsystem class can be used to create subsystems which are placeholders for one SBML model.
    Each Subsystem must have ONE compartment (except when it's a Subsystem for a membrane, in which case it will have two compartments which should be called 'internal', 'external')
    The methods in the Subsystem class can be used for - 
    0. Load SBMLDocuments to a Subsystem object.
    1. Using various utility functions to edit SBML models (such as renaming, identifier modifications etc.)
    2. Performing simple quasi-steady state approximations to reduce models
    3. Work with reversible and irreversible reactions in an SBML model
    4. Combine, merge, and connect different Subsystem objects (Refer to wiki for a detailed documentation)
    5. Simulate SBMLDocument objects (placed inside Subsystem objects) using different simulators such as COPASI, bioscrape, libSBMLsim
    '''

    def __init__(self, SBMLDocument, System = None):
        '''
        Initializes the Subsystem object with the SBMLDocument object 
        Initializes the System attribute which may store the System inside which this Subsystem is placed.
        '''
        check(SBMLDocument,'checking SBMLDocument object')
        self.SBMLDocument = SBMLDocument
        self.System = System
        
    def getSBMLDocument(self):
        '''
        Returns the SBMLDocument object of the Subsystem
        '''
        return self.SBMLDocument

    def setSBMLDocument(self, doc):
        '''
        The doc is set as the SBMLDocument of the Subsystem
        Returns the Subsystem object
        '''
        check(doc,'retreiving SBMLDocument object in self.setSBMLDocument')
        self.SBMLDocument = doc
        return self

    def setSystem(self,systemObj):
        '''
        Sets the systemObject argument as the System for this Subsystem and returns it
        '''
        self.System = systemObj
        return self.System


    def getSystem(self):
        '''
        Returns the System object in which the Subsystem is placed.
        '''
        return self.System

    def renameSName(self, ListOfOldNames, new_name):
        '''
        Search the SBMLDocument in this Subsystem for the ListOfOldNames and rename all such 
        components by the new_name. Returns the updated SBMLDocument object of this Subsystem.
        '''
        model = self.getSBMLDocument().getModel()
        check(model,'retreiving model from document in renameSName')
        mod_obj = SimpleModel(model)
        names = []
        if type(ListOfOldNames) is str:
            names.append(ListOfOldNames)
        elif type(ListOfOldNames) is list:
            names = ListOfOldNames[:]
        else:
            raise ValueError('The ListOfOldNames argument should either be a string or a list of strings')
        
        if type(new_name) is not str:
            raise ValueError('The new name attribute should be a string')

        for old_name in names:
            if type(old_name) is not str:
                raise ValueError('All species names should be string type')
            species = mod_obj.getSpeciesByName(old_name)
            if species == None:
                raise ValueError('No species named' + old_name + 'found.')
            if type(species) is list:
                warnings.warn('Multiple species found with the name' + old_name + '. Replacing all.')
                for sp in species:
                    check(sp.setName(new_name), 'setting the new name from rename to the list of species')
            else:
                check(species.setName(new_name), 'setting new name from rename function call')
        return self.getSBMLDocument()

    def convertSubsystemLevelAndVersion(self, newLevel, newVersion):
        '''
        Converts the SBMLDocument of this Subsytem to the newLevel and newVersion
        Returns the SBMLDocument object of the Subsystem with updated level and version.
        '''
        document = self.getSBMLDocument()
        check(document,'retreiving document object for subsystem in convert function')
        if type(newLevel) is not int or type(newVersion) is not int:
            raise ValueError('The arguments newLevel and newVersion must be integers')

        if newLevel == document.getLevel() and newVersion == document.getVersion():
            warnings.warn('The current SBMLDocument level and version are the same as the new level and version given')
            return

        config = ConversionProperties()
        if config != None:
            config.addOption('setLevelAndVersion')
        else:
            raise ValueError('Failed to call ConversionProperties')
        # Now, need to set the target level and version (to which to convert the document)
        # Use the setTargetNamespaces() object of the ConversionsProperties as follows.
        # First, need to create a new SBMLNamespaces object with the desired (target) level and version
        sbmlns = SBMLNamespaces(newLevel,newVersion)
        check(sbmlns, 'creating new sbml namespaces')
        # check(config.setTargetNamespaces(sbmlns),'setting target namespaces')
        config.setTargetNamespaces(sbmlns)
        # Use the SBMLDocument.convert(ConversionsProperties) syntax to convert
        check(document.convert(config),'converting document level and version')
        if newLevel == 3 and newVersion == 1:
            conv_status = document.checkL3v1Compatibility()
        elif newLevel == 2 and newVersion == 4:
            conv_status = document.checkL2v3Compatibility()
        elif newLevel == 2 and newVersion == 3:
            conv_status = document.checkL2v3Compatibility()
        elif newLevel == 2 and newVersion == 2:
            conv_status = document.checkL2v2Compatibility()
        elif newLevel == 2 and newVersion == 1:
            conv_status = document.checkL2v1Compatibility()
        if conv_status != 0:
            raise ValueError('SBML Level/Version conversion failed')
        return self.getSBMLDocument()

    def renameSId(self, oldSId, newSId): 
        '''
        Updates the SId from oldSId to newSId for any component of the Subsystem.
        Returns the SBMLDocument of the updated Subsystem
        '''

        # 
        # @file    renameSId.py
        # @brief   Utility program, renaming a specific SId 
        #          while updating all references to it.
        # @author  Frank T. Bergmann
        # 
        # <!--------------------------------------------------------------------------
        # This sample program is distributed under a different license than the rest
        # of libSBML.  This program uses the open-source MIT license, as follows:
        # 
        # Copyright (c) 2013-2018 by the California Institute of Technology
        # (California, USA), the European Bioinformatics Institute (EMBL-EBI, UK)
        # and the University of Heidelberg (Germany), with support from the National
        # Institutes of Health (USA) under grant R01GM070923.  All rights reserved.
        # 
        # Permission is hereby granted, free of charge, to any person obtaining a
        # copy of this software and associated documentation files (the "Software"),
        # to deal in the Software without restriction, including without limitation
        # the rights to use, copy, modify, merge, publish, distribute, sublicense,
        # and/or sell copies of the Software, and to permit persons to whom the
        # Software is furnished to do so, subject to the following conditions:
        # 
        # The above copyright notice and this permission notice shall be included in
        # all copies or substantial portions of the Software.
        # 
        # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
        # THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
        # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
        # DEALINGS IN THE SOFTWARE.
        # 
        # Neither the name of the California Institute of Technology (Caltech), nor
        # of the European Bioinformatics Institute (EMBL-EBI), nor of the University
        # of Heidelberg, nor the names of any contributors, may be used to endorse
        # or promote products derived from this software without specific prior
        # written permission.
        # ------------------------------------------------------------------------ -->
        # 

        if oldSId == newSId:
            print("The Ids are identical, renaming stopped.")
            return

        if not libsbml.SyntaxChecker.isValidInternalSId(newSId):
            print("The new SId '{0}' does not represent a valid SId.".format(newSId))
            return

        document = self.getSBMLDocument()
        check(document,'retreiving document from subsystem in renameSId')
        element = document.getElementBySId(oldSId)

        if element == None:
            print("Found no element with SId '{0}' in subsystem {1}".format(oldSId,document.getModel().getId()))
            return
        
        # found element -> renaming
        check(element.setId(newSId),'setting new SId in renameSId')


        # update all references to this element
        allElements = document.getListOfAllElements()
        check(allElements,'getting list of all elements in renameSId')
        for i in range(allElements.getSize()):
            current = allElements.get(i)
            current.renameSIdRefs(oldSId, newSId)
        return document 

    def getAllIds(self):
        """ 
        Returns SIds of all components in this Subsystem in string format
        """
        document = self.getSBMLDocument()
        check(document,'retreiving document from subsystem in getAllIds')
        allElements = document.getListOfAllElements()
        result = []
        if (allElements == None or allElements.getSize() == 0):
            return result 
        for i in range (allElements.getSize()):
            current = allElements.get(i) 
            if (current.isSetId() and current.getTypeCode() != libsbml.SBML_EVENT and current.getTypeCode() != libsbml.SBML_LOCAL_PARAMETER):
                result.append(current.getId()) 
        return result     
    
    def suffixAllElementIds(self, name):
        '''
        All elements identifiers in the
        SBMLDocument of this Subsystem are suffixed with name.
        Returns the SBMLDocument of the Subsystem.
        '''
        document = self.getSBMLDocument()
        check(document,'retreiving document from subsystem in suffixAllElements')
        allids = self.getAllIds()
        if type(name) is not str:
            raise ValueError('The name argument should be string type')
            
        for oldid in allids:
            if document.getElementBySId(oldid) != None:
                self.renameSId(oldid, oldid + '_' + name)

        ## Use if want to suffix all Name arguments too
        # elements = document.getListOfAllElements()
        # for element in elements:
        #     if element.isSetName():
        #         oldname = element.getName()
        #         newname = oldname + '_' + name
        #         element.setName(newname)

        return document

    def setCompartments(self, newCompartments):
        '''
    	The newCompartments list is set as the new ListOfCompartments 
        in theSBMLDocument of this Subsystem
        Returns the updated SBMLDocument 
        '''
        document = self.getSBMLDocument()
        check(document,'retreiving document from subsystem in setSubsystemCompartments')
        compartments = document.getModel().getListOfCompartments()
        check(compartments,'retreiving list of compartments in setSubsystemCompartments')
        if type(newCompartments) is not list:
            if type(newCompartments) is str:
                newcomp = newCompartments
                newCompartments = []
                newCompartments.append(newcomp)
            else:
                raise ValueError('The newCompartments argument should be a list of strings or a single string')

        if len(compartments) != len(newCompartments):
            warnings.warn('The number of compartments given is not the same as the number of compartments in the model.') 
            for i in range(len(newCompartments)):
                # rename compartment name and id
                if compartments.get(i).isSetName():
                    status = compartments.get(i).setName(newCompartments[i])
                    check(status, 'setting name of compartment in setSubsystemCompartment')
                oldid = compartments.get(i).getId()
                check(oldid,'retreiving oldid in setSubsystemCompartments')
                self.renameSId(oldid,newCompartments[i])   
   
        else:
            for i in range(len(compartments)):
                # rename compartment name and id
                if compartments.get(i).isSetName():
                    status = compartments.get(i).setName(newCompartments[i])
                    check(status, 'setting name of compartment in setSubsystemCompartments')
                oldid = compartments.get(i).getId()
                check(oldid,'retreiving oldid in setSubsystemCompartments')
                self.renameSId(oldid,newCompartments[i])   
        return self.getSBMLDocument()
   
    def createNewModel(self, modelId, timeUnits, extentUnits, substanceUnits):
        '''
        Creates a new Model object in the SBMLDocument of this Subsystem 
        with the given attributes. 
        Returns the libSBML Model object created.
        '''
        model = self.getSBMLDocument().createModel()
        if model == None:
            print('Unable to create Model object.')
            sys.exit(1)
        status = model.setId(modelId)
        if status != LIBSBML_OPERATION_SUCCESS:
            print('Unable to set identifier on the Model object')
            sys.exit(1)
        check(model.setTimeUnits(timeUnits), 'set model-wide time units')
        check(model.setExtentUnits(extentUnits), 'set model units of extent')
        check(model.setSubstanceUnits(substanceUnits),
              'set model substance units')
        return model

    def mergeSubsystemModels(self, ListOfSubsystems):
        '''
        The ListOfSubsystems are merged together. All components are 
        merged together except the Species.
        Helper function which is used in other methods. 
        Returns the SBMLDocument of the merged Subsystem 
        '''
        # The following are merged : 
        # functions, units, compartments, species, parameters, 
        # initial assignments, rules, constraints, reactions, and events
        document = self.getSBMLDocument()
        check(document,'retreiving document in mergeSubsystem')
        model_base = ListOfSubsystems[0].getSBMLDocument().getModel()
        check(model_base,'retreiving model in mergeSubsystems')
        model = self.createNewModel('merged_model',model_base.getTimeUnits(), model_base.getExtentUnits(), model_base.getSubstanceUnits())
        check(document.setModel(model),'setting model for document in mergeSubsystem')
        for subsystem in ListOfSubsystems:
            if type(subsystem) is not Subsystem:
                raise ValueError('All items of the ListOfSubsystems argument should be of Subsystem class')
            mod = subsystem.getSBMLDocument().getModel()
            check(mod,'retreiving model in mergeSubsystem')
            # Obsolete in SBML Level 3 
            # if mod.getNumCompartmentTypes() != 0:
            #     for each_compartmentType in mod.getListOfCompartmentType():
            #         model.addCompartmentType(each_compartmentType)
            if mod.getNumConstraints() != 0:
                for each_constraint in mod.getListOfConstraints():
                    model.addConstraint(each_constraint)
            if mod.getNumInitialAssignments() != 0:
                for each_initialAssignment in mod.getListOfInitialAssignments():
                    model.addInitialAssignment(each_initialAssignment)
            if mod.getNumFunctionDefinitions() != 0:
                for each_functionDefinition in mod.getListOfFunctionDefinitions():
                    model.addFunctionDefinition(each_functionDefinition)
            if mod.getNumRules() != 0:
                for each_rule in mod.getListOfRules():
                    model.addRule(each_rule)
            if mod.getNumEvents() != 0:
                for each_event in mod.getListOfEvents():
                    model.addEvent(each_event)
            if mod.getNumCompartments() != 0:
                for each_compartment in mod.getListOfCompartments():
                    model.addCompartment(each_compartment)
            if mod.getNumParameters() != 0:
                for each_parameter in mod.getListOfParameters():
                    model.addParameter(each_parameter)
            if mod.getNumUnitDefinitions() != 0:
                for each_unit in mod.getListOfUnitDefinitions():
                    model.addUnitDefinition(each_unit)
            if mod.getNumReactions() != 0:
                for each_reaction in mod.getListOfReactions():
                    model.addReaction(each_reaction)
            model.setAreaUnits(mod.getAreaUnits())
            model.setExtentUnits(mod.getExtentUnits())
            model.setLengthUnits(mod.getLengthUnits())
            model.setSubstanceUnits(mod.getSubstanceUnits())
            model.setTimeUnits(mod.getTimeUnits())
            model.setVolumeUnits(mod.getVolumeUnits())
        return self.getSBMLDocument()
   
    def shareSubsystems(self, ListOfSubsystems, ListOfSharedResources, mode = 'virtual', combineCall = False):
        '''
        Merges the ListOfSubsystems together along with all the Species. 
        The Species in ListOfSharedResources are combined together 
        and so are shared by all Subsystems among the ListOfSubsystems.
        Returns the combined SBMLDocument object of this Subsystem which stores the combined model
        The combineCall is an optional argument for internal use in the code.  
        '''
        # Merge all other components first and then add species 
        self.mergeSubsystemModels(ListOfSubsystems)
        model = self.getSBMLDocument().getModel()
        check(model,'retreiving model in shareSubsystems')
        model_obj = SimpleModel(model)
        mod_id = ''
        total_size = 0
        # combineCall is used to check whether the subsystems are being combined (coming from combineSubsystems(...))
        # or not. This changes the compartment size. For shared - the size is set as the total size of the System inside which the Subsystems are present.
        # whereas for a combineSubsystems call, the total size of the combined model is equal to the sum of the sizes of the compartments in the subsystems that are being combined.
        if not combineCall:
            total_size = self.getSystem().Size
        else:
            for subsystem in ListOfSubsystems:
                total_size += subsystem.getSBMLDocument().getModel().getCompartment(0).getSize()

        check(model.getCompartment(0).setSize(total_size), 'setting compartment size in model')
        final_species_hash_map = {}
        if mode == 'volume':
            # 'volume' mode combines species by setting their initial amounts
            # dependent on the volume of the compartments they are placed in 
            # and the inidividual initial amounts for all the species being combined 
            for subsystem in ListOfSubsystems:
                mod = subsystem.getSBMLDocument().getModel()
                check(mod,'retreiving subsystem model in shareSubsystems')
                mod_id += '_' + mod.getId()
                # if list of shared resources is empty, add all species directly
                if not ListOfSharedResources:
                    species_list = mod.getListOfSpecies()
                    check(species_list,'retreiving list of species of susbsytem model in shareSubsystems')
                    for species in species_list:
                        ssys_size = 0
                        cumulative_amount = 0
                        species_amount = 0
                        ssys_size = species.getModel().getCompartment(0).getSize()
                        cumulative_amount = (species.getInitialAmount())*ssys_size
                        species_amount = cumulative_amount/total_size
                        check(model.addSpecies(species),'adding species to the model when ListOfSharedResources is empty, in shareSubsystems')
                        check(model.getSpecies(species.getId()).setInitialAmount(species_amount),'setting initial amount to cumulative in shareSubsystems')
                else:
                    species_hash_map = {}
                    for species in mod.getListOfSpecies():
                        ssys_size = 0
                        cumulative_amount = 0
                        species_amount = 0
                        # species will only be combined if their name argument is same as the list of shared resources
                        species_name = species.getName()
                        check(species_name,'getting species name in shareSubsystems')
                        if species_name in ListOfSharedResources:
                        # Maintain the dictionary for all species in the input subsystems by their name
                            species_hash_map[species_name] = species
                        else:
                            ssys_size = species.getModel().getCompartment(0).getSize()
                            cumulative_amount = (species.getInitialAmount())*ssys_size
                            species_amount = cumulative_amount/total_size
                            check(model.addSpecies(species),'adding species to the model in shareSubsystems')
                            check(model.getSpecies(species.getId()).setInitialAmount(species_amount),'setting initial amount in shareSubsystems')
                    for species_name in species_hash_map:
                        if final_species_hash_map.get(species_name):
                            #If the final hash map already has that species then append to
                            # the same instead of duplicating
                            final_species_hash_map[species_name].append(
                                species_hash_map[species_name])
                        else:
                            # For all the species in the dictionary not already in the final
                            # hash map, save them to the final hash map dictionary.
                            final_species_hash_map[species_name] = [
                                species_hash_map[species_name]]

            # To find a valid id to a given name
            allids = self.getAllIds()
            trans = SetIdFromNames(allids)
            for unique_species_name in final_species_hash_map:
                ssys_size = 0
                cumulative_amount = 0
                species_amount = 0
                if len(final_species_hash_map[unique_species_name]) > 1: 
                    flag = 0
                    comp_dict = {}
                    for species in final_species_hash_map[unique_species_name]:
                        # To combine species only when they are in the same compartment
                        # when in different compartments, they will not be combined
                        if comp_dict.get(species.getId()):
                            comp_dict[species.getId()].append(species.getCompartment())
                        else:
                            comp_dict[species.getId()] = [species.getCompartment()]
                        
                    for spe_id in comp_dict:
                        if len(comp_dict[spe_id]) > 1:
                            # multiple compartments for a species
                            oldid = spe_id
                            allids = self.getAllIds()
                            trans = SetIdFromNames(allids)
                            newid = trans.getValidIdForName(spe_id)
                            self.renameSId(oldid, newid)
                            flag = 1
                    # we don't want this species to be combined
                    if flag:
                        continue

                    uni_sp = final_species_hash_map[unique_species_name][0]
                    # For any species with same name, as one of the species in the system's ListOfSharedResources
                    # which were present in more than one subsystem and in the same compartment
                    count = 0
                    for i in final_species_hash_map[unique_species_name]:
                        ssys_size = i.getModel().getCompartment(0).getSize()
                        cumulative_amount += (i.getInitialAmount())*ssys_size
                        species_amount = cumulative_amount/total_size
                        check(model.addSpecies(i),'add species to model in shareSubsystems')
                        oldid = i.getId()
                        check(oldid,'getting olid in shareSubsystems')
                        newid = trans.getValidIdForName(i.getName()) + '_shared'
                        self.renameSId(oldid, newid)
                        if count >= 1:
                            check(model.removeSpecies(newid),'removing species from the model in shareSubsystems')
                        count += 1
                    sp = model_obj.getSpeciesByName(uni_sp.getName())
                    if type(sp) is list: 
                        for sp_i in sp:
                            check(sp_i.setInitialAmount(species_amount),'setting initial amount to cumulative in shareSubsystems')
                    else:
                        check(sp.setInitialAmount(species_amount),'setting initial amount to cumulative in shareSubsystems')
                else:
                    # If there are no species with multiple occurence in different subsystems
                    # then just add the list of all species maintained in the final hash map
                    # to our new subsystem's list of species.
                    i = final_species_hash_map[unique_species_name][0]
                    check(model.addSpecies(i),'adding species to the model in shareSubsystems')
        elif mode == 'virtual':
            # 'virtual' mode combines species and assigns the species initial amount
            # to be equal to the initial amount of the particular species in the first Subsystem in the ListOfSubsystems given as argument
            # So, the first Subsystem in the list of subsystems should contain the correct initial amounts for all species and they are used.
            for subsystem in ListOfSubsystems:
                mod = subsystem.getSBMLDocument().getModel()
                check(mod,'retreiving subsystem model in shareSubsystems')
                mod_id += '_' + mod.getId()
                if not ListOfSharedResources:
                    species_list = mod.getListOfSpecies()
                    check(species_list,'retreiving list of species of susbsytem model in shareSubsystems')
                    for species in species_list:
                        check(model.addSpecies(species),'adding species to the model when ListOfSharedResources is empty, in shareSubsystems')
                else:
                    species_hash_map = {}
                    for species in mod.getListOfSpecies():
                        species_name = species.getName() 
                        check(species_name,'getting species name in shareSubsystems')
                        if species_name in ListOfSharedResources:
                            # Maintain the dictionary for all species in the input subsystems by their name
                            species_hash_map[species_name] = species
                        else:
                            check(model.addSpecies(species),'adding species to the model in shareSubsystems')
                    for species_name in species_hash_map:
                        if final_species_hash_map.get(species_name):
                            #If the final hash map already has that species then append to
                            # the same instead of duplicating
                            final_species_hash_map[species_name].append(
                                species_hash_map[species_name])
                        else:
                            # For all the species in the dictionary not already in the final
                            # hash map, save them to the final hash map dictionary.
                            final_species_hash_map[species_name] = [
                                species_hash_map[species_name]]

            allids = self.getAllIds()
            trans = SetIdFromNames(allids)
            for unique_species_name in final_species_hash_map:
                cumulative_amount = 0
                if len(final_species_hash_map[unique_species_name]) > 1: 
                    # For any species with same name 
                    # which were present in more than one subsystem
                    flag = 0
                    comp_dict = {}
                    for species in final_species_hash_map[unique_species_name]:
                        if comp_dict.get(species.getId()):
                            comp_dict[species.getId()].append(species.getCompartment())
                        else:
                            comp_dict[species.getId()] = [species.getCompartment()]
                        
                    for spe_id in comp_dict:
                        if len(comp_dict[spe_id]) > 1:
                            # multiple compartments for a species
                            oldid = spe_id
                            allids = self.getAllIds()
                            trans = SetIdFromNames(allids)
                            newid = trans.getValidIdForName(spe_id)
                            self.renameSId(oldid, newid)
                            flag = 1
                    # we don't want this species to be combined
                    if flag:
                        continue

                    count = 0
                    for i in final_species_hash_map[unique_species_name]:
                        check(model.addSpecies(i),'add species to model in shareSubsystems')
                        oldid = i.getId()
                        check(oldid,'getting olid in shareSubsystems')
                        newid = trans.getValidIdForName(i.getName()) + '_shared'
                        self.renameSId(oldid, newid)
                        if count >= 1:
                            check(model.removeSpecies(newid),'removing species from the model in shareSubsystems')
                        count += 1
                else:
                    # If there are no species with multiple occurence in different subsystems
                    # then just add the list of all species maintained in the final hash map
                    # to our new subsystem's list of species.
                    i = final_species_hash_map[unique_species_name][0]
                    check(model.addSpecies(i),'adding species to the model in shareSubsystems')

        # Updating model id
        check(model.setId('shared_subsystems_' + mod_id),'setting new model id for shared model')
        return self.getSBMLDocument()


    def combineSubsystems(self, ListOfSubsystems, mode = 'virtual', combineNames = True):
        '''
        Combines the ListOfSubsystems. 
	    Species with the same name together are combined, if combineNames is True. 
        The ListOfSharedResources of the System in which the Subsystem is placed 
        is used to share the Species in the list. Other Species are combined depending on 
        the combineNames (True or False)
        Returns the SBMLDocument object of this Subsystem which holds the combined model.
        '''
        # Flatten out the ListOfSubsystems argument 
        ListOfListOfSubsystems = []
        if type(ListOfSubsystems) is not list:
            raise ValueError('When combining subsystems, the ListOfSubsystems argument is expected to be a list of subystems')
        for subsystem in ListOfSubsystems:
            if type(subsystem) is list:
                for sub in subsystem:
                    ListOfListOfSubsystems.append(sub)
            elif type(subsystem) is Subsystem:
                ListOfListOfSubsystems.append(subsystem)
            else:
                raise ValueError('All elements of ListOfSubsystems argument should be Subsystem objects')
        
        ListOfSubsystems = []
        ListOfSubsystems = ListOfListOfSubsystems
        flag = 0
        for subsystem in ListOfSubsystems:
            if subsystem.getSystem() != ListOfSubsystems[0].getSystem():
                flag += 1
            if type(subsystem) is not Subsystem:
                raise ValueError('All objects in ListOfSubsystems input argument list should be of Subsystem class')
        if not flag:
            ListOfResources = ListOfSubsystems[0].getSystem().ListOfSharedResources
        else:
            ListOfResources = []
            warnings.warn('Not all of the Subsystems being combined are in the same Compartment')


        # Get the sharedSubsystem object to combine the species in ListOfSharedResources before combining all other species
        self.shareSubsystems(ListOfSubsystems,ListOfResources, mode, True)
        model = self.getSBMLDocument().getModel()
        check(model,'retreiving model in combineSubsystems')
        simpleModel = SimpleModel(model)
        mod_id = ''
        if mode == 'volume':
            if combineNames == False:
                total_size = 0
                for subsystem in ListOfSubsystems:
                    sub_model = subsystem.getSBMLDocument().getModel()
                    check(sub_model,'retreiving subsystem model in combineSubsystems')
                    mod_id += '_' + sub_model.getId()
                    total_size += sub_model.getCompartment(0).getSize()
            # The final species hash map is a dictionary for all the species that will be
            # in the final subsystem.
            if combineNames == True:
                final_species_hash_map = {}
                final_reaction_map = {}
                total_size = 0
                for subsystem in ListOfSubsystems:
                    sub_model = subsystem.getSBMLDocument().getModel()
                    total_size += sub_model.getCompartment(0).getSize()
                    mod_id += '_' + sub_model.getId()
                    # Finding duplicate species by name 
                    species_hash_map = {}
                    for species in sub_model.getListOfSpecies():
                        if species.getName() not in ListOfResources:
                        # Maintain the dictionary for all species in the subsystems by their name and compartment they are in
                            species_hash_map[species.getName()] = species
                    for species_name in species_hash_map:
                        if final_species_hash_map.get(species_name):
                            #If the final hash map already has that species then append to
                            # the same instead of duplicating
                            final_species_hash_map[species_name].append(
                                species_hash_map[species_name])
                        else:
                            # For all the species in the dictionary not already in the final
                            # hash map, save them to the final hash map dictionary.
                            final_species_hash_map[species_name] = [
                                species_hash_map[species_name]]

                   # Finding duplicate reactions by the reaction string
                    reaction_map = {}
                    for reaction in sub_model.getListOfReactions():
                        rc1_list = reaction.getListOfReactants()
                        pt1_list = reaction.getListOfProducts()
                        rStr = ''
                        for i in range(len(rc1_list)):
                            sref = rc1_list[i]
                            rStr += sub_model.getElementBySId(sref.getSpecies()).getName()
                            if i < (len(rc1_list) - 1):
                                rStr += ' + '
                        if reaction.getReversible():
                            rStr += ' <-> '
                        else:
                            rStr += ' --> '
                        for i in range(len(pt1_list)):
                            sref = pt1_list[i]
                            rStr += sub_model.getElementBySId(sref.getSpecies()).getName()
                            if i < (len(pt1_list) - 1):
                                rStr += ' + '

                        reaction_map[rStr] = reaction

                    for rStr in reaction_map:
                        if final_reaction_map.get(rStr):
                            final_reaction_map[rStr].append(reaction_map[rStr])
                        else:
                            final_reaction_map[rStr] = [reaction_map[rStr]]

                # Removing duplicate reactions and adding only one
                for rxn_str in final_reaction_map:
                    if len(final_reaction_map[rxn_str]) > 1:
                        for ind in range(0,len(final_reaction_map[rxn_str])):
                            i = final_reaction_map[rxn_str][ind]
                            if ind > 0:
                                status = model.removeReaction(i.getId())
                                if status != None:
                                    warnings.warn('Removing all duplicates of the reaction {0} in the combined model. Check the reaction rate to ensure model is consistent.'.format(rxn_str))

                # Removing duplicate species in the same compartment
                for unique_species_name in final_species_hash_map:
                    cumulative_amount = 0
                    if len(final_species_hash_map[unique_species_name]) > 1: 
                        flag = 0 
                        comp_dict = {}
                        for species in final_species_hash_map[unique_species_name]:
                            if comp_dict.get(species.getId()):
                                comp_dict[species.getId()].append(species.getCompartment())
                            else:
                                comp_dict[species.getId()] = [species.getCompartment()]
                        for spe_id in comp_dict:
                            if len(comp_dict[spe_id]) > 1:
                                # multiple compartments for a species
                                oldid = spe_id
                                allids = self.getAllIds()
                                trans = SetIdFromNames(allids)
                                newid = trans.getValidIdForName(spe_id)
                                self.renameSId(oldid, newid)
                                flag = 1

                        if flag:
                            continue
                           
                        uni_sp = final_species_hash_map[unique_species_name][0]
                        # For any species with same name 
                        # which were present in more than one subsystem
                        count = 0
                        for i in final_species_hash_map[unique_species_name]:
                            cumulative_amount += (model.getSpecies(i.getId()).getInitialAmount())
                            oldid = i.getId()
                            check(oldid, 'retreiving oldid combineSubsystems')
                            allids = self.getAllIds()
                            trans = SetIdFromNames(allids)
                            newid = trans.getValidIdForName(i.getName()) + '_combined'
                            self.renameSId(oldid, newid)
                            if count >= 1:
                                check(model.removeSpecies(newid),'removing species in combineSubsystems')
                            count += 1

                        species_amount = cumulative_amount
                        sp = simpleModel.getSpeciesByName(uni_sp.getName())
                        if type(sp) is list: 
                            for sp_i in sp:
                                check(sp_i.setInitialAmount(species_amount),'setting initial amount to cumulative in combineSubsystems')
                        else:
                            check(sp.setInitialAmount(species_amount),'setting initial amount to cumulative in combineSubsystems')
                    # else:
                    #     # If there are no species with multiple occurence in different subsystems
                    #     # then just add the list of all species maintained in the final hash map
                    #     # to our new subsystem's list of species.
                    #     ssys_size = i.getModel().getCompartment(0).getSize()
                    #     cumulative_amount = (i.getInitialAmount())*ssys_size
                    #     species_amount = cumulative_amount/total_size
                    #     check(i.setInitialAmount(species_amount),'setting initial amount to cumulative in combineSubsystems')
                    #     check(model.addSpecies(final_species_hash_map[unique_species_name][0]),'adding species in combineSubsystems')
        
            check(model.getCompartment(0).setSize(total_size), 'setting compartment size in model')
        elif mode == 'virtual':
            if combineNames == False:
                total_size = 0
                for subsystem in ListOfSubsystems:
                    mod = subsystem.getSBMLDocument().getModel()
                    check(mod,'retreiving subsystem model in combineSubsystems')
                    mod_id += '_' + mod.getId()
                    total_size += mod.getCompartment(0).getSize()

            # The final species hash map is a dictionary for all the species that will be
            # in the final subsystem.
            if combineNames == True:
                final_species_hash_map = {}
                final_reaction_map = {}
                total_size = 0
                for subsystem in ListOfSubsystems:
                    sub_model = subsystem.getSBMLDocument().getModel()
                    total_size += sub_model.getCompartment(0).getSize()
                    mod_id += '_' + sub_model.getId()
                    # Finding duplicate species by name and compartment
                    species_hash_map = {}
                    for species in sub_model.getListOfSpecies():
                        if species.getName() not in ListOfResources:
                        # Maintain the dictionary for all species in the input subsystems by their name
                            species_hash_map[species.getName()] = species
                    for species_name in species_hash_map:
                        if final_species_hash_map.get(species_name):
                            #If the final hash map already has that species then append to
                            # the same instead of duplicating
                            final_species_hash_map[species_name].append(
                                species_hash_map[species_name])
                        else:
                            # For all the species in the dictionary not already in the final
                            # hash map, save them to the final hash map dictionary.
                            final_species_hash_map[species_name] = [
                                species_hash_map[species_name]]

                    # Finding duplicate reactions by the reaction string
                    reaction_map = {}
                    for reaction in sub_model.getListOfReactions():
                        rc1_list = reaction.getListOfReactants()
                        pt1_list = reaction.getListOfProducts()
                        rStr = ''
                        for i in range(len(rc1_list)):
                            sref = rc1_list[i]
                            rStr += sub_model.getElementBySId(sref.getSpecies()).getName()
                            if i < (len(rc1_list) - 1):
                                rStr += ' + '
                        if reaction.getReversible():
                            rStr += ' <-> '
                        else:
                            rStr += ' --> '
                        for i in range(len(pt1_list)):
                            sref = pt1_list[i]
                            rStr += sub_model.getElementBySId(sref.getSpecies()).getName()
                            if i < (len(pt1_list) - 1):
                                rStr += ' + '

                        reaction_map[rStr] = reaction

                    for rStr in reaction_map:
                        if final_reaction_map.get(rStr):
                            final_reaction_map[rStr].append(reaction_map[rStr])
                        else:
                            final_reaction_map[rStr] = [reaction_map[rStr]]
                
                # Removing duplicate reactions and adding only one
                for rxn_str in final_reaction_map:
                    if len(final_reaction_map[rxn_str]) > 1:
                        for ind in range(0,len(final_reaction_map[rxn_str])):
                            i = final_reaction_map[rxn_str][ind]
                            if ind > 0:
                                status = model.removeReaction(i.getId())
                                if status != None:
                                    warnings.warn('Removing all duplicates of the reaction {0} in the combined model. Check the reaction rate to ensure model is consistent.'.format(rxn_str))

                # Removing duplicate species and adding only one
                for unique_species_name in final_species_hash_map:
                    if len(final_species_hash_map[unique_species_name]) > 1: 
                        flag = 0
                        comp_dict = {}
                        for species in final_species_hash_map[unique_species_name]:
                            if comp_dict.get(species.getId()):
                                comp_dict[species.getId()].append(species.getCompartment())
                            else:
                                comp_dict[species.getId()] = [species.getCompartment()]
                        for spe_id in comp_dict:
                            if len(comp_dict[spe_id]) > 1:
                                # multiple compartments for a species
                                oldid = spe_id
                                allids = self.getAllIds()
                                trans = SetIdFromNames(allids)
                                newid = trans.getValidIdForName(spe_id)
                                self.renameSId(oldid, newid)
                                flag = 1
                        # we don't want these species to be combined
                        if flag:
                            continue

                        # For any species with same name 
                        # which were present in more than one subsystem
                        count = 0
                        for i in final_species_hash_map[unique_species_name]:
                            model.addSpecies(i)
                            oldid = i.getId()
                            check(oldid, 'retreiving oldid combineSubsystems')
                            allids = self.getAllIds()
                            trans = SetIdFromNames(allids)
                            newid = trans.getValidIdForName(i.getName()) + '_combined'
                            self.renameSId(oldid, newid)
                            if count >= 1:
                                check(model.removeSpecies(newid),'removing species in combineSubsystems')
                            count += 1
                    # else:
                        # If there are no species with multiple occurence in different subsystems
                        # then just add the list of all species maintained in the final hash map
                        # to our new subsystem's list of species.
                        # model.addSpecies(final_species_hash_map[unique_species_name][0])
                        # check(model.addSpecies(final_species_hash_map[unique_species_name][0]),'adding species in combineSubsystems')
        
            check(model.getCompartment(0).setSize(total_size), 'setting compartment size in model')
        # Updating model id
        check(model.setId('combined_subsystems_' + mod_id),'setting new model id for shared model')
        return self.getSBMLDocument()

    def combineToConnectSubsystems(self, combineNames):
        model = self.getSBMLDocument().getModel()
        check(model,'retreiving model in combineToConnectSubsystems')
        simpleModel = SimpleModel(model)
        if combineNames == True:
            final_species_hash_map = {}
            # Finding duplicate species by name and compartment
            species_hash_map = {}
            for species in model.getListOfSpecies():
                # Maintain the dictionary for all species in the input subsystems by their name
                species_hash_map[species.getName()] = species
            for species_name in species_hash_map:
                if final_species_hash_map.get(species_name):
                    #If the final hash map already has that species then append to
                    # the same instead of duplicating
                    final_species_hash_map[species_name].append(
                        species_hash_map[species_name])
                else:
                    # For all the species in the dictionary not already in the final
                    # hash map, save them to the final hash map dictionary.
                    final_species_hash_map[species_name] = [
                        species_hash_map[species_name]]
            # Removing duplicate species and adding only one
            for unique_species_name in final_species_hash_map:
                if len(final_species_hash_map[unique_species_name]) > 1: 
                    print(unique_species_name)
                    flag = 0
                    comp_dict = {}
                    for species in final_species_hash_map[unique_species_name]:
                        if comp_dict.get(species.getId()):
                            comp_dict[species.getId()].append(species.getCompartment())
                        else:
                            comp_dict[species.getId()] = [species.getCompartment()]
                    for spe_id in comp_dict:
                        if len(comp_dict[spe_id]) > 1:
                            # multiple compartments for a species
                            oldid = spe_id
                            allids = self.getAllIds()
                            trans = SetIdFromNames(allids)
                            newid = trans.getValidIdForName(spe_id)
                            self.renameSId(oldid, newid)
                            flag = 1
                    # we don't want these species to be combined
                    if flag:
                        continue

                    # For any species with same name 
                    # which were present in more than one subsystem
                    count = 0
                    for i in final_species_hash_map[unique_species_name]:
                        model.addSpecies(i)
                        oldid = i.getId()
                        check(oldid, 'retreiving oldid combineSubsystems')
                        allids = self.getAllIds()
                        trans = SetIdFromNames(allids)
                        newid = trans.getValidIdForName(i.getName()) + '_combined'
                        self.renameSId(oldid, newid)
                        if count >= 1:
                            check(model.removeSpecies(newid),'removing species in combineSubsystems')
                        count += 1
                # else:
                    # If there are no species with multiple occurence in different subsystems
                    # then just add the list of all species maintained in the final hash map
                    # to our new subsystem's list of species.
                    # model.addSpecies(final_species_hash_map[unique_species_name][0])
                    # check(model.addSpecies(final_species_hash_map[unique_species_name][0]),'adding species in combineSubsystems')
    
        return self.getSBMLDocument()


  
    def connectSubsystems(self, ListOfSubsystems, connectionMap, mode = 'virtual', combineNames = False, amount_mode = 'additive', connected_species_amount = 0):
        '''
        The ListOfSubsystems are combined together as in combineSubsystems 
        method (depending on combineNames). Using the map given in connectionMap
        other species which are different, are also combined. The optional argument
        of amount_mode can be used to set if amounts of combined species will be a sum (additive mode) 
        or ('constant') mode will set the amount equal to that of the last optional argument, connected_species_amount, which the user provides. 
        Returns the connected SBMLDocument object of this Subsystem
        '''
        self.combineSubsystems(ListOfSubsystems, mode, combineNames)
        writeSBML(self.getSBMLDocument(),'models/test0.xml')
        model = self.getSBMLDocument().getModel()
        check(model,'retreiving self model in connectSubsystem')
        simpleModel = SimpleModel(model)
        for species_name in connectionMap.keys():
            species1 = simpleModel.getSpeciesByName(species_name)
            species2 = simpleModel.getSpeciesByName(connectionMap[species_name])
            if type(species1) is not list:
                species1 = [species1]
            if type(species2) is not list:
                species2 = [species2]
            for species in species2:
                check(species.setName(species_name),'updating name of species')
                oldid = species.getId()
                newid = oldid + '_connected'
                self.renameSId(oldid, newid)
            for species in species1:
                oldid = species.getId()
                print(species.getName())
                newid = oldid + '_connected'
                self.renameSId(oldid, newid)    
        # Combine the subsystems 
        writeSBML(self.getSBMLDocument(),'models/test01.xml')
        self.combineToConnectSubsystems(combineNames)
        writeSBML(self.getSBMLDocument(),'models/test11.xml')
        self.combineToConnectSubsystems(combineNames)
        # for species_name in connectionMap.keys():
        #     species1 = simpleModel.getSpeciesByName(species_name)
        #     species2 = simpleModel.getSpeciesByName(connectionMap[species_name])
        #     if type(species1) is not list:
        #         species1 = [species1]
        #     if type(species2) is not list:
        #         species2 = [species2]
        #     for species in species2:
        #         check(species.setName(species_name),'updating name of species')
        #         oldid = species.getId()
        #         newid = oldid + '_connected'
        #         self.renameSId(oldid, newid)
        #     for species in species1:
        #         oldid = species.getId()
        #         print(species.getName())
        #         newid = oldid + '_connected'
        #         self.renameSId(oldid, newid)  

        # # The connection map specifies two or more different species, that will be combined together
        # for species_name in connectionMap.keys():
        #     # Get the ids of the concerned species from the
        #     # connection map given 
        #     x = simpleModel.getSpeciesByName(species_name)
        #     y = simpleModel.getSpeciesByName(connectionMap[species_name])
        #     ListOfSpeciesGiven = []
        #     ListOfSpeciesGiven.append(x)
        #     ListOfSpeciesGiven.append(y)
        #     ListOfSpecies = []
        #     # Flatten the ListOfSpeciesGiven
        #     for species in ListOfSpeciesGiven:
        #         if type(species) is list:
        #             for sp in species:
        #                 ListOfSpecies.append(sp)
        #         else:
        #             ListOfSpecies.append(species)
            
        #     # Combine all species together in the ListOfSpecies
        #     comp_dict = {}
        #     for species in ListOfSpecies:
        #         # Check if they are in the same compartment before combining
        #         if comp_dict.get(species.getCompartment()):
        #             comp_dict[species.getCompartment()].append(species)
        #         else:
        #             comp_dict[species.getCompartment()] = [species]
            
        #     for comp in comp_dict.keys():
        #         s = 0
        #         uni_sp = comp_dict[comp][0]
        #         allids = self.getAllIds()
        #         trans = SetIdFromNames(allids)
        #         newid = trans.getValidIdForName(uni_sp.getName() + '_connected')
        #         count = 0 
        #         for species in comp_dict[comp]:
        #             # These species are in the same compartment, rename one, remove others
        #             if amount_mode == 'additive':
        #                 s += species.getInitialAmount()
        #             elif amount_mode == 'constant':
        #                 s = connected_species_amount
        #             oldid = species.getId()
        #             self.renameSId(oldid, newid)
        #             if count >= 1:
        #                 check(model.removeSpecies(newid), 'removing species to avoid duplication, in connectSubsystems')
        #             count += 1

        #         sp = model.getElementBySId(newid)
        #         check(sp.setInitialAmount(s),'setting initial amount connectSubsystems')
        check(model.setId('connected_subsystems_' + model.getId()),'setting new model id for shared model')
        return self.getSBMLDocument()

    def setSpeciesAmount(self, inputSpecies, amount):
        '''
        Sets amount of the species with the same name as inputSpecies argument equal to the amount argument
        Arguments may both be lists of same length.
        Returns the updated SBMLDocument object of this Subsystem.
        '''
        model_obj = SimpleModel(self.getSBMLDocument().getModel())
        if type(inputSpecies) is list:
            for inp_sp in inputSpecies:
                if type(inp_sp) is not str:
                    raise ValueError('All items of inputSpecies must be strings.')
                sp = model_obj.getSpeciesByName(inp_sp)
                if type(sp) is list:
                    for s_i in sp:
                        if type(amount) is not float and type(amount) is not int:
                            raise ValueError('The amount should be either a float or an int')
                        check(s_i.setInitialAmount(amount),'setting initial amount to 0 in connectSubsystem')
                else:
                    if type(amount) is not float and type(amount) is not int:
                        raise ValueError('The amount should be either a float or an int')
                    check(sp.setInitialAmount(amount),'setting initial amount')
        else:
            if type(inputSpecies) is not str:
                raise ValueError('inputSpecies argument must be a string or a list of strings.')
            sp = model_obj.getSpeciesByName(inputSpecies)
            if type(sp) is list:
                for s_i in sp:
                    if type(amount) is not float and type(amount) is not int:
                        raise ValueError('The amount should be either a float or an int')
                    check(s_i.setInitialAmount(amount),'setting initial amount')
            else:
                if type(amount) is not float and type(amount) is not int:
                    raise ValueError('The amount should be either a float or an int')
                check(sp.setInitialAmount(amount),'setting initial amount')


    def getFastReactions(self):
        '''
        Returns the reactions in the Subsystem with the attribute fast set as True
        '''
        allReactions = self.getSBMLDocument().getModel().getListOfReactions()
        fastReactions = []
        for reaction in allReactions:
            if reaction.isSetFast():
                if reaction.getFast() == True:
                    fastReactions.append(reaction)
        return fastReactions
    
    def setFastReactions(self, indexList):
        ''' 
        The indexList is used to set the corresponding reactions as fast
        by setting their fast attribute to True. For example, 
        indexList = [0 5], sets the 1st and 4th reaction in the Subsystem model as fast
        Returns the updated SBMLDocument of this Subsystem
        '''
        model = self.getSBMLDocument().getModel()
        if type(indexList) is int:
            model.getReaction(indexList).setFast(True)
            return
        for index in indexList:
            model.getReaction(index-1).setFast(True)
        return self.getSBMLDocument()
        

    def getReversibleReactions(self):
        '''
        Returns the reactions in the Subsystem with the reversible attribute 
        set as True
        '''
        allReactions = self.getSBMLDocument().getModel().getListOfReactions()
        reversibleReactions = []
        for reaction in allReactions:
            if reaction.isSetReversible():
                if reaction.getReversible():
                    reversibleReactions.append(reaction)
        return reversibleReactions

    def setReversibleReactions(self, indexList, rateFormulaList = None): 
        ''' 
        The indexList is used to set the corresponding reactions as reversible
        by setting the reversible attribute of the reaction as True. 
        The rateFormulaList is a list of strings with math formula 
        for the new rates of the corresponding reactions that are 
        being set as reversible. Returns the new Subsystem object with changes made
        Returns the updated SBMLDocument object of this Subsystem
        '''
        if not indexList:
            print('The list of index for reactions is empty.')
            return

        newSubsystem = self.getSystem().createNewSubsystem()
        model_orig = self.getSBMLDocument().getModel()
        newSubsystem.getSBMLDocument().setModel(model_orig)
        model = newSubsystem.getSBMLDocument().getModel()
        if type(indexList) is int:
            rxn = model.getReaction(indexList)
            rxn.setReversible(True)
            if rateFormulaList:
                rxn.unsetKineticLaw()
                rxn_obj = SimpleReaction(rxn)
                formulaString = rateFormulaList
                math_ast = rxn_obj.createMath(formulaString)
                kinetic_law = rxn_obj.createRate(math_ast)
                rxn.setKineticLaw(kinetic_law)
            return newSubsystem.getSBMLDocument()

        for i in range(len(indexList)):
            index = indexList[i]
            rxn = model.getReaction(index)
            rxn.setReversible(True)
            if rateFormulaList:
                rxn.unsetKineticLaw()
                rxn_obj = SimpleReaction(rxn)
                formulaString = rateFormulaList[i]
                math_ast = rxn_obj.createMath(formulaString)
                kinetic_law = rxn_obj.createRate(math_ast)
                rxn.setKineticLaw(kinetic_law)
        return newSubsystem.getSBMLDocument()


    def unsetReversibleReactions(self, indexList, rateFormulaList = None):
        ''' The indexList is used to unset the corresponding reactions' reversible
        attribute by setting it as False. 
        The rateFormulaList is a list of strings with math formula 
        for the new rates of the corresponding reactions that are 
        being set as reversible. Returns the new Subsystem object with changes made
        Returns the updated SBMLDocument of this Subsystem
        '''
        if not indexList:
            print('The list of index for reactions is empty.')
            return
        newSubsystem = self.getSystem().createNewSubsystem()
        model_orig = self.getSBMLDocument().getModel()
        newSubsystem.getSBMLDocument().setModel(model_orig)
        model = newSubsystem.getSBMLDocument().getModel()
        if type(indexList) is int:
            rxn = model.getReaction(indexList)
            rxn.setReversible(False)
            if rateFormulaList:
                rxn.unsetKineticLaw()
                rxn_obj = SimpleReaction(rxn)
                formulaString = rateFormulaList
                math_ast = rxn_obj.createMath(formulaString)
                kinetic_law = rxn_obj.createRate(math_ast)
                rxn.setKineticLaw(kinetic_law)
            return newSubsystem

        for i in range(len(indexList)):
            index = indexList[i]
            rxn = model.getReaction(index)
            rxn.setReversible(False)
            if rateFormulaList:
                rxn.unsetKineticLaw()
                rxn_obj = SimpleReaction(rxn)
                formulaString = rateFormulaList[i]
                math_ast = rxn_obj.createMath(formulaString)
                kinetic_law = rxn_obj.createRate(math_ast)
                rxn.setKineticLaw(kinetic_law)
        return newSubsystem


    def modelReduce(self, timepoints):
        ''' 
        Reduces the model by removing the reactions which are set as fast
        in the Subsystem model. The timepoints are used to simulate the
        fast reactions for these timepoints. The steady state values of 
        the involved species in the fast reactions are used in the
        reduced model as their initial value. 
        Returns the Subsystem object with the reduced model obtained.
        '''
        reducedSubsystem = self.getSystem().createNewSubsystem()
        model_orig = self.getSBMLDocument().getModel()
        reducedSubsystem.getSBMLDocument().setModel(model_orig)
        mod = reducedSubsystem.getSBMLDocument().getModel()

        fastRxns = self.getFastReactions()
        fastSubsystem = self.getSystem().createNewSubsystem()
        fastModel = fastSubsystem.createNewModel('fastModel', mod.getTimeUnits(), mod.getExtentUnits(), mod.getSubstanceUnits() )
        # adding all global (model level) components of the model
        # to the fastModel, except reactions and species
        if mod.getNumCompartmentTypes() != 0:
            for each_compartmentType in mod.getListOfCompartmentType():
                fastModel.addCompartment(each_compartmentType)
        if mod.getNumConstraints() != 0:
            for each_constraint in mod.getListOfConstraints():
                fastModel.addConstraint(each_constraint)
        if mod.getNumInitialAssignments() != 0:
            for each_initialAssignment in mod.getListOfInitialAssignments():
                fastModel.addInitialAssignment(each_initialAssignment)
        if mod.getNumFunctionDefinitions() != 0:
            for each_functionDefinition in mod.getListOfFunctionDefinitions():
                fastModel.addFunctionDefinition(each_functionDefinition)
        if mod.getNumRules() != 0:
            for each_rule in mod.getListOfRules():
                fastModel.addRule(each_rule)
        if mod.getNumEvents() != 0:
            for each_event in mod.getListOfEvents():
                fastModel.addEvent(each_event)
        if mod.getNumCompartments() != 0:
            for each_compartment in mod.getListOfCompartments():
                fastModel.addCompartment(each_compartment)
        if mod.getNumParameters() != 0:
            for each_parameter in mod.getListOfParameters():
                fastModel.addParameter(each_parameter)
        if mod.getNumUnitDefinitions() != 0:
            for each_unit in mod.getListOfUnitDefinitions():
                fastModel.addUnitDefinition(each_unit)
        fastModel.setAreaUnits(mod.getAreaUnits())
        fastModel.setExtentUnits(mod.getExtentUnits())
        fastModel.setLengthUnits(mod.getLengthUnits())
        fastModel.setSubstanceUnits(mod.getSubstanceUnits())
        fastModel.setTimeUnits(mod.getTimeUnits())
        fastModel.setVolumeUnits(mod.getVolumeUnits())

       # adding the reactions that are fast and the species used in them to 
        # the fast model
        for rxn in fastRxns:
            fastModel.addReaction(rxn)
            mod.removeReaction(rxn.getId())
            for reactant_ref in rxn.getListOfReactants():
                fastModel.addSpecies(mod.getElementBySId(reactant_ref.getSpecies()))
            for product_ref in rxn.getListOfProducts():
                fastModel.addSpecies(mod.getElementBySId(product_ref.getSpecies()))
        
        # get equilibrium values for species in fast reactions
        # writeSBML(fastSubsystem.getSBMLDocument(), 'models/intermediate_model.xml')
        print('###### Simulating the fast reactions in the model...All other species and parameters will be marked useless')
        time.sleep(2)
        data, m = fastSubsystem.simulateSbmlWithBioscrape(0,timepoints)
        allSpecies = fastModel.getListOfSpecies()
        for i in range(len(allSpecies)):
            species = mod.getElementBySId(allSpecies.get(i).getId())
            newAmount = data[:,m.get_species_index(species.getId())][-1]
            if newAmount > 0:
                species.setInitialAmount(newAmount)
            else:
                species.setInitialAmount(0)
        return reducedSubsystem

    def simulateBioscrape(self, initialTime, timepoints):
        ''' 
        To simulate a Subsystem without generating the plot. 
        Returns the data for all species and bioscrape model object which can be used to find out species indexes.
        '''
        filename = 'models/temp_simulate.xml'
        writeSBML(self.getSBMLDocument(), filename) 
        m = bioscrape.types.read_model_from_sbml(filename)
        s = bioscrape.simulator.ModelCSimInterface(m)
        s.py_prep_deterministic_simulation()
        s.py_set_initial_time(initialTime)
        sim = bioscrape.simulator.DeterministicSimulator()
        result = sim.py_simulate(s, timepoints)
        return result.py_get_result(), m

    def plotBioscrape(self, ListOfSpeciesToPlot, timepoints, xlabel = 'Time', ylabel = 'Concentration (AU)', sizeOfXLabels = 14, sizeOfYLabels = 14):
        ''' 
        To plot a Subsystem model using bioscrape.
        '''
        filename = 'models/temp_plot.xml'
        writeSBML(self.getSBMLDocument(), filename) 
        plotSbmlWithBioscrape(filename, timepoints[0], timepoints, ListOfSpeciesToPlot, xlabel, ylabel, sizeOfXLabels, sizeOfYLabels)
    
    def simulateVariableInputsBioscrape(self, ListOfInputs, ListOfListOfAmounts, ListOfSpeciesToPlot, timepoints, mode = 'continue', xlabel = 'Time', ylabel = 'Concentration (AU)', sizeOfXLabels = 14, sizeOfYLabels = 14):
        ''''
        Simulates the Subsystem model with the input species amounts varying 
        Uses bioscrape to simulate and plots the result
        Returns data, time vectors post simulation
        '''
        mpl.rc('axes', prop_cycle=(mpl.cycler('color', ['r', 'k', 'b','g','y','m','c']) ))
        model = self.getSBMLDocument().getModel()
        simpleModel = SimpleModel(model)
        species_list = []
        final_result = {}
        total_time = {}
        SpeciesToPlot = ListOfSpeciesToPlot[:]
        for species_name in ListOfSpeciesToPlot:
            species = simpleModel.getSpeciesByName(species_name)
            if type(species) is list:
                warnings.warn('There are multiple species with the name ' + species_name + 'Suffixed species will be plotted ')
                for species_i in species:
                    species_list.append(species_i.getId())
                    final_result[species_i.getId()] = []
                    total_time[species_i.getId()] = []
                key_ind = ListOfSpeciesToPlot.index(species_name)
                insert_new = []
                for j in range(len(species)-1):
                    insert_new.append(species_name + str(j+1))
                SpeciesToPlot[key_ind+1:key_ind+1] = insert_new 
            else:
                species_list.append(species.getId())
                final_result[species.getId()] = []
                total_time[species.getId()] = []
        initialTime = timepoints[0]
        t_end = timepoints[-1]
        points = len(timepoints)
        if (len(ListOfInputs) == 1) or (type(ListOfInputs) is str):
            t = initialTime
            if type(ListOfInputs) is list:
                input = ListOfInputs[0]
            elif type(ListOfInputs) is str:
                input = ListOfInputs
            else:
                raise ValueError('The input species argument should either be a list or a string')

            species_inp = simpleModel.getSpeciesByName(input)
            if type(species_inp) is list:
                raise ValueError('Multiple input species found in the model for the input name given.')
            for amount in ListOfListOfAmounts:
                if type(amount) is list:
                    raise ValueError('For single input, the amounts should not be a list of list type')
            for j in range(len(ListOfListOfAmounts)):
                # Start simulating and create data
                amount = ListOfListOfAmounts[j]
                check(species_inp.setInitialAmount(amount), 'setting initial amount to input species')
                time = np.linspace(t,t+t_end,points)
                data, m = self.simulateBioscrape(t, time)
                for species_id in species_list:
                    sp_data = data[:,m.get_species_index(species_id)]
                    t = time[-1]
                    final_result[species_id].extend(sp_data)
                    total_time[species_id].extend(time)
                if mode == 'continue':
                    for species in model.getListOfSpecies():
                        species.setInitialAmount(data[:,m.get_species_index(species.getId())][-1])

        else:
            t = initialTime
            ListOfSpecies = []
            for i in range(len(ListOfInputs)):
                input = ListOfInputs[i]
                species_inp = simpleModel.getSpeciesByName(input)
                if type(species_inp) is list:
                    raise ValueError('Multiple input species found in the model.')
                ListOfSpecies.append(species_inp)
            for i in range(len(ListOfListOfAmounts)):
                if (type(ListOfListOfAmounts[i]) is not list) or (len(ListOfListOfAmounts[i]) != len(ListOfInputs)) :
                    raise ValueError('For multiple inputs, all items of ListOfListOfAmounts attribute should be lists of length same as the number of inputs')
            for j in range(len(ListOfListOfAmounts)):
                for amount, species in zip(ListOfListOfAmounts[j], ListOfSpecies):
                # Start simulating and create data
                    check(species.setInitialAmount(amount), 'setting initial amount to input species')
                time = np.linspace(t,t+t_end,points)
                data, m = self.simulateBioscrape(t, time)
                for species_id in species_list:
                    sp_data = data[:,m.get_species_index(species_id)]
                    t = time[-1]
                    final_result[species_id].extend(sp_data)
                    total_time[species_id].extend(time)

                if mode == 'continue':
                    for species in model.getListOfSpecies():
                        species.setInitialAmount(data[:,m.get_species_index(species.getId())][-1])

        for species_id in species_list:
            plt.plot(total_time[species_id], final_result[species_id])

        plt.legend(SpeciesToPlot)
        mpl.rc('xtick', labelsize= sizeOfXLabels) 
        mpl.rc('ytick', labelsize=sizeOfYLabels)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()
        return final_result, total_time

