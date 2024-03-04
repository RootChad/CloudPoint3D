import click
import pye57
import numpy as np

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_e57(input_file, output_directory, grid_size):
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))
        with pye57.E57(input_file) as e57_file:
            # Read point cloud data
            scan_count = e57_file.scan_count
            for scan_index in range(scan_count):
                data = e57_file.read_scan(scan_index, ignore_missing_fields=True)

                # Extract cartesian coordinates
                cartesian_x = data['cartesianX']
                cartesian_y = data['cartesianY']
                cartesian_z = data['cartesianZ']

                # Determine bounding box of the object
                min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
                min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
                min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)

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

                            # Filter points within section
                            section_points = []
                            for i in range(len(cartesian_x)):
                                if (section_min_x <= cartesian_x[i] <= section_max_x and
                                    section_min_y <= cartesian_y[i] <= section_max_y and
                                    section_min_z <= cartesian_z[i] <= section_max_z):
                                    section_points.append([cartesian_x[i], cartesian_y[i], cartesian_z[i]])

                            # Create dictionary for scan fields if section_points is not empty
                            if section_points:
                                scan_fields = {
                                    'cartesianX': np.array([point[0] for point in section_points]),
                                    'cartesianY': np.array([point[1] for point in section_points]),
                                    'cartesianZ': np.array([point[2] for point in section_points])
                                }

                                # Create new E57 file for section
                                section_output_file = f"{output_directory}/section_{scan_index}_{x}_{y}_{z}.e57"
                                with pye57.E57(section_output_file, mode='w') as section_e57_file:
                                    section_e57_file.write_scan_raw(scan_fields)

                                click.echo(f"Section {scan_index}_{x}_{y}_{z} exported successfully.")
                            else:
                                click.echo(f"No points found in section {scan_index}_{x}_{y}_{z}. Skipping.")

            click.echo("All sections exported successfully.")

    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_e57()
