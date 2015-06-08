#!/usr/bin/python

import sys

def isBoobiesPicture(url): #{{{
    '''This method should verify if a given URL is a picture that contains boobies.'''
    return False
#}}}


if __name__ == '__main__':
    if len(sys.argv) > 1:
	fn = sys.argv[1]
	print "%s: %s" % (fn, isBoobiesPicture(fn))
