#!/usr/bin/python

# SQLite
import sqlite3
import os
import sys

class Adder(object):
    def db_init(self, fn): #{{{
	if os.path.exists(fn):
	    self.db = sqlite3.connect(fn)
	else:
	    self.db = sqlite3.connect(fn)
	    cu = self.db.cursor()
	    cu.execute("create table boobies (url varchar)")
	    self.db.commit()
    #}}}
    def db_addBoobies(self, url): #{{{
	cu = self.db.cursor()
	cu.execute("insert into boobies values(?)", (url,))
	self.db.commit()
	return cu.lastrowid
    #}}}


if __name__ == '__main__':
    x = Adder()
    x.db_init("boobies.db")
    for l in [s.strip() for s in sys.stdin.readlines()]:
	x.db_addBoobies(l)
