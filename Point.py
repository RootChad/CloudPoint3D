import click
import pye57
import numpy as np

@click.command()
@click.argument('input_file', type=click.Path(exists=True))  # Chemin vers le fichier d'entrée E57.
@click.argument('output_directory', type=click.Path())  # Répertoire pour stocker les fichiers sectionnés.
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')  # Taille de la grille pour la section.
def section_e57(input_file, output_directory, grid_size):
    try:
        # Convertir la taille de la grille en tuple de trois entiers.
        grid_sizes = tuple(map(int, grid_size.split('x')))
        
        # Ouvrir le fichier E57.
        with pye57.E57(input_file) as e57_file:
            # Obtenir le nombre de scans dans le fichier E57.
            scan_count = e57_file.scan_count
            
            # Itérer sur chaque scan.
            for scan_index in range(scan_count):
                # Lire les données du scan, en ignorant les champs manquants.
                data = e57_file.read_scan(scan_index, ignore_missing_fields=True)

                # Extraire les coordonnées cartésiennes.
                cartesian_x = data['cartesianX']
                cartesian_y = data['cartesianY']
                cartesian_z = data['cartesianZ']

                # Déterminer la boîte englobante de l'objet.
                min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
                min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
                min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)

                # Calculer la taille de chaque section basée sur la boîte englobante.
                section_size_x = (max_x - min_x) / grid_sizes[0]
                section_size_y = (max_y - min_y) / grid_sizes[1]
                section_size_z = (max_z - min_z) / grid_sizes[2]

                # Itérer sur la grille pour créer des sections.
                for x in range(grid_sizes[0]):
                    for y in range(grid_sizes[1]):
                        for z in range(grid_sizes[2]):
                            # Définir les limites de la section.
                            section_min_x = min_x + x * section_size_x
                            section_max_x = min_x + (x + 1) * section_size_x
                            section_min_y = min_y + y * section_size_y
                            section_max_y = min_y + (y + 1) * section_size_y
                            section_min_z = min_z + z * section_size_z
                            section_max_z = min_z + (z + 1) * section_size_z

                            # Filtrer les points à l'intérieur de la section.
                            section_points = []
                            for i in range(len(cartesian_x)):
                                if (section_min_x <= cartesian_x[i] <= section_max_x and
                                    section_min_y <= cartesian_y[i] <= section_max_y and
                                    section_min_z <= cartesian_z[i] <= section_max_z):
                                    section_points.append([cartesian_x[i], cartesian_y[i], cartesian_z[i]])

                            # Créer un dictionnaire pour les champs du scan si section_points n'est pas vide.
                            if section_points:
                                scan_fields = {
                                    'cartesianX': np.array([point[0] for point in section_points]),
                                    'cartesianY': np.array([point[1] for point in section_points]),
                                    'cartesianZ': np.array([point[2] for point in section_points])
                                }

                                # Créer un nouveau fichier E57 pour la section.
                                section_output_file = f"{output_directory}/section_{scan_index}_{x}_{y}_{z}.e57"
                                with pye57.E57(section_output_file, mode='w') as section_e57_file:
                                    section_e57_file.write_scan_raw(scan_fields)

                                click.echo(f"Section {scan_index}_{x}_{y}_{z} exported successfully.")
                            else:
                                click.echo(f"No points found in section {scan_index}_{x}_{y}_{z}. Skipping.")

            click.echo("All sections exported successfully.")

    except Exception as e:
        # Gérer les exceptions potentielles.
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_e57()
