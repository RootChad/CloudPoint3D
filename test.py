import os
import trimesh

def perform_boolean_intersection(mesh_path_1, mesh_path_2, output_path):
    mesh1 = trimesh.load(mesh_path_1)
    mesh2 = trimesh.load(mesh_path_2)    
    try:
        result = trimesh.boolean.union([mesh1, mesh2], engine='blender')
        if isinstance(result, trimesh.Scene):
            if result.is_empty:
                print("Intersection vide. Passer à la prochaine boîte.")           
        
        if not result.is_empty:
            fragment_path = os.path.join(output_path, f'mesh_fragment.obj')
            result.export(fragment_path)
    except Exception as e:
        print(f"Error intersecting mesh and box: {e}")

# Exemple d'utilisation
mesh_path_1 = 'data/model.obj'  # Chemin vers le premier maillage exporté
mesh_path_2 = 'data/test.obj'  # Chemin vers le deuxième maillage exporté
output_path = 'data/'  # Chemin et nom de fichier pour le résultat

perform_boolean_intersection(mesh_path_1, mesh_path_2, output_path)