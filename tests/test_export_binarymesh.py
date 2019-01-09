import time
box = hou.node("/obj/box/OUT")
clockstart = time.time()
box.geometry().saveToFile("hdk.binarymesh")
print('Generation time: %g seconds' % (time.time() - clockstart))