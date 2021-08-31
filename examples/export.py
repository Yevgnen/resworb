# -*- coding: utf-8 -*-

from resworb.browsers.safari import Safari

safari = Safari()

print(safari.export(kinds=["cloud_tabs"]))
print(safari.export(kinds=["readings"]))
print(safari.export(kinds=["bookmarks"]))
print(safari.export(kinds=["histories"]))
print(safari.export(kinds="all"))
