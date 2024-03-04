from madcad import *
from pywavefront import Wavefront
# Créer deux cubes
cube1 = brick(width=vec3(10000))  # Cube avec une taille de 10 unités de côté
cube2 = brick(width=vec3(15000))   # Cube avec une taille de 8 unités de côté

mesh = read("model.obj")
mesh.transform(vec3(1, 1, 1))

print(mesh.volume())
print(cube1.volume())
# Déplacer le deuxième cube pour qu'ils ne se chevauchent pas
cube2 = cube2.transform(vec3(5, 5, 5))
w, h = 10000, 10000
rect = flatsurface(
    wire([vec3(-w, -h, 0), vec3(w, -h, 0), vec3(w, h, 0), vec3(-w, h, 0)])
)
rect.transform(vec3(100000, 100000, 100000))
# Faire la différence entre les deux cubes
difference_result = difference(cube1, rect)
io.write(difference_result,"test.stl")
# Afficher le résultat
show([cube1,rect,mesh])
