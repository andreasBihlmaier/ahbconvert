#!/usr/bin/env python

import argparse
import xml.etree.ElementTree as ET

class Model:
  def __init__(self, package):
    self.package = package

  def __repr__(self):
    print('name=' + self.name)

  def load_sdf(self, sdf_file):
    tree = ET.parse(sdf_file)
    sdf = tree.getroot()
    model = sdf.findall('model')[0]
    self.name = model.attrib['name']


  def save_urdf(self, urdf_file):
    print('TODO')




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
