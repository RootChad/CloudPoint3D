import click
from pywavefront import Wavefront
import numpy as np

def calculate_normals(vertices, faces):
    normals = np.zeros(vertices.shape, dtype=np.float32)
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        normals[face] += normal

    norms = np.linalg.norm(normals, axis=1)
    epsilon = 1e-8  # Small value to avoid division by very small numbers
    norms = np.where(norms > epsilon, norms, 1)  # Avoid division by zero or small numbers
    normals /= norms[:, np.newaxis]  # Divide normals by their norms
    return normals


def showLogo():
    logo = """
  ____                 _     _____ _           _   
 |  _ \               | |   / ____| |         | |  
 | |_) |_ __ ___  __ _| |_ | |    | |__   __ _| |_ 
 |  _ <| '__/ _ \/ _` | __|| |    | '_ \ / _` | __|
 | |_) | | |  __/ (_| | |_ | |____| | | | (_| | |_ 
 |____/|_|  \___|\__,_|\__| \_____|_| |_|\__,_|\__|
"""
    click.echo(logo)

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_obj(input_file, output_directory, grid_size):
    showLogo()
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))
        
        # Load OBJ file and parse data
        obj_mesh = Wavefront(input_file, collect_faces=True)
        
        # Extract vertices
        vertices = np.array(obj_mesh.vertices)
        
        # Extract faces
        faces = np.concatenate([np.array(mesh.faces) for mesh in obj_mesh.mesh_list])
        print(faces)
        # Calculate normals
        normals = calculate_normals(vertices, faces)
        
        # Determine bounding box of the object
        min_x, max_x = np.min(vertices[:, 0]), np.max(vertices[:, 0])
        min_y, max_y = np.min(vertices[:, 1]), np.max(vertices[:, 1])
        min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])
        
        # Calculate section sizes based on object bounding box
        section_size_x = (max_x - min_x) / grid_sizes[0]
        section_size_y = (max_y - min_y) / grid_sizes[1]
        section_size_z = (max_z - min_z) / grid_sizes[2]
        
        # Iterate over grid and create sections
        for x in range(grid_sizes[0]):
            for y in range(grid_sizes[1]):
                for z in range(grid_sizes[2]):
                    # Define section boundaries
                    section_min_x = min_x + x * section_size_x
                    section_max_x = min_x + (x + 1) * section_size_x
                    section_min_y = min_y + y * section_size_y
                    section_max_y = min_y + (y + 1) * section_size_y
                    section_min_z = min_z + z * section_size_z
                    section_max_z = min_z + (z + 1) * section_size_z
                    
                    # Filter vertices within section
                    section_vertices = []
                    section_normals = []
                    for i, vertex in enumerate(vertices):
                        if (section_min_x <= vertex[0] <= section_max_x and
                            section_min_y <= vertex[1] <= section_max_y and
                            section_min_z <= vertex[2] <= section_max_z):
                            section_vertices.append(vertex)
                            section_normals.append(normals[i])
                    
                    # Filter faces within section
                    section_faces = []
                    for face in faces:
                        face_vertices = vertices[face]
                        if ((face_vertices[:, 0] >= section_min_x) & (face_vertices[:, 0] <= section_max_x) &
                            (face_vertices[:, 1] >= section_min_y) & (face_vertices[:, 1] <= section_max_y) &
                            (face_vertices[:, 2] >= section_min_z) & (face_vertices[:, 2] <= section_max_z)).all():
                            section_faces.append(face)
                    
                    # Write section data to OBJ file
                    section_output_file = f"{output_directory}/section_{x}_{y}_{z}.obj"
                    with open(section_output_file, 'w') as section_obj_file:
                        # Write vertices
                        for vertex in section_vertices:
                            section_obj_file.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
                        # Write normals
                        for normal in section_normals:
                            section_obj_file.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
                        # Write faces
                        for face in section_faces:
                            vertex_indices = face + 1  # OBJ indices are 1-based
                            section_obj_file.write("f " + " ".join(map(str, vertex_indices)) + "\n")

                    click.echo(f"Section {x}_{y}_{z} exported successfully.")

        click.echo("All sections exported successfully.")
        
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_obj()
