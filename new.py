import click
from pywavefront import Wavefront
import numpy as np
from itertools import combinations

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

def intersect_plane_triangle(plane_point, plane_normal, triangle):
    # Calculate triangle normal
    v0, v1, v2 = triangle
    edge1 = v1 - v0
    edge2 = v2 - v0
    triangle_normal = np.cross(edge1, edge2)

    # Check if triangle is parallel to the plane
    if np.dot(triangle_normal, plane_normal) == 0:
        return []

    # Calculate intersection point
    t = np.dot(plane_normal, (plane_point - v0)) / np.dot(plane_normal, triangle_normal)
    intersection_point = v0 + t * triangle_normal

    # Check if intersection point is inside triangle
    u = np.dot(edge1, edge1)
    v = np.dot(edge2, edge2)
    w = np.dot(intersection_point - v0, edge1)
    s = np.dot(intersection_point - v0, edge2)
    denominator = u*v - np.dot(edge1, edge2)**2
    s_param = (v*w - np.dot(edge2, intersection_point - v0)) / denominator
    t_param = (u*s - np.dot(edge1, intersection_point - v0)) / denominator

    if (0 <= s_param <= 1) and (0 <= t_param <= 1) and (s_param + t_param <= 1):
        return [intersection_point]
    else:
        return []

def section_faces(vertices, faces, plane_point, plane_normal):
    intersected_faces = []
    for face in faces:
        triangle = vertices[face]
        intersections = intersect_plane_triangle(plane_point, plane_normal, triangle)
        if intersections:
            intersected_faces.append(face)
    return intersected_faces

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_obj(input_file, output_directory, grid_size):
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))
        
        # Load OBJ file and parse data
        obj_mesh = Wavefront(input_file)
        
        # Extract vertices, faces, and normals
        vertices = np.array(obj_mesh.vertices)
        faces = np.concatenate([np.array(mesh.faces) for mesh in obj_mesh.mesh_list])
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

                    # Define section plane
                    plane_point = np.array([(section_min_x + section_max_x) / 2,
                                             (section_min_y + section_max_y) / 2,
                                             (section_min_z + section_max_z) / 2])
                    plane_normal = np.array([1.0, 0.0, 0.0])  # For example, you can adjust this normal
                    
                    # Find intersected faces
                    intersected_faces = section_faces(vertices, faces, plane_point, plane_normal)
                    
                    # Write section faces to OBJ file
                    section_output_file = f"{output_directory}/section_{x}_{y}_{z}.obj"
                    with open(section_output_file, 'w') as section_obj_file:
                        for vertex in vertices:
                            section_obj_file.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
                        for normal in normals:
                            section_obj_file.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
                        for face in intersected_faces:
                            vertex_indices = face + 1  # OBJ indices are 1-based
                            section_obj_file.write("f " + " ".join(map(str, vertex_indices)) + "\n")
                    
                    click.echo(f"Section {x}_{y}_{z} exported successfully.")

        click.echo("All sections exported successfully.")
        
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_obj()
