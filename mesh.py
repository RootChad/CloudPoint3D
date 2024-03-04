import os
import trimesh
import numpy as np
import click

def create_grid_division(mesh, divisions):
    bounds = mesh.bounds
    division_points = [np.linspace(start, end, num=div+1) for start, end, div in zip(bounds[0], bounds[1], divisions)]
    
    fragments = []
    
    for i in range(divisions[0]):
        for j in range(divisions[1]):
            for k in range(divisions[2]):
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]
                center = [(min_corner[0] + max_corner[0]) / 2, (min_corner[1] + max_corner[1]) / 2, (min_corner[2] + max_corner[2]) / 2]
                extents = [max_corner[0] - min_corner[0], max_corner[1] - min_corner[1], max_corner[2] - min_corner[2]]                
                box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))                
                try:
                    result = trimesh.boolean.intersection([mesh, box], engine='blender')                    
                    if isinstance(result, trimesh.Scene):
                        # Si le résultat est une scène, tenter de combiner tous les objets mesh en un seul mesh
                        combined_mesh = result.dump(concatenate=True)
                        if not combined_mesh.is_empty:
                            fragments.append(combined_mesh)
                    elif isinstance(result, trimesh.Trimesh) and not result.is_empty:
                        # Si le résultat est un maillage, l'ajouter directement
                        fragments.append(result)
                except Exception as e:
                    print(f"Error during intersection: {e}")
                    continue
    
    return fragments

@click.command()
@click.option('--input_path', type=click.Path(exists=True), required=True, help='Path to the OBJ file to import.')
@click.option('--grid_size', type=(int, int, int), required=True, help='Grid size for division as three integers: x y z.')
@click.option('--output_folder', type=click.Path(), required=True, help='Destination folder for the exported meshes.')
def main(input_path, grid_size, output_folder):
    mesh = trimesh.load_mesh(input_path)
    fragments = create_grid_division(mesh, grid_size)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for i, fragment in enumerate(fragments):
        output_path = os.path.join(output_folder, f'fragment_{i}.obj')
        fragment.export(output_path)
    

if __name__ == '__main__':
    main()
