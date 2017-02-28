# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 08:59:27 2016
Parts from DDI4ModelViewer.py


@author: lhoyle
"""

import os
import sys
import re
import xml.etree.ElementTree as ET


# get the most recent xmi.xml file of the PlatformIndependent DDI4 model
#     from the DDI development website
#  ------------for testing read from a file --------------
import requests
res = requests.get('http://lion.ddialliance.org/xmi.xml')
res.status_code == requests.codes.ok
print('Processing the following version of the DDI4 xmi.xml Platform Independent Model:')
print(res.text[:167])

# parse the root element of the XML file into an XML tree
rootDDI4XMI = ET.fromstring(res.text)
# ---------------------------------------------------------

# get the default folder from the command line 
#otherwise default to this
DataFolder = "C:\\Ddrive\\projects\\various\\Python\\DDI4\\2017_02_24\\"
if len(sys.argv)> 1:
    if os.path.isdir(sys.argv[1]):
        DataFolder = sys.argv[1]

if not os.path.isdir(DataFolder):
    print('WARNING: output directory does not exist\n')
    sys.exit()    
else: 
    print('\nNOTE: Data files will be output to:\n    ' + DataFolder + '\n' )
# ----------for testing read a local static copy of the xmi 
#with open(DataFolder + "xmi.xml", 'r', encoding="utf-8") as f:
#    XMItext = f.read()
#rootDDI4XMI = ET.fromstring(XMItext)
# ---------------------------------------------------------


print(rootDDI4XMI.tag)


DebugFile = open(DataFolder + "Debug.txt", 'w', encoding="utf-8")



# for each view get a list of its classes
#  make a dictionary of those lists keyed on the view name

diagrams = {}

for diagram in rootDDI4XMI.iter('diagram'): 
    view = diagram.find('model').attrib.get('package')
    if view != 'ComplexDataTypes':
        #print(view)
        classList = []
        for element in diagram.find('elements'):
            classList.append(element.attrib.get('subject'))
        #print('   '+str(classList))
        diagrams[view] = classList
#print(str(diagrams))

def viewList(className, diagrams ):
# given a class name return a list of the Views in which it appears     
    viewList = []
    for viewName, viewClassList in diagrams.items():        
        if className in viewClassList:
            viewList.append(viewName)
    if len(viewList)>0:
        return viewList
    else:
        return        
def cardinalityString(lowerValue, upperValue):
# Given the lower and upper values from an xmi file, return a string e.g."0..n"
    if lowerValue == None:
        lowerValue = "0"
    elif lowerValue == "-1":
        lowerValue = "n"
    if upperValue == None:
        upperValue = "0"
    elif upperValue == "-1":
        upperValue = "n" 
    return lowerValue + ".." + upperValue  

def classInYAML(topLevel, className, leadingBlanks, classProperties, classParentName, classRelations):

    # first list properties

    YamlText =  ''
    if classProperties.get(className) != None:
      
      for keyProperty in sorted(classProperties[className]):
          lowerValue = classProperties[className][keyProperty]['minimumCardinality'] 
          upperValue = classProperties[className][keyProperty]['maximumCardinality']  
          if lowerValue == None:
            lowerValue = "0"
          elif lowerValue == "-1":
            lowerValue = "n"
          if upperValue == None:
            upperValue = "0"
          elif upperValue == "-1":
            upperValue = "n" 
 
          dataType = classProperties[className][keyProperty]['dataType']
          dataTypeText = dataType
          if dataType == None:
              dataTypeText = "unspecified"
            
          if  classProperties[className][keyProperty]['refersTo'] == 'DdiClass'   :
              dataTypeText = "DDI class " + dataType
        
          leadingString = " "
                                    # indent each property one additional space
          YamlText = YamlText + \
                      leadingString + \
                      leadingBlanks + \
                      keyProperty + \
                      ": " + \
                      "         # " + \
                      "(" + lowerValue + \
                      "..." + upperValue + ") " + \
                      dataTypeText + \
                      '  (' + className + ')' 
                      
        # if minimum cardinality not 0 then indicate "required"        
          if lowerValue != '0':
              YamlText = YamlText + " required"
            
        # if maximum cardinality > 1 then insert a list indicator 
        # and up the indentation by 2      
          ListIndent = ""            
          if upperValue != '1':
              YamlText = YamlText + ' (list) \n' + leadingBlanks +  '  -'
              ListIndent = "   "
          else:
              ListIndent = " "
            
          YamlText = YamlText + "\n"         
                   
          if classProperties[className][keyProperty]['refersTo'] == 'DdiClass'   :
              if dataType in classProperties:                
                YamlText = YamlText + classInYAML(False, dataType,  ListIndent +  leadingBlanks, classProperties, classParentName, classRelations)
              else: 
                DebugFile.write('|'+ dataType + '|' + " not in classProperties \n")  
    
    # Now list relations ----------   
               
    if classRelations.get(className) != None:
        YamlText = YamlText + \
               '\n#  Relationships - ' + \
               className + ' to: *_______\n' + \
               '#     enter  *URN for the target of each relationship below\n'
                        
        for keyRelationName in sorted(classRelations[className]):
             if not classRelations[className][keyRelationName]['targetCardinality'].startswith('0.'):
                 requiredText = ' required'
             else:
                 requiredText = ''
             if  keyRelationName == 'realizes':           # realizes is not to be instantiated
                 YamlText = YamlText + \
                            " " + \
                            leadingBlanks + \
                            '#           realizes ' + \
                            classRelations[className][keyRelationName]['relationTarget'] + \
                            '\n'
             else:    
                 YamlText = YamlText + \
                            " " + \
                            leadingBlanks + \
                            keyRelationName + \
                            ':' + \
                            '                       #' + \
                            classRelations[className][keyRelationName]['targetCardinality'] + \
                            '  *' + classRelations[className][keyRelationName]['relationTarget'] + \
                            requiredText 
                        
                 # if maximum cardinality > 1 then insert a list indicator 
                 # and up the indentation by 2      
                 targetUpperRegEx = re.compile(r'\.\.(\d+|n)', re.VERBOSE)
                 targetUpperMatch = targetUpperRegEx.search(classRelations[className][keyRelationName]['targetCardinality'])
             
                 if targetUpperMatch != None:
                     if targetUpperMatch.group(1) != '1':
                         YamlText = YamlText  + ' (list) \n' + leadingBlanks +  '  -'
        
                 YamlText = YamlText +'\n'
    # now find inherited properties and relations       
    if className in classParentName:
        YamlText = YamlText + '\n# ----- ' + \
        className + ' inherits the following from ' + classParentName[className] + '----- \n#    Properties' '\n'
        YamlText = YamlText + classInYAML(False, classParentName[className], leadingBlanks, classProperties, classParentName, classRelations)
              
    return YamlText


# create an overall model graph
#overallGraph = nx.DiGraph()

# this dictionary will contain a dictionary of properties 
# for each class with properties
#     in that dictinonary there will be details for the property 
#     e.g. minimumCardinality
# example: 
# classProperties['InstanceVariable']['variableRole']['datatype'] 
#   is a 'StructuredString'
classProperties = {}

# this dictionary will contain a dictionary for each class with relations
#    with the relation name as the key
#    and a list [sourceCardinality, targetCardinality] as the value
    
classRelations = {}

# this dictionary will contain true (is abstract) or false (is not abstract)
#  for all classes 
classIsAbstract = {}

#this dictionary will contain the parent class name for any class that 
# extends its parent
classParentName = {}

# this dictionary will contain the target cardinality keyed on the relation 
# (association) name
associationTargetCardinality = {}



# populate the classIsAbstract dictionary , create a node in the graph
for packagedElement in rootDDI4XMI.iter('packagedElement'):
    # only want xmi:type="uml:Class"
    if packagedElement.attrib.get('{http://www.omg.org/spec/XMI/20110701}type') == "uml:Class":
        name = packagedElement.attrib.get('name')
        if packagedElement.attrib.get('isAbstract') == 'true':
            classIsAbstract[name] = True
        else:
            classIsAbstract[name] = False
#        overallGraph.add_node(name,{'isAbstract':classIsAbstract[name]} )     
    
# populate classParentName with the classes that extend another
for generalization in rootDDI4XMI.iter('generalization'):
    xmiId = generalization.attrib.get('{http://www.omg.org/spec/XMI/20110701}id')
    xmiIdRegex = re.compile(r'''(
           ^([^_]+)_   # child class
           ([^_]+)_    # "extends"
           ([^_]*)$    # parent class
           )''', re.VERBOSE)
    xmiIdSearch = xmiIdRegex.search(xmiId)
    child=xmiIdSearch.group(2)
    parent=xmiIdSearch.group(4)
    classParentName[child] = parent
#    overallGraph.add_node(child,{'isAbstract':classIsAbstract[name], 'extends':parent} )
    
    
#populate tne associationTargetCardinality dictionary
for ownedEnd in rootDDI4XMI.iter('ownedEnd'):
    association = ownedEnd.attrib.get('association')
    
    if ownedEnd.find('lowerValue') == None or ownedEnd.find('upperValue') == None:
        targetCardinality = "Missing"
        print("NOTE: missing target cardinality for " + association)
    else:    
        targetCardinality = cardinalityString(ownedEnd.find('lowerValue').attrib.get('value'),ownedEnd.find('upperValue').attrib.get('value'))
    
        
    associationTargetCardinality[association] = targetCardinality
    
# find the Source, Target and relationship name for each relationship in the DDI4 model

for ownedAttribute in rootDDI4XMI.iter('ownedAttribute'):
    association = ownedAttribute.attrib.get('association')
    # NOTE: assumption - Relations all have an association attribute
    if association !=  None:
        associationRegex = re.compile(r'''(
           ^([^_]+)_   # source class
           ([^_]+)_    # association name
           ([^_]*)$    # "association"
           )''', re.VERBOSE)
        oASearch = associationRegex.search(association)
        relationName = oASearch.group(3)
        relationSource = ownedAttribute.attrib.get('name')
        
        relationTarget = ownedAttribute.find('type').attrib.get('{http://www.omg.org/spec/XMI/20110701}idref')
        
        #  extract and edit cardinalities into one string
        
        if ownedAttribute.find('lowerValue') == None:
            lowerCardinalityValue = "Missing"
            print("NOTE: for" + relationSource + "relation " + relationName + "cardinality is missing")                 
        else:
            lowerCardinalityValue = ownedAttribute.find('lowerValue').attrib.get('value')
        
        if ownedAttribute.find('upperValue') == None:
            upperCardinalityValue = "Missing"
            print("NOTE: for" + relationSource + "relation " + relationName + "cardinality is missing")                 
        else:
            upperCardinalityValue = ownedAttribute.find('upperValue').attrib.get('value')   
            
        sourceCardinality = cardinalityString(lowerCardinalityValue, upperCardinalityValue)
        targetCardinality = associationTargetCardinality[association]
        relationCardinality = sourceCardinality + "->" + targetCardinality

        # print(relationSource, relationName, relationTarget)
        
        # put relationNames in a list for each class
        if relationSource in classRelations.keys():
            # add a relation to this class's list
            classRelations[relationSource][relationName] =  {'relationTarget': relationTarget, 'sourceCardinality': sourceCardinality,'targetCardinality': targetCardinality}
        else:
            classRelations[relationSource] = {relationName: {'relationTarget': relationTarget, 'sourceCardinality': sourceCardinality,'targetCardinality': targetCardinality}}
            
        # add nodes and edge to the graph
#        overallGraph.add_node(relationSource,{'properties':classProperties.get(relationSource), 'relations':classRelations.get(relationSource), 'inViews':viewList(relationSource,diagrams),'isAbstract':classIsAbstract[relationSource], 'extends':classParentName.get(relationSource)} )    
        
        #print(relationSource, relationName, relationCardinality)
#        overallGraph.add_edge(relationSource, relationTarget, name=relationName, cardinality=relationCardinality)
    else:
        # capture properties and their details for each class in a dictionary
        #   NOTE: not currently capturing <ownedComment    
    
        xmiId = ownedAttribute.attrib.get('{http://www.omg.org/spec/XMI/20110701}id')
        idRegex = re.compile(r'''(
             ^([^_]+)_   # class name
             ([^_]*)$    # property
        )''', re.VERBOSE)
        idSearch = idRegex.search(xmiId)
        className = idSearch.group(2)
        propertyName = idSearch.group(3)
        
        DebugFile.write('xmiId: ' + xmiId + '  className: ' + className + '  propertyName: ' + propertyName+ '\n')
        #  extract and edit cardinalities into one string
        minimumCardinality = ownedAttribute.find('lowerValue').attrib.get('value')
        maximumCardinality = ownedAttribute.find('upperValue').attrib.get('value')
        propertyCardinality = cardinalityString(minimumCardinality,maximumCardinality)     
                
        # the datatype will be in the <type> element
        #   if a DDI4 class in the attribute xmi:idref 
        #   if a uml primitive in the attribute xmi:type with a value of "uml:PrimitiveType" or  "xsd:anyURI"
        #        and POSSIBLY an href attribute
        
        typeXmiType = ownedAttribute.find('type').attrib.get('{http://www.omg.org/spec/XMI/20110701}type')
        typeXmiIdref = ownedAttribute.find('type').attrib.get('{http://www.omg.org/spec/XMI/20110701}idref')
        typeHref = ownedAttribute.find('type').attrib.get('href')
        
        if typeXmiIdref != None:    # this is a reference to a DDI class
            refersTo = 'DdiClass'
            dataType = typeXmiIdref
        elif typeXmiType != None:
            refersTo = typeXmiType
            dataType = typeHref
        else:
            refersTo = 'unknownReference'
            dataType = 'unspecified'
            print ('unknown property type: ' + className)
        
        
        # enter or add to the dictionary of properties        
        
        if className in classProperties.keys():
            # add a property to this class's list
            classProperties[className][propertyName] = {'minimumCardinality': minimumCardinality, 'maximumCardinality': maximumCardinality, 'refersTo': refersTo, 'dataType': dataType}
            #DebugFile.write('    |' + className +  '| added property: ' + propertyName + '\n')
        else:
            classProperties[className] = {propertyName: {'minimumCardinality': minimumCardinality, 'maximumCardinality': maximumCardinality, 'refersTo': refersTo, 'dataType': dataType}}
            #DebugFile.write('    |' + className +  '| created with property: ' + propertyName  + '\n')
#        overallGraph.add_node(className,{'properties':classProperties.get(className), 'relations':classRelations.get(className), 'inViews':viewList(className,diagrams),'isAbstract':classIsAbstract[className], 'extends':classParentName.get(className)} )    

     


YamlFile = open(DataFolder + "Test.yml", 'w', encoding="utf-8")

className="Annotation"
leadingBlanks=""

YamlFile.write(leadingBlanks + className + ": " + "\n")
YamlFile.write('#  Native Properties and Relationships \n')
YamlFile.write(classInYAML(False, className,leadingBlanks, classProperties, classParentName, classRelations))

YamlFile.close()




# write a template file for each view
for viewName, classList in diagrams.items():
  ViewFile = open(DataFolder + viewName + ".yml", 'w', encoding="utf-8")
  ViewFile.write(  "DDI:     #View " + viewName)

  for className in classList:
      leadingBlanks=" "   
      ViewFile.write("\n\n\n# --------------------\n")
      ViewFile.write(" -" + leadingBlanks + className + ": " + "\n")
      leadingBlanks="   "
      ViewFile.write(classInYAML(True, className,leadingBlanks, classProperties, classParentName, classRelations))
      
  ViewFile.close() 
  
DebugFile.close()

# which classes extend AnnotatedIdentifiable
#AnnotatedFile = open(DataFolder +  "AnnotatedClasses", 'w', encoding="utf-8")
#for childClass, parentClass in classParentName.items():
#    if parentClass=='AnnotatedIdentifiable':
#        AnnotatedFile.write(childClass + " \n")
#AnnotatedFile.close()
 
 #posSpring =  nx.spring_layout(overallGraph) 
#posShell = nx.shell_layout(overallGraph) 

# Reports and Graphs for each View
#for viewName, classList in diagrams.items():
#    print("\n\nView " + viewName)
#    viewPropertyList = []
#    for className in classList:
#        classPropertyList = classProperties.get(className)
#        if classPropertyList != None:
#            for propertyName in classPropertyList:
#                viewPropertyList.append(propertyName + "(" + className + ")"  )
#    viewPropertyList.sort()
#    print("\nProperty List")
#    for propertyName in viewPropertyList:
#        print(propertyName)
    
    # draw a static diagram of each view both as spring-form and circular
#    viewGraph = overallGraph.subgraph(classList).copy()
    #print("View: "+viewName)
#    print("\nNodes: " + str(viewGraph.nodes()))
#    print("\nEdges: " + str(viewGraph.edges()))
#    graphLabel = viewName + "_Springform_Layout"
#    nx.draw_spring(viewGraph, with_labels=True, node_size=600, node_color='#eeffff', font_size=9) 
#    plt.suptitle(graphLabel)
#    plt.savefig(viewName + "_spring.png")
#    plt.show()
#    graphLabel = viewName + "_Circular_Layout"
#    nx.draw_circular(viewGraph, with_labels=True, node_size=600, node_color='#eeffff', font_size=9) 
#    plt.suptitle(graphLabel)
#    plt.savefig(viewName + "_circular.png")
#    plt.show()

