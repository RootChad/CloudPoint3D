import click
import madcad as pmc
import numpy as np

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_directory', type=click.Path())
@click.option('--grid-size', default='5x5x5', help='Grid size for sectioning, format: x,y,z')
def section_obj(input_file, output_directory, grid_size):
    try:
        grid_sizes = tuple(map(int, grid_size.split('x')))
        
        # Load OBJ file
        mesh = pmc.read(input_file)
        
        # Determine bounding box of the object
        min_x, max_x = mesh.vertices[:, 0].min(), mesh.vertices[:, 0].max()
        min_y, max_y = mesh.vertices[:, 1].min(), mesh.vertices[:, 1].max()
        min_z, max_z = mesh.vertices[:, 2].min(), mesh.vertices[:, 2].max()
        
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
                    plane = pmc.Plane(normal=[1.0, 0.0, 0.0], point=[(section_min_x + section_max_x) / 2,
                                                                    (section_min_y + section_max_y) / 2,
                                                                    (section_min_z + section_max_z) / 2])
                    
                    # Cut mesh
                    cut_mesh = pmc.Boolean.intersection(mesh, plane)
                    
                    # Write sliced mesh to file
                    section_output_file = f"{output_directory}/section_{x}_{y}_{z}.obj"
                    cut_mesh.export(section_output_file)
                    
                    click.echo(f"Section {x}_{y}_{z} exported successfully.")

        click.echo("All sections exported successfully.")
        
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    section_obj()
