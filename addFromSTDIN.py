#!/usr/bin/python

import sys
from boobies.BoobiesDatabaseMongoDB import *

if __name__ == '__main__':
    x = BoobiesDatabaseMongoDB()
    for l in [s.strip() for s in sys.stdin.readlines()]:
	x.addBoobies(l)
