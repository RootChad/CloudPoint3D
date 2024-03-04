import click
import pye57
import numpy as np

def read_point_cloud(input_file):
    with pye57.E57(input_file) as e57_file:
        scan_count = e57_file.scan_count
        for scan_index in range(scan_count):
            yield e57_file.read_scan(scan_index, ignore_missing_fields=True)

def calculate_section_boundaries(cartesian_coords, grid_sizes):
    min_x, max_x = np.min(cartesian_coords['cartesianX']), np.max(cartesian_coords['cartesianX'])
    min_y, max_y = np.min(cartesian_coords['cartesianY']), np.max(cartesian_coords['cartesianY'])
    min_z, max_z = np.min(cartesian_coords['cartesianZ']), np.max(cartesian_coords['cartesianZ'])

    section_size_x = (max_x - min_x) / grid_sizes[0]
    section_size_y = (max_y - min_y) / grid_sizes[1]
    section_size_z = (max_z - min_z) / grid_sizes[2]

    return min_x, max_x, min_y, max_y, min_z, max_z, section_size_x, section_size_y, section_size_z

def filter_points_within_section(cartesian_coords, section_boundaries):
    section_min_x, section_max_x, section_min_y, section_max_y, section_min_z, section_max_z = section_boundaries
    section_points = []

    for i in range(len(cartesian_coords['cartesianX'])):
        if (section_min_x <= cartesian_coords['cartesianX'][i] <= section_max_x and
            section_min_y <= cartesian_coords['cartesianY'][i] <= section_max_y and
            section_min_z <= cartesian_coords['cartesianZ'][i] <= section_max_z):
            section_points.append([cartesian_coords['cartesianX'][i], cartesian_coords['cartesianY'][i], cartesian_coords['cartesianZ'][i]])

    return section_points

def export_section(scan_index, section_coords, output_directory, section_index):
    section_output_file = f"{output_directory}/section_{scan_index}_{section_index[0]}_{section_index[1]}_{section_index[2]}.e57"
    with pye57.E57(section_output_file, mode='w') as section_e57_file:
        section_e57_file.write_scan_raw({
            'cartesianX': np.array([point[0] for point in section_coords]),
            'cartesianY': np.array([point[1] for point in section_coords]),
            'cartesianZ': np.array([point[2] for point in section_coords])
        })

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_e57(input_file, output_directory, grid_size):
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))
        for point_cloud_data in read_point_cloud(input_file):
            section_boundaries = calculate_section_boundaries(point_cloud_data, grid_sizes)

            for x in range(grid_sizes[0]):
                for y in range(grid_sizes[1]):
                    for z in range(grid_sizes[2]):
                        section_index = (x, y, z)
                        section_points = filter_points_within_section(point_cloud_data, section_boundaries)

                        if section_points:
                            export_section(point_cloud_data['scanIndex'], section_points, output_directory, section_index)
                            click.echo(f"Section {point_cloud_data['scanIndex']}_{x}_{y}_{z} exported successfully.")
                        else:
                            click.echo(f"No points found in section {point_cloud_data['scanIndex']}_{x}_{y}_{z}. Skipping.")

        click.echo("All sections exported successfully.")

    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_e57()
