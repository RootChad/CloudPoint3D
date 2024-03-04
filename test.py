import click
import pye57
import numpy as np
from pywavefront import Wavefront

def calculate_grid_sizes(vertices, grid_size):
    # Calculate size of each section based on dimensions of OBJ object
    min_x, min_y, min_z = np.min(vertices, axis=0)
    max_x, max_y, max_z = np.max(vertices, axis=0)
    
    # Calculate grid sizes proportional to the size of the object
    grid_sizes = tuple(int(np.ceil((max_dim - min_dim) / grid_dim)) for min_dim, max_dim, grid_dim in zip((min_x, min_y, min_z), (max_x, max_y, max_z), map(int, grid_size.split('x'))))
    return grid_sizes

def section_obj(vertices, output_directory, scan_index, x, y, z, section_min_x, section_max_x, section_min_y, section_max_y, section_min_z, section_max_z):
    try:
        # Filter points within section for OBJ
        section_points_obj = vertices[(vertices[:, 0] >= section_min_x) & 
                                      (vertices[:, 0] <= section_max_x) &
                                      (vertices[:, 1] >= section_min_y) & 
                                      (vertices[:, 1] <= section_max_y) &
                                      (vertices[:, 2] >= section_min_z) & 
                                      (vertices[:, 2] <= section_max_z)]

        # Export points of OBJ to OBJ file
        section_obj_file = f"{output_directory}/section_{scan_index}_{x}_{y}_{z}.obj"
        with open(section_obj_file, 'w') as f:
            for vertex in section_points_obj:
                f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

        click.echo(f"Section OBJ {scan_index}_{x}_{y}_{z} exported successfully.")

    except Exception as e:
        click.echo(f"An error occurred during OBJ sectioning: {str(e)}")

def section_e57(data, output_directory, grid_sizes, scan_index, x, y, z, min_x, max_x, min_y, max_y, min_z, max_z):
    try:
        # Calculate section sizes based on object bounding box
        section_size_x = (max_x - min_x) / grid_sizes[0]
        section_size_y = (max_y - min_y) / grid_sizes[1]
        section_size_z = (max_z - min_z) / grid_sizes[2]

        # Determine section boundaries
        section_min_x = min_x + x * section_size_x
        section_max_x = min_x + (x + 1) * section_size_x
        section_min_y = min_y + y * section_size_y
        section_max_y = min_y + (y + 1) * section_size_y
        section_min_z = min_z + z * section_size_z
        section_max_z = min_z + (z + 1) * section_size_z

        # Filter points within section for E57
        section_points_e57 = []
        for i in range(len(data['cartesianX'])):
            if (section_min_x <= data['cartesianX'][i] <= section_max_x and
                section_min_y <= data['cartesianY'][i] <= section_max_y and
                section_min_z <= data['cartesianZ'][i] <= section_max_z):
                section_points_e57.append([data['cartesianX'][i], data['cartesianY'][i], data['cartesianZ'][i]])

        # Create dictionary for scan fields if section_points is not empty
        if section_points_e57:
            scan_fields = {
                'cartesianX': np.array([point[0] for point in section_points_e57]),
                'cartesianY': np.array([point[1] for point in section_points_e57]),
                'cartesianZ': np.array([point[2] for point in section_points_e57])
            }

            # Create new E57 file for section
            section_output_file = f"{output_directory}/section_{scan_index}_{x}_{y}_{z}.e57"
            with pye57.E57(section_output_file, mode='w') as section_e57_file:
                section_e57_file.write_scan_raw(scan_fields)

            click.echo(f"Section E57 {scan_index}_{x}_{y}_{z} exported successfully.")
        

    except Exception as e:
        click.echo(f"An error occurred during E57 sectioning: {str(e)}")

@click.command()
@click.argument('e57_file', type=click.Path(exists=True))
@click.argument('obj_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_e57_and_obj(e57_file, obj_file, output_directory, grid_size):
    try:
        # Load the E57 file
        with pye57.E57(e57_file) as e57_file:
            scan_count = e57_file.scan_count
            for scan_index in range(scan_count):
                data = e57_file.read_scan(scan_index, ignore_missing_fields=True)

                # Extract cartesian coordinates for E57
                cartesian_x = data['cartesianX']
                cartesian_y = data['cartesianY']
                cartesian_z = data['cartesianZ']

                # Determine bounding box of the object for E57
                min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
                min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
                min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)

                # Calculate grid sizes proportional to the size of OBJ object
                obj_mesh = Wavefront(obj_file)
                obj_vertices = np.array(obj_mesh.vertices)
                grid_sizes = calculate_grid_sizes(obj_vertices, grid_size)

                # Sectioning for E57
                for x in range(grid_sizes[0]):
                    for y in range(grid_sizes[1]):
                        for z in range(grid_sizes[2]):
                            section_e57(data, output_directory, grid_sizes, scan_index, x, y, z, min_x, max_x, min_y, max_y, min_z, max_z)

        # Load the OBJ file
        obj_mesh = Wavefront(obj_file)
        vertices = np.array(obj_mesh.vertices)

        # Sectioning for OBJ
        for x in range(grid_sizes[0]):
            for y in range(grid_sizes[1]):
                for z in range(grid_sizes[2]):
                    section_min_x = min_x + x * section_size_x
                    section_max_x = min_x + (x + 1) * section_size_x
                    section_min_y = min_y + y * section_size_y
                    section_max_y = min_y + (y + 1) * section_size_y
                    section_min_z = min_z + z * section_size_z
                    section_max_z = min_z + (z + 1) * section_size_z

                    section_obj(vertices, output_directory, scan_index, x, y, z, section_min_x, section_max_x, section_min_y, section_max_y, section_min_z, section_max_z)

    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_e57_and_obj()
