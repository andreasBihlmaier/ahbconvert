#!/usr/bin/env python

import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom

def prettyXML(uglyXML):
  return xml.dom.minidom.parseString(uglyXML).toprettyxml(indent='  ')

def pose2origin(pose):
  xyz = ' '.join(pose.split()[:3])
  rpy = ' '.join(pose.split()[3:])
  return xyz, rpy

class Link:
  def __init__(self, link_tag):
    self.name = link_tag.attrib['name']
    self.pose = None
    self.inertial = {}
    self.collision = {}
    self.visual = {}

    pose = link_tag.find('pose')
    if pose != None:
      self.pose = pose.text
    inertial = link_tag.find('inertial')
    if inertial != None:
      pose = inertial.find('pose')
      if pose != None:
        self.inertial['pose'] = pose.text
      mass = inertial.find('mass')
      if mass != None:
        self.inertial['mass'] = mass.text
      inertia = inertial.find('inertia')
      if inertia != None:
        inertia_vals = {}
        for coord in 'ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz':
          coord_val = inertia.find(coord)
          if coord_val != None:
            inertia_vals[coord] = coord_val.text
        self.inertial['inertia'] = inertia_vals
    for elem in 'collision', 'visual':
      elem_tag = link_tag.find(elem)
      if elem_tag != None:
        getattr(self, elem)['name'] = elem_tag.attrib['name']
        pose = elem_tag.find('pose')
        if pose != None:
          getattr(self, elem)['pose'] = pose.text
        geometry = elem_tag.find('geometry')
        if geometry != None:
          geometry_vals = {}
          sphere = geometry.find('sphere')
          if sphere != None:
            radius = sphere.find('radius')
            geometry_vals['sphere'] = {'radius': radius.text}
          mesh = geometry.find('mesh')
          if mesh != None:
            uri = mesh.find('uri')
            mesh_vals = {'uri': uri.text}
            scale = mesh.find('scale')
            if scale != None:
              mesh_vals['scale'] = scale.text
            geometry_vals['mesh'] = mesh_vals
          getattr(self, elem)['geometry'] = geometry_vals

  def toUrdfSubElement(self, parent_tag, package):
    link_tag = ET.SubElement(parent_tag, 'link', {'name': self.name})
    for elem in 'collision', 'visual':
      if getattr(self, elem):
        elem_tag = ET.SubElement(link_tag, elem, {'name': getattr(self, elem)['name']})
        if 'pose' in getattr(self, elem):
          xyz, rpy = pose2origin(getattr(self, elem)['pose'])
          origin_tag = ET.SubElement(elem_tag, 'origin', {'rpy': rpy, 'xyz': xyz})
        if 'geometry' in getattr(self, elem):
          geometry_tag = ET.SubElement(elem_tag, 'geometry')
          if 'mesh' in getattr(self, elem)['geometry']:
            mesh_tag = ET.SubElement(geometry_tag, 'mesh', {'filename':  'package://' + package + '/' + '/'.join(getattr(self, elem)['geometry']['mesh']['uri'].split('/')[3:])})
          if 'sphere' in getattr(self, elem)['geometry']:
            sphere_tag = ET.SubElement(geometry_tag, 'sphere', {'radius': getattr(self, elem)['geometry']['sphere']['radius']})
    if self.inertial:
      inertial_tag = ET.SubElement(link_tag, 'inertial')
      mass_tag = ET.SubElement(inertial_tag, 'mass', {'value': self.inertial['mass']})
      if 'pose' in self.inertial:
        xyz, rpy = pose2origin(self.inertial['pose'])
        origin_tag = ET.SubElement(inertial_tag, 'origin', {'rpy': rpy, 'xyz': xyz})
      if 'inertia' in self.inertial:
        inertia_tag = ET.SubElement(inertial_tag, 'inertia')
        for coord in 'ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz':
          inertia_tag.attrib[coord] = self.inertial['inertia'].get(coord, '0')

  def __repr__(self):
    return 'Link(name=%s, pose=%s, inertial=%s, collision=%s, visual=%s)' % (self.name, self.pose, str(self.inertial), str(self.collision), str(self.visual))



class Joint:
  def __init__(self, joint_tag):
    self.name = joint_tag.attrib['name']
    self.joint_type = joint_tag.attrib['type']
    self.child = joint_tag.find('child').text
    self.parent = joint_tag.find('parent').text
    self.pose = None
    self.axis = {}

    pose_tag = joint_tag.find('pose')
    if pose_tag != None:
      self.pose = pose_tag.text
    axis_tag = joint_tag.find('axis')
    xyz_tag = axis_tag.find('xyz')
    if xyz_tag != None:
      self.axis['xyz'] = xyz_tag.text
    limit_tag = axis_tag.find('limit')
    if limit_tag != None:
      limit_vals = {}
      for elem in 'lower', 'upper', 'effort', 'velocity':
        elem_tag = limit_tag.find(elem)
        if elem_tag != None:
          limit_vals[elem] = elem_tag.text
      self.axis['limit'] = limit_vals

  def toUrdfSubElement(self, parent_tag):
    print('TODO')

  def __repr__(self):
    return 'Joint(name=%s, type=%s, child=%s, parent=%s, axis=%s, pose=%s)' % (self.name, self.joint_type, self.child, self.parent, str(self.axis), self.pose)




class Model:
  def __init__(self, package):
    self.package = package
    self.links = []
    self.joints = []

  def __repr__(self):
    return 'Model(name=%s,\n links=%s,\n joints=%s\n)' % (self.name, str(self.links), str(self.joints))

  def load_sdf(self, sdf_filename):
    tree = ET.parse(sdf_filename)
    sdf = tree.getroot()
    model = sdf.findall('model')[0]
    self.name = model.attrib['name']
    self.add_elements(sdf_filename)

  def add_elements(self, sdf_filename):
    tree = ET.parse(sdf_filename)
    sdf = tree.getroot()
    model = sdf.findall('model')[0]
    for link in model.iter('link'):
      self.links.append(Link(link))
    for joint in model.iter('joint'):
      self.joints.append(Joint(joint))


  def save_urdf(self, urdf_filename):
    urdf = ET.Element('robot', {'name': self.name})
    for link in self.links:
      link.toUrdfSubElement(urdf, self.package)
    for joint in self.joints:
      joint.toUrdfSubElement(urdf)

    urdf_file = open(urdf_filename, 'w')
    pretty_urdf_string = prettyXML(ET.tostring(urdf))
    urdf_file.write(pretty_urdf_string)




def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('sdf', help='SDF file to convert')
  parser.add_argument('urdf_package', help='Name of package where model ressources (e.g. meshes) are located')
  parser.add_argument('urdf', help='Resulting URDF file to be written')
  args = parser.parse_args()

  model = Model(args.urdf_package)
  model.load_sdf(args.sdf)
  print('Parsed SDF model:\n' + str(model))
  model.save_urdf(args.urdf)


if __name__ == '__main__':
  main()
