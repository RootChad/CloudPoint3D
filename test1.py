import pymeshlab
ms = pymeshlab.MeshSet()
ms.load_new_mesh('model.obj')
ms.load_new_mesh('model.obj')
print(ms.mesh_number())