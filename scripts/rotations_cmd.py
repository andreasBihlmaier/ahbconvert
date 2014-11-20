#!/usr/bin/env python

import sys
import argparse
import numpy as np
from tf.transformations import *
import cmd
import numbers
from math import acos, sqrt



def homogeneous2quaternion(homogeneous):
  """
  Quaternion: [x, y, z, w]
  """
  quaternion = quaternion_from_matrix(homogeneous)
  return quaternion


def homogeneous2rpy(homogeneous):
  """
  RPY: [sx, sy, sz]
  """
  rpy = euler_from_matrix(homogeneous)
  return rpy

def homogeneous2axis_angle(homogeneous):
  """
  Axis-angle: [ax, ay, az]
  """
  qx, qy, qz, qw = homogeneous2quaternion(homogeneous)
  angle = 2.0 * acos(qw)
  norm = sqrt(1 - qw*qw)
  ax = (qx / norm) * angle
  ay = (qy / norm) * angle
  az = (qz / norm) * angle
  return (ax, ay, az)


def rpy2homogeneous(rpy):
  """
  RPY: [sx, sy, sz]
  """
  homogeneous = euler_matrix(rpy[0], rpy[1], rpy[2], 'rzyx')
  return homogeneous


def string2float_list(s):
  return [float(i) for i in s.split()]


def toFloat(val):
  if isinstance(val, numbers.Number) or isinstance(val, str):
    return float(val)
  else:
    return tuple(toFloat(fval) for fval in val)


def print_all_representations(homogeneous):
  print('homogeneous:\n%s\n' % homogeneous)
  print('rpy:\n%f %f %f\n' % homogeneous2rpy(homogeneous))
  print('quaternion (x, y, z, w):\n%f %f %f %f\n' % tuple(homogeneous2quaternion(homogeneous).tolist()))
  print('axis-angle:\n%f %f %f\n' % homogeneous2axis_angle(homogeneous))


class RotationsCmd(cmd.Cmd):
  def do_EOF(self, line):
    return True


  def do_rpy(self, line):
    """
    Roll-Pitch-Yaw (aka EulerZYX), accepted inputs:
    > r p y
    > [r, p, y]
    > r
    p
    y
    """
    if not line:
      args = []
      while not len(args) == 3:
        args_tmp = raw_input('rpy> ')
        args.extend(args_tmp.split())
    else:
      args = line.split()

    rpy = toFloat(args)
    print_all_representations(rpy2homogeneous(rpy))






def main(args):
  #parser = argparse.ArgumentParser()
  #parser.add_argument('representation', help='Representation of rotation in second argument')
  #args = parser.parse_args()
  RotationsCmd().cmdloop()

  



if __name__ == '__main__':
  main(sys.argv)
