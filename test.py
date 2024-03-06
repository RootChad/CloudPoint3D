import os
import click
import trimesh
import pye57
import numpy as np
import pyvista as pv

def visualize_with_grid(obj_mesh, point_cloud, grid_sizes, bounds):
    # Vérifier si l'objet est une Scene et le convertir en Mesh si nécessaire
    if isinstance(obj_mesh, trimesh.Scene):
        # Si obj_mesh est une Scene, concaténer tous les maillages en un seul
        mesh = obj_mesh.dump(concatenate=True)
        # Extraire les vertices du Mesh pour PyVista
        mesh_polydata = pv.wrap(mesh.vertices.view(np.ndarray))
    else:
        # Si obj_mesh est déjà un Mesh, procéder directement
        mesh_polydata = pv.wrap(obj_mesh.vertices.view(np.ndarray))

    cloud = pv.PolyData(point_cloud)
    
    grid_x, grid_y, grid_z = np.mgrid[
        bounds[0]:bounds[1]:complex(grid_sizes[0]),
        bounds[2]:bounds[3]:complex(grid_sizes[1]),
        bounds[4]:bounds[5]:complex(grid_sizes[2])
    ]
    grid_points = np.vstack([grid_x.ravel(), grid_y.ravel(), grid_z.ravel()]).T
    grid = pv.PolyData(grid_points)
    
    plotter = pv.Plotter()
    plotter.add_mesh(mesh_polydata, color='lightblue', label='OBJ Mesh')
    plotter.add_mesh(cloud, color='red', point_size=5, label='E57 Cloud')
    plotter.add_points(grid, point_size=2, color='green', label='Segmentation Grid')
    plotter.add_legend()
    plotter.show()

def load_e57_point_cloud(e57_file):
    with pye57.E57(e57_file) as e57:
        data = e57.read_scan(0)
        x = np.array(data["cartesianX"])
        y = np.array(data["cartesianY"])
        z = np.array(data["cartesianZ"])
        points = np.vstack((x, y, z)).T
    return points

def segment_mesh(mesh, divisions, output_folder):
    bounds = mesh.bounds
    division_points = [np.linspace(start, end, num=div+1) for start, end, div in zip(bounds[0], bounds[1], divisions)]
    
    for i in range(divisions[0]):
        for j in range(divisions[1]):
            for k in range(divisions[2]):
                min_corner = [division_points[0][i], division_points[1][j], division_points[2][k]]
                max_corner = [division_points[0][i+1], division_points[1][j+1], division_points[2][k+1]]
                center = [(min_corner[0] + max_corner[0]) / 2, (min_corner[1] + max_corner[1]) / 2, (min_corner[2] + max_corner[2]) / 2]
                extents = [max_corner[0] - min_corner[0], max_corner[1] - min_corner[1], max_corner[2] - min_corner[2]]                
                box = trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(center))
                
                try:
                    result = trimesh.boolean.intersection([mesh, box], engine='blender')
                    if isinstance(result, trimesh.Scene):
                        combined_mesh = result.dump(concatenate=True)
                        if not combined_mesh.is_empty:
                            fragment_path = os.path.join(output_folder, f'fragment_{i}_{j}_{k}.obj')
                            combined_mesh.export(fragment_path)
                    elif isinstance(result, trimesh.Trimesh) and not result.is_empty:
                        fragment_path = os.path.join(output_folder, f'fragment_{i}_{j}_{k}.obj')
                        result.export(fragment_path)
                except Exception as e:
                    print(f"Error during intersection: {e}")

def segment_point_cloud(input_file, divisions, output_folder):
    with pye57.E57(input_file) as e57_file:
        scan_count = e57_file.scan_count
        for scan_index in range(scan_count):
            data = e57_file.read_scan(scan_index, ignore_missing_fields=True)
            cartesian_x = data['cartesianX']
            cartesian_y = data['cartesianY']
            cartesian_z = data['cartesianZ']
            min_x, max_x = np.min(cartesian_x), np.max(cartesian_x)
            min_y, max_y = np.min(cartesian_y), np.max(cartesian_y)
            min_z, max_z = np.min(cartesian_z), np.max(cartesian_z)
            section_size_x = (max_x - min_x) / divisions[0]
            section_size_y = (max_y - min_y) / divisions[1]
            section_size_z = (max_z - min_z) / divisions[2]

            for x in range(divisions[0]):
                for y in range(divisions[1]):
                    for z in range(divisions[2]):
                        section_min_x = min_x + x * section_size_x
                        section_max_x = min_x + (x + 1) * section_size_x
                        section_min_y = min_y + y * section_size_y
                        section_max_y = min_y + (y + 1) * section_size_y
                        section_min_z = min_z + z * section_size_z
                        section_max_z = min_z + (z + 1) * section_size_z

                        section_points = [ [cartesian_x[i], cartesian_y[i], cartesian_z[i]] 
                                           for i in range(len(cartesian_x)) 
                                           if section_min_x <= cartesian_x[i] <= section_max_x 
                                           and section_min_y <= cartesian_y[i] <= section_max_y 
                                           and section_min_z <= cartesian_z[i] <= section_max_z ]

                        if section_points:
                            scan_fields = {
                                'cartesianX': np.array([point[0] for point in section_points]),
                                'cartesianY': np.array([point[1] for point in section_points]),
                                'cartesianZ': np.array([point[2] for point in section_points]),
                            }
                            section_output_file = f"{output_folder}/section_{scan_index}_{x}_{y}_{z}.e57"
                            with pye57.E57(section_output_file, mode='w') as section_e57_file:
                                section_e57_file.write_scan_raw(scan_fields)

@click.command()
@click.option('--obj_file', type=click.Path(exists=True), help='Path to the OBJ file.')
@click.option('--e57_file', type=click.Path(exists=True), help='Path to the E57 file.')
@click.option('--output_directory', type=click.Path(), required=True, help='Directory to save the output sections.')
@click.option('--grid_size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def main(obj_file, e57_file, output_directory, grid_size):
    grid_sizes = tuple(map(int, grid_size.split('x')))
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    bounds = None
    mesh = None
    if obj_file:
        mesh = trimesh.load_mesh(obj_file)
        bounds_obj = np.array(mesh.bounds).flatten()
        if bounds is None:
            bounds = bounds_obj
        else:
            # Combine OBJ and E57 bounds if both files are provided
            bounds = np.vstack([bounds, bounds_obj]).min(axis=0), np.vstack([bounds, bounds_obj]).max(axis=0)

    point_cloud = None
    if e57_file:
        point_cloud = load_e57_point_cloud(e57_file)
        bounds_e57 = np.vstack([point_cloud.min(axis=0), point_cloud.max(axis=0)]).flatten()
        if bounds is None:
            bounds = bounds_e57
        else:
            # Update bounds to include both OBJ and E57 if both are provided
            bounds = np.minimum(bounds[:3], bounds_e57[:3]), np.maximum(bounds[3:], bounds_e57[3:])
            
    if mesh is not None or point_cloud is not None:
        # Visualize OBJ and E57 with the segmentation grid if either is provided
        visualize_with_grid(mesh, point_cloud, grid_sizes, np.hstack(bounds))

if __name__ == '__main__':
    main()