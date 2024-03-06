import os
import click
import trimesh
import pye57
import numpy as np

def segment_mesh(mesh, divisions, output_folder):
    # Calculer les points de division pour chaque axe en fonction des limites du maillage et du nombre de divisions
    bounds = mesh.bounds
    division_points = [np.linspace(start, end, num=div+1) for start, end, div in zip(bounds[0], bounds[1], divisions)]
    
    # Parcourir chaque cellule définie par la grille et effectuer une intersection avec le maillage
    for i in range(divisions[0]):
        for j in range(divisions[1]):
            for k in range(divisions[2]):
                # Calculer les coins min et max de la cellule actuelle
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]
                # Déterminer le centre et les dimensions de la cellule
                center = [(min_corner[0] + max_corner[0]) / 2, (min_corner[1] + max_corner[1]) / 2, (min_corner[2] + max_corner[2]) / 2]
                extents = [max_corner[0] - min_corner[0], max_corner[1] - min_corner[1], max_corner[2] - min_corner[2]]                
                # Créer une boîte pour cette cellule
                box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))                
                try:
                    # Tenter une intersection entre le maillage et la boîte
                    result = trimesh.boolean.intersection([mesh, box], engine='blender')
                    # Traiter le résultat de l'intersection
                    if isinstance(result, trimesh.Scene):
                        combined_mesh = result.dump(concatenate=True)
                        if not combined_mesh.is_empty:
                            fragment_path = os.path.join(output_folder, f'fragment_{i}_{j}_{k}.obj')
                            combined_mesh.export(fragment_path)
                    elif isinstance(result, trimesh.Trimesh) and not result.is_empty:
                        fragment_path = os.path.join(output_folder, f'fragment_{i}_{j}_{k}.obj')
                        result.export(fragment_path)
                except Exception as e:
                    print(f"Error during intersection: {e}")

def segment_point_cloud(input_file, divisions, output_folder):
    # Ouvrir le fichier E57 et lire les données du nuage de points
    with pye57.E57(input_file) as e57_file:
        scan_count = e57_file.scan_count
        for scan_index in range(scan_count):
            data = e57_file.read_scan(scan_index, ignore_missing_fields=True)
            # Extraire les coordonnées cartésiennes
            cartesian_x = data['cartesianX']
            cartesian_y = data['cartesianY']
            cartesian_z = data['cartesianZ']
            # Calculer la boîte englobante du nuage de points
            min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
            min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
            min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)
            # Déterminer la taille de chaque section
            section_size_x = (max_x - min_x) / divisions[0]
            section_size_y = (max_y - min_y) / divisions[1]
            section_size_z = (max_z - min_z) / divisions[2]

            # Séparer le nuage de points en sections basées sur la grille spécifiée
            for x in range(divisions[0]):
                for y in range(divisions[1]):
                    for z in range(divisions[2]):
                        # Définir les limites de chaque section
                        section_min_x = min_x + x * section_size_x
                        section_max_x = min_x + (x + 1) * section_size_x
                        section_min_y = min_y + y * section_size_y
                        section_max_y = min_y + (y + 1) * section_size_y
                        section_min_z = min_z + z * section_size_z
                        section_max_z = min_z + (z + 1) * section_size_z

                        # Filtrer les points à l'intérieur de la section
                        section_points = [ [cartesian_x[i], cartesian_y[i], cartesian_z[i]] 
                                           for i in range(len(cartesian_x)) 
                                           if section_min_x <= cartesian_x[i] <= section_max_x 
                                           and section_min_y <= cartesian_y[i] <= section_max_y 
                                           and section_min_z <= cartesian_z[i] <= section_max_z ]

                        # Enregistrer les points de la section dans un nouveau fichier E57 si des points sont présents
                        if section_points:
                            scan_fields = {
                                'cartesianX': np.array([point[0] for point in section_points]),
                                'cartesianY': np.array([point[1] for point in section_points]),
                                'cartesianZ': np.array([point[2] for point in section_points]),
                            }
                            section_output_file = f"{output_folder}/section_{scan_index}_{x}_{y}_{z}.e57"
                            with pye57.E57(section_output_file, mode='w') as section_e57_file:
                                section_e57_file.write_scan_raw(scan_fields)

@click.command()
@click.option('--obj_file', type=click.Path(exists=True), help='Path to the OBJ file. Optional.')
@click.option('--e57_file', type=click.Path(exists=True), help='Path to the E57 file. Optional.')
@click.option('--output_directory', type=click.Path(), required=True, help='Directory to save the output sections.')
@click.option('--grid_size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def main(obj_file, e57_file, output_directory, grid_size):
    # Convertir la taille de la grille en tuple d'entiers
    grid_sizes = tuple(map(int, grid_size.split('x')))
    
    # Créer le répertoire de sortie si nécessaire
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Segmenter le fichier OBJ si fourni
    if obj_file:
        mesh = trimesh.load_mesh(obj_file)
        segment_mesh(mesh, grid_sizes, output_directory)
    
    # Segmenter le fichier E57 si fourni
    if e57_file:
        segment_point_cloud(e57_file, grid_sizes, output_directory)

if __name__ == '__main__':
    main()
