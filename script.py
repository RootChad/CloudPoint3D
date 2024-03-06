import os
import click
import trimesh
import pye57
import numpy as np
import pyglet as pg
def center_data(mesh, point_cloud_data):
    # Centrer le maillage
    mesh_center = mesh.bounds.mean(axis=0)
    mesh.apply_translation(-mesh_center)

    # Centrer le nuage de points
    point_cloud_center = np.mean(point_cloud_data, axis=0)
    centered_point_cloud_data = point_cloud_data - point_cloud_center

    return mesh, centered_point_cloud_data
def calculate_combined_bounds(mesh, point_cloud_data):
    mesh_bounds = mesh.bounds
    point_cloud_bounds = np.array([
        [np.min(point_cloud_data[:, 0]), np.min(point_cloud_data[:, 1]), np.min(point_cloud_data[:, 2])],
        [np.max(point_cloud_data[:, 0]), np.max(point_cloud_data[:, 1]), np.max(point_cloud_data[:, 2])]
    ])
    combined_min = np.minimum(mesh_bounds[0], point_cloud_bounds[0])
    combined_max = np.maximum(mesh_bounds[1], point_cloud_bounds[1])
    return combined_min, combined_max

def segment_based_on_grid(data, division_points, output_folder, data_type, scan_index=None):
    for i in range(len(division_points[0]) - 1):
        for j in range(len(division_points[1]) - 1):
            for k in range(len(division_points[2]) - 1):
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]

                if data_type == 'mesh':
                    center = [(min_corner[0] + max_corner[0]) / 2, (min_corner[1] + max_corner[1]) / 2, (min_corner[2] + max_corner[2]) / 2]
                    extents = [max_corner[0] - min_corner[0], max_corner[1] - min_corner[1], max_corner[2] - min_corner[2]]
                    box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))
                    
                    result = trimesh.boolean.intersection([data, box], engine='blender')
                    box_path = os.path.join(output_folder, f'box_{i}_{j}_{k}.obj')
                    box.export(box_path)
                    if isinstance(result, (trimesh.Scene, trimesh.Trimesh)) and not result.is_empty:
                        fragment_path = os.path.join(output_folder, f'mesh_fragment_{i}_{j}_{k}.obj')
                        
                        result.export(fragment_path)

                elif data_type == 'point_cloud':
                    section_points = data[(data[:, 0] >= min_corner[0]) & (data[:, 0] <= max_corner[0]) &
                                          (data[:, 1] >= min_corner[1]) & (data[:, 1] <= max_corner[1]) &
                                          (data[:, 2] >= min_corner[2]) & (data[:, 2] <= max_corner[2])]
                    if section_points.size > 0:
                        section_output_file = f"{output_folder}/section_{scan_index}_{i}_{j}_{k}.e57"
                        with pye57.E57(section_output_file, mode='w') as section_e57_file:
                            scan_fields = {
                                'cartesianX': section_points[:, 0],
                                'cartesianY': section_points[:, 1],
                                'cartesianZ': section_points[:, 2],
                            }
                            section_e57_file.write_scan_raw(scan_fields)

def main(obj_file, e57_file, output_directory, grid_size):
    grid_sizes = tuple(map(int, grid_size.split('x')))
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    mesh = trimesh.load_mesh(obj_file) if obj_file else None
    point_cloud_data = None
    if e57_file:
        with pye57.E57(e57_file) as e57_file:
            data = e57_file.read_scan(0, ignore_missing_fields=True)
            point_cloud_data = np.column_stack((data['cartesianX'], data['cartesianY'], data['cartesianZ']))

    if mesh and point_cloud_data is not None:
        mesh, centered_point_cloud_data = center_data(mesh, point_cloud_data)
        combined_min, combined_max = calculate_combined_bounds(mesh, centered_point_cloud_data)
        #combined_min, combined_max = calculate_combined_bounds(mesh, point_cloud_data)
        division_points = [np.linspace(start, end, num=div+1) for start, end, div in zip(combined_min, combined_max, grid_sizes)]

        segment_based_on_grid(mesh, division_points, output_directory, 'mesh')
        segment_based_on_grid(centered_point_cloud_data, division_points, output_directory, 'point_cloud', scan_index=0)

@click.command()
@click.option('--obj_file', type=click.Path(exists=True), help='Path to the OBJ file. Optional.')
@click.option('--e57_file', type=click.Path(exists=True), help='Path to the E57 file. Optional.')
@click.option('--output_directory', type=click.Path(), required=True, help='Directory to save the output sections.')
@click.option('--grid_size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def cli(obj_file, e57_file, output_directory, grid_size):
    main(obj_file, e57_file, output_directory, grid_size)

if __name__ == '__main__':
    cli()
