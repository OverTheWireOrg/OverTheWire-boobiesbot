#!/usr/bin/env python

from boobies.BoobiesDatabaseMongoDB import *

db = BoobiesDatabaseMongoDB()

ids = db.getAllIds()
c = 0
for i in ids:
    c += 1
    print "Updating %s (%d/%d)" % (i, c, len(ids))
    db.validateAndCacheURL(i, autodelete=True)
print "Done"

ids2 = db.getAllIds()
print "Went from %d to %d URLs" % (len(ids), len(ids2))
