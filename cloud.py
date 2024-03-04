import os
import click
from e57 import E57File
from pyvista import read_mesh

@click.command()
@click.option(
    "-i",
    "--input_e57",
    type=click.Path(exists=True),
    required=True,
    help="Chemin vers le fichier E57 d'entrée",
)
@click.option(
    "-m",
    "--input_obj",
    type=click.Path(exists=True),
    required=True,
    help="Chemin vers le modèle 3D OBJ d'entrée",
)
@click.option(
    "-g",
    "--grid_size",
    type=click.Tuple([int, int, int]),
    default=(5, 5, 5),
    help="Taille de la grille de sectionnement (x, y, z)",
)
@click.option(
    "-o",
    "--output_dir",
    type=click.Path(exists=True),
    required=True,
    help="Dossier de sortie pour les sections",
)
def main(input_e57, input_obj, grid_size, output_dir):

    # Chargement des données
    e57_file = E57File(input_e57)
    point_cloud = e57_file.point_cloud
    mesh = read_mesh(input_obj)

    # Sectionnement du nuage de points et du modèle 3D
    sections_e57 = []
    sections_obj = []

    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            for k in range(grid_size[2]):
                # Définir la section du nuage de points
                section_cloud = point_cloud.subsample_aabb(
                    (i * grid_size[0], j * grid_size[1], k * grid_size[2]),
                    ((i + 1) * grid_size[0], (j + 1) * grid_size[1], (k + 1) * grid_size[2]),
                )

                # Définir la section du modèle 3D
                section_mesh = mesh.clip_box(
                    (i * grid_size[0], j * grid_size[1], k * grid_size[2]),
                    ((i + 1) * grid_size[0], (j + 1) * grid_size[1], (k + 1) * grid_size[2]),
                )

                # Sauvegarder les sections
                sections_e57.append(section_cloud)
                sections_obj.append(section_mesh)

    # Exportation des sections
    for i, section_e57 in enumerate(sections_e57):
        output_e57_path = os.path.join(output_dir, f"section_{i:03d}.e57")
        section_e57.export(output_e57_path)

    for i, section_obj in enumerate(sections_obj):
        output_obj_path = os.path.join(output_dir, f"section_{i:03d}.obj")
        section_obj.export(output_obj_path)

if __name__ == "__main__":
    main()
