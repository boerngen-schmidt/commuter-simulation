'''
Created on 06.11.2014

Original code form http://code.activestate.com/recipes/52224/

@author: Benjamin Börngen-Schmidt
'''
import sys, os

class Error(Exception): pass

def _find(path, matchFunc=os.path.isfile):
    for dirname in sys.path:
        candidate = os.path.join(dirname, path)
        if matchFunc(candidate):
            return candidate
    raise Error("Can't find file %s" % path)

def find(path):
    return _find(path)

def findDir(path):
    return _find(path, matchFunc=os.path.isdir)
