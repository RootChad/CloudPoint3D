import os
import trimesh
import numpy as np
import click

def create_grid_division(mesh, divisions):
    # Obtenir les limites du maillage pour déterminer l'espace à diviser
    bounds = mesh.bounds
    
    # Calculer les points de division pour chaque axe en fonction du nombre de divisions souhaitées
    division_points = [np.linspace(start, end, num=div+1) for start, end, div in zip(bounds[0], bounds[1], divisions)]
    
    fragments = []  # Initialiser la liste pour stocker les fragments résultants
    
    # Itérer sur chaque division de la grille pour créer des boîtes de division
    for i in range(divisions[0]):
        for j in range(divisions[1]):
            for k in range(divisions[2]):
                # Déterminer les coins minimaux et maximaux de la boîte actuelle
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]
                
                # Calculer le centre et les dimensions de la boîte
                center = [(min_corner[0] + max_corner[0]) / 2, (min_corner[1] + max_corner[1]) / 2, (min_corner[2] + max_corner[2]) / 2]
                extents = [max_corner[0] - min_corner[0], max_corner[1] - min_corner[1], max_corner[2] - min_corner[2]]                
                
                # Créer la boîte de division
                box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))                
                
                try:
                    # Tenter d'effectuer une intersection entre le maillage et la boîte
                    result = trimesh.boolean.intersection([mesh, box], engine='blender')                    
                    
                    # Traiter le résultat de l'intersection
                    if isinstance(result, trimesh.Scene):
                        # Si le résultat est une scène, combiner tous les maillages en un seul si possible
                        combined_mesh = result.dump(concatenate=True)
                        if not combined_mesh.is_empty:
                            fragments.append(combined_mesh)
                    elif isinstance(result, trimesh.Trimesh) and not result.is_empty:
                        # Si le résultat est un maillage individuel, l'ajouter directement à la liste des fragments
                        fragments.append(result)
                except Exception as e:
                    # Gérer les erreurs potentielles durant l'intersection
                    print(f"Error during intersection: {e}")
                    continue  # Continuer avec la prochaine boîte si une erreur survient
    
    return fragments  # Retourner la liste des fragments obtenus

@click.command()
@click.option('--input_path', type=click.Path(exists=True), required=True, help='Path to the OBJ file to import.')
@click.option('--grid_size', type=(int, int, int), required=True, help='Grid size for division as three integers: x y z.')
@click.option('--output_folder', type=click.Path(), required=True, help='Destination folder for the exported meshes.')
def main(input_path, grid_size, output_folder):
    # Charger le maillage à partir du chemin d'entrée
    mesh = trimesh.load_mesh(input_path)
    
    # Diviser le maillage en utilisant la grille spécifiée
    fragments = create_grid_division(mesh, grid_size)
    
    # Créer le dossier de sortie si nécessaire
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Exporter chaque fragment dans le dossier de sortie
    for i, fragment in enumerate(fragments):
        output_path = os.path.join(output_folder, f'fragment_{i}.obj')
        fragment.export(output_path)
    

if __name__ == '__main__':
    main()
