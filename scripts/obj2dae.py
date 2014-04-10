#!/usr/bin/env python2
"""
Convert Wavefront .obj (with optional .mtl) to Collada .dae meshes
"""

from __future__ import print_function
import sys, re, os, argparse
import collada, numpy 
import codecs

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--unit', help='Set units to [m]eter, [c]entimeter or [m]illimeter (default: m)')
parser.add_argument('-f', '--fuse', action="store_true", help='Fuse face groups with same material')
parser.add_argument('obj', help='Input Wavefront .obj mesh')
parser.add_argument('dae', help='Output COLLADA .dae mesh')
args = parser.parse_args()

unit = 'm'
if args.unit:
  unit = args.unit

inputFileName = args.obj
outputFileName = args.dae
mtlPath = os.path.dirname(os.path.abspath(inputFileName))

def BOMoffset(inputFile):
  if inputFile.readline().startswith(codecs.BOM_UTF8):
    return len(codecs.BOM_UTF8)
  else:
    return 0

inputFile = open(inputFileName, 'r');
inputFileStart = BOMoffset(inputFile)
inputFile.seek(inputFileStart)

vertices = []
normals = []
materials = {}
defaultMaterialName = 'obj2daeDefaultMaterial'
materials[defaultMaterialName] = { 'Kd': [0.6, 0.6, 0.6] }
for line in inputFile:
  line = line.strip()
  if len(line) == 0 or line.startswith('#'):
    continue
  splitters = line.split()
  if splitters[0] == 'v':
    vertex = [float(val) for val in splitters[1:]]
    vertices.append(vertex)
  elif splitters[0] == 'vn':
    normal = [float(val) for val in splitters[1:]]
    normals.append(normal)
  elif splitters[0] == 'mtllib':
    materialFileName = splitters[1]
    if not materialFileName.startswith(os.sep):
      materialFileName = mtlPath + os.sep + materialFileName
    materialFile = open(materialFileName, 'r')
    materialFile.seek(BOMoffset(materialFile))
    material = {}
    materialName = ''
    for materialLine in materialFile:
      materialLine = materialLine.strip()
      if len(materialLine) == 0 or materialLine.startswith('#'):
        continue
      materialSplitters = materialLine.split()
      if materialSplitters[0] == 'newmtl':
        if material:
          materials[materialName] = material
        materialName = materialSplitters[1]
        material = {}
      elif materialSplitters[0] == 'Kd':
        material[materialSplitters[0]] = [float(val) for val in materialSplitters[1:]]
    if material:
      materials[materialName] = material

inputFile.seek(inputFileStart)
groups = {}
groupIdx = 0
groupName = str(groupIdx)
materialName = defaultMaterialName
faces = []
for line in inputFile:
  line = line.strip()
  if len(line) == 0 or line.startswith('#'):
    continue
  splitters = line.split()
  if splitters[0] == 'g':
    if faces:
      groups[groupName] = { 'faces': faces, 'material': materialName }
    groupIdx += 1
    groupName = splitters[1]
    materialName = defaultMaterialName
    faces = []
  elif splitters[0] == 'usemtl':
    materialName = splitters[1]
  elif splitters[0] == 'f':
    face = []
    for faceElement in splitters[1:]:
      faceElementSplitters = faceElement.split('/')
      if len(faceElementSplitters) < 3:
        faceElementSplitters.extend([''] * (3 - len(faceElementSplitters)))
      indices = {}
      if faceElementSplitters[0]:
        indices['vertex'] = int(faceElementSplitters[0]) - 1
      if faceElementSplitters[1]:
        indices['texture'] = int(faceElementSplitters[1]) - 1
      if faceElementSplitters[2]:
        indices['normal'] = int(faceElementSplitters[2]) - 1
      face.append(indices)
    faces.append(face)
if faces:
  groups[groupName] = { 'faces': faces, 'material': materialName }

#print("vertices=", vertices)
#print("normals=", normals)
#print("materials=", materials)
#print("groups=", groups)

if args.fuse:
  fusedGroups = {}
  fusedCount = 0
  while groups:
    groupName = groups.keys()[0]
    group = groups.pop(groupName)
    fuseNames = []
    for searchGroupName in groups:
      searchgroup = groups[searchGroupName]
      if group['material'] == searchgroup['material']:
        fuseNames.append(searchGroupName)
    if not fuseNames:
      fusedGroups[groupName] = group
    else:
      fuseGroupName = 'fused%d' % fusedCount
      fusedCount += 1
      fusedGroups[fuseGroupName] = group
      for fuseName in fuseNames:
        fuseGroup = groups.pop(fuseName)
        fusedGroups[fuseGroupName]['faces'].extend(fuseGroup['faces'])
  #print("fusedGroups=", fusedGroups)
  groups = fusedGroups



mesh = collada.Collada()
if unit == 'm':
  mesh.assetInfo.unitname = 'meter'
  mesh.assetInfo.unitmeter = 1.000
elif unit == 'cm':
  mesh.assetInfo.unitname = 'centimeter'
  mesh.assetInfo.unitmeter = 0.010
elif unit == 'mm':
  mesh.assetInfo.unitname = 'millimeter'
  mesh.assetInfo.unitmeter = 0.001

colladaMaterials = {}
for materialName in materials:
  material = materials[materialName]
  colladaEffect = collada.material.Effect(materialName + "-effect", [], "phong")
  if 'Kd' in material:
    colladaEffect.diffuse = tuple(material['Kd'])
  colladaMaterial = collada.material.Material(materialName, materialName, colladaEffect)
  mesh.effects.append(colladaEffect)
  mesh.materials.append(colladaMaterial)
  colladaMaterials[materialName] = colladaMaterial

colladaVerticesSource = collada.source.FloatSource("vertices", numpy.array(vertices), ('X', 'Y', 'Z'))
colladaSources = [colladaVerticesSource]
if normals:
  colladaNormalSource = collada.source.FloatSource("normals", numpy.array(normals), ('X', 'Y', 'Z'))
  colladaSources.append(colladaNormalSource)
colladaGeometry = collada.geometry.Geometry(mesh, "geometry", "geometry", colladaSources)
mesh.geometries.append(colladaGeometry)

colladaInputList = collada.source.InputList()
colladaInputList.addInput(0, 'VERTEX', "#vertices")
if normals:
  colladaInputList.addInput(1, 'NORMAL', "#normals")

colladaMaterialNodes = []
for groupName in groups:
  group = groups[groupName]
  materialName = group['material']
  indices = []
  for face in group['faces']:
    for faceIndices in face:
      indices.append(faceIndices['vertex'])
      if normals:
        indices.append(faceIndices['normal'])
  colladaTriangleSet = colladaGeometry.createTriangleSet(numpy.array(indices), colladaInputList, materialName)
  colladaGeometry.primitives.append(colladaTriangleSet)
  if materialName in colladaMaterials:
    colladaMaterial = colladaMaterials[materialName]
  else:
    print('Warning: material %s unknown. Using default material %s instead' % (materialName, defaultMaterialName))
    colladaMaterial = colladaMaterials[defaultMaterialName]
  colladaMaterialNodes.append(collada.scene.MaterialNode(materialName, colladaMaterial, inputs=[]))

colladaGeometryNode = collada.scene.GeometryNode(colladaGeometry, colladaMaterialNodes)
node = collada.scene.Node('mynode', children=[colladaGeometryNode])
myscene = collada.scene.Scene("myscene", [node])
mesh.scenes.append(myscene)
mesh.scene = myscene

mesh.write(outputFileName)
