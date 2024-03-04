

import click
import meshlib.mrmeshpy as mr
from meshlib.mrmeshpy import BooleanOperation
from meshlib.mrmeshpy import Mesh
from meshlib import mrmeshnumpy as mn
import numpy as np
import plotly.graph_objects as go
@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_obj(input_file, output_directory, grid_size):

        grid_sizes = tuple(map(int, grid_size.split('x')))
        # Load OBJ file
        mesh = mr.loadMesh( input_file )
        #print(mn.getNumpyVerts(mesh))
        vertices = mn.getNumpyVerts(mesh)
        faces = mn.getNumpyFaces(mesh.topology)
        # draw
        # prepare data for plotly
        #mr.cutMeshWithPlane(mesh, mr.Plane3f(), mr.FaceMap())
        print("Faces ")
        print(faces)
        # Determine bounding box of the object
        min_x, max_x = vertices[:, 0].min(), vertices[:, 0].max()
        min_y, max_y = vertices[:, 1].min(), vertices[:, 1].max()
        min_z, max_z = vertices[:, 2].min(), vertices[:, 2].max()
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
                    
                    # Create cutting plane
                    plane = np.array([[section_min_x, section_min_y, section_min_z],
                                      [section_max_x, section_min_y, section_min_z],
                                      [section_max_x, section_max_y, section_min_z]])
                    plane_faces = np.array([[0, 1, 2]])
                    # Convert plane to Mesh object
                    #plane_mesh = mn.getNumpyVerts(plane)
                    plane_mesh = mn.meshFromFacesVerts(plane_faces,plane)
                    # Perform boolean intersection operation
                    print(plane)
                    result_mesh = mr.boolean(mesh, plane_mesh, BooleanOperation.DifferenceAB)
                    # Write resulting mesh to file
                    section_output_file = f"{output_directory}/section_{x}_{y}_{z}.obj"
                    
                    mr.saveMesh(result_mesh.mesh, section_output_file)
                    click.echo(f"Section {x}_{y}_{z} exported successfully.")

        click.echo("All sections exported successfully.")
        

if __name__ == '__main__':
    section_obj()
