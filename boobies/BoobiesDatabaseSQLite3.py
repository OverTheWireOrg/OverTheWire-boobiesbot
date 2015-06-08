#!/usr/bin/python

import sqlite3, os
from BoobiesDatabase import BoobiesDatabase

class BoobiesDatabaseSQLite3(BoobiesDatabase):
    def __init__(self, fn = "boobies.db"): #{{{
	if os.path.exists(fn):
	    self.db = sqlite3.connect(fn)
	else:
	    self.db = sqlite3.connect(fn)
	    cu = self.db.cursor()
	    cu.execute("create table boobies (url varchar)")
	    self.db.commit()
    #}}}
    def addBoobies(self, url): #{{{
	cu = self.db.cursor()
	cu.execute("insert into boobies values(?)", (url,))
	self.db.commit()
        return cu.lastrowid
    #}}}
    def alreadyStored(self, url): #{{{
	cu = self.db.cursor()
	cu.execute("select rowid from boobies where url = ?", (url,))
	row = cu.fetchone()
	if row:
	    return True
	else:
	    return False
    #}}}
    def getSpecificBoobies(self,id): #{{{
       cu = self.db.cursor()
       cu.execute("select url, rowid from boobies where rowid=%d" %id)
       row = cu.fetchone()
       if row:
           return (str(row[0]), int(row[1]))
       else:
           return ("", 0)
   #}}}
    def getRandomBoobies(self): #{{{
	cu = self.db.cursor()
	cu.execute("select url, rowid from boobies order by random() limit 1")
	row = cu.fetchone()
	if row:
	    return (str(row[0]), int(row[1]))
	else:
	    return ("", 0)
    #}}}
    def delBoobies(self, bid): #{{{
        cu = self.db.cursor()
        cu.execute("delete from boobies where rowid=%d" % bid)
        self.db.commit()
    #}}}    


if __name__ == '__main__':
    db = BoobiesDatabaseSQLite3()

    print db.addBoobies("http://test.com")
    print db.alreadyStored("http://test.com")
    print db.getSpecificBoobies(1)
    print db.getRandomBoobies()
    print db.delBoobies(1)


