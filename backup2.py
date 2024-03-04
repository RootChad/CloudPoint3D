import click
import pye57
import numpy as np
from pywavefront import Wavefront

@click.command()
@click.argument('e57_file', type=click.Path(exists=True))
@click.argument('obj_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_e57_and_obj(e57_file, obj_file, output_directory, grid_size):
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))

        # Load the E57 file
        with pye57.E57(e57_file) as e57_file:
            scan_count = e57_file.scan_count
            for scan_index in range(scan_count):
                data = e57_file.read_scan(scan_index, ignore_missing_fields=True)

                # Extract cartesian coordinates
                cartesian_x = data['cartesianX']
                cartesian_y = data['cartesianY']
                cartesian_z = data['cartesianZ']

                # Check if any points exist in E57 data
                if len(cartesian_x) == 0:
                    click.echo(f"No points found in E57 data for scan {scan_index}. Skipping.")
                    continue

                # Determine center of gravity for E57 points
                e57_center = np.mean(np.vstack((cartesian_x, cartesian_y, cartesian_z)), axis=1)

                # Determine bounding box of the object
                min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
                min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
                min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)

                # Calculate section sizes based on object bounding box
                section_size_x = (max_x - min_x) / grid_sizes[0]
                section_size_y = (max_y - min_y) / grid_sizes[1]
                section_size_z = (max_z - min_z) / grid_sizes[2]

                # Load the OBJ model
                obj_mesh = Wavefront(obj_file)
                print("Vertices ")
                print(obj_mesh.vertices)
                # Extract vertices from the OBJ mesh
                vertices = np.array(obj_mesh.vertices)

                # Check if any vertices exist in OBJ data
                if len(vertices) == 0:
                    click.echo("No vertices found in OBJ data. Skipping.")
                    continue

                # Determine center of gravity for OBJ points
                obj_center = np.mean(vertices, axis=0)

                # Compute translation to align OBJ with E57
                translation = e57_center - obj_center

                # Apply translation to OBJ vertices
                vertices += translation

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

                            # Filter points within section for E57
                            section_points_e57 = []
                            for i in range(len(cartesian_x)):
                                if (section_min_x <= cartesian_x[i] <= section_max_x and
                                    section_min_y <= cartesian_y[i] <= section_max_y and
                                    section_min_z <= cartesian_z[i] <= section_max_z):
                                    section_points_e57.append([cartesian_x[i], cartesian_y[i], cartesian_z[i]])

                            # Filter points within section for OBJ
                            section_points_obj = vertices[(vertices[:, 0] >= section_min_x) & 
                                                          (vertices[:, 0] <= section_max_x) &
                                                          (vertices[:, 1] >= section_min_y) & 
                                                          (vertices[:, 1] <= section_max_y) &
                                                          (vertices[:, 2] >= section_min_z) & 
                                                          (vertices[:, 2] <= section_max_z)]
                            # Debug prints
                            print("Section boundaries:")
                            print(f"X: {section_min_x} - {section_max_x}")
                            print(f"Y: {section_min_y} - {section_max_y}")
                            print(f"Z: {section_min_z} - {section_max_z}")

                            print(f"Number of points in section: {len(section_points_obj)}")
                            # Debug print vertices
                            print("Vertices in section:")
                            print(vertices[:, 0])
                            # Export points of OBJ to OBJ file
                            print(section_points_obj)
                            section_obj_file = f"{output_directory}/section_{scan_index}_{x}_{y}_{z}.obj"
                            with open(section_obj_file, 'w') as f:
                                for vertex in section_points_obj:
                                    f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

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

                                click.echo(f"Section {scan_index}_{x}_{y}_{z} exported successfully.")
                            else:
                                click.echo(f"No points found in section {scan_index}_{x}_{y}_{z}. Skipping.")

    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_e57_and_obj()
