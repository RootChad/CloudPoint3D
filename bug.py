import os
import click
import trimesh
import pye57
import numpy as np
import time
from tqdm import tqdm
import datetime
# Function to calculate the division points based on the center, box size, and grid size.
def calculate_grid_division_points(center, box_size, grid_sizes, heights=None):
    division_points = []
    for axis, (size, grid_size) in enumerate(zip(box_size, grid_sizes)):
        # For the Z axis and if specific heights are provided
        if axis == 2 and heights is not None:
            assert len(heights) == grid_size, "The number of heights must match the number of divisions on the Z axis."
            start_z = center[axis]
            points_z = [start_z + sum(heights[:i + 1]) for i in range(len(heights))]
            division_points.append([start_z] + points_z)
        else:
            # For the X and Y axes, or for the Z axis without specific heights
            total_size = size * grid_size
            start = center[axis] 
            end = center[axis] + total_size 
            points = np.linspace(start, end, num=grid_size + 1)
            division_points.append(points)
    
    return division_points

# Function to segment the mesh and point cloud based on grid division points.
def segment_based_on_grid(mesh, point_cloud_data, point_cloud_colors, division_points, output_folder):
    # Iterate over all possible box positions within the grid.
    for i in range(len(division_points[0]) - 1):
        for j in range(len(division_points[1]) - 1):
            for k in range(len(division_points[2]) - 1):
                # Determine the corners of the current box.
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]

                # Calculate the center and extents for the current box.
                center = [(min_corner[d] + max_corner[d]) / 2 for d in range(3)]
                extents = [max_corner[d] - min_corner[d] for d in range(3)]
                
                # Create a box mesh for the current section.
                box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))
                #box_path = os.path.join(output_folder, f'box_{i}_{j}_{k}.obj')
                #box.export(box_path)
                
                # Attempt to intersect the mesh with the box, exporting the result.
                try:
                    result = trimesh.boolean.intersection([mesh, box], engine='blender')
                    if isinstance(result, (trimesh.Scene, trimesh.Trimesh)) and not result.is_empty:
                        result.unmerge_vertices()
                        fragment_path = os.path.join(output_folder, f'mesh_fragment_{i}_{j}_{k}.obj')                        
                        result.export(fragment_path)
                except Exception as e:
                    print(f"Error intersecting mesh and box: {e}")

                # Segment the point cloud based on the current box.
                in_box = np.all((point_cloud_data >= min_corner) & (point_cloud_data <= max_corner), axis=1)
                section_points = point_cloud_data[in_box]
                if point_cloud_colors is not None:
                    section_colors = point_cloud_colors[in_box]
                else:
                    # Handle the case where there are no color data
                    section_colors = None  # Or an appropriate default value
                
                if section_points.size > 0:
                    section_output_file = os.path.join(output_folder, f'point_cloud_section_{i}_{j}_{k}.e57')
                    with pye57.E57(section_output_file, mode='w') as section_e57_file:
                        scan_fields = {
                            'cartesianX': section_points[:, 0],
                            'cartesianY': section_points[:, 1],
                            'cartesianZ': section_points[:, 2]
                        }
                        # Include color data if available
                        if section_colors is not None:
                            scan_fields.update({
                                'colorRed': section_colors[:, 0],
                                'colorGreen': section_colors[:, 1],
                                'colorBlue': section_colors[:, 2],
                            })
                        section_e57_file.write_scan_raw(scan_fields)

# CLI command setup using click to parse arguments.
@click.command()
@click.option('--obj_file', type=click.Path(exists=True), help='Path to the OBJ file.')
@click.option('--e57_file', type=click.Path(exists=True), help='Path to the E57 file.')
@click.option('--output_directory', type=click.Path(), required=True, help='Directory to save the output sections.')
@click.option('--grid_size', type=str, default='5x5x5', help='Grid size for sectioning, format: x,y,z')
@click.option('--box_size', type=str, default='1x1x1', help='Box size for sectioning, format: x,y,z')
@click.option('--heights', type=str, default='', help='List of heights for each Z layer, separated by commas. Example: "1.5,2"')
@click.option('--center', type=str, default='0,0,0', help='Center of the grid in format x,y,z. Default is "0,0,0".')
def main(obj_file, e57_file, output_directory, grid_size, box_size, heights, center):
    # Ensure the output directory exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Parse grid and box sizes from strings to tuples.
    grid_sizes = tuple(map(int, grid_size.split('x')))
    box_sizes = tuple(map(float, box_size.split('x')))
    heights_list = [float(h) for h in heights.split(',')] if heights else None
    center_list = [float(c) for c in center.split(',')]

    # Load the mesh with progress tracking
    print("Loading OBJ file...")
    with tqdm(total=1, desc="OBJ Progress") as pbar:
        start_time = time.time()
        mesh = trimesh.load(obj_file) if obj_file else None
        elapsed_time = time.time() - start_time
        pbar.update(1)
        pbar.set_postfix_str(f"Time taken: {datetime.timedelta(seconds=round(elapsed_time))}")

    # Load the point cloud with progress tracking
    print("Loading E57 file...")
    # Load the mesh and point cloud data, if provided.
    mesh = trimesh.load(obj_file) if obj_file else None
    point_cloud_data = None
    point_cloud_colors = None  # Initialize for storing color data.
    if e57_file:
        with pye57.E57(e57_file) as e57_file:
            data = e57_file.read_scan(0, colors=True, ignore_missing_fields=True)
            point_cloud_data = np.column_stack((data['cartesianX'], data['cartesianY'], data['cartesianZ']))
            if 'colorRed' in data and 'colorGreen' in data and 'colorBlue' in data:
                point_cloud_colors = np.column_stack((data['colorRed'], data['colorGreen'], data['colorBlue']))
                
    # Proceed with segmentation if mesh and point cloud data are available.
    if mesh and point_cloud_data is not None:
        division_points = calculate_grid_division_points(center_list, box_sizes, grid_sizes, heights=heights_list)
        segment_based_on_grid(mesh, point_cloud_data, point_cloud_colors, division_points, output_directory)

if __name__ == '__main__':
    main()
