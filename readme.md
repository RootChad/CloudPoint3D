# PointCloud and 3D model segmentation

## Installation Guide

Welcome to the Project Name installation guide. Follow these steps to set up your environment and get started.

### Prerequisites

Ensure you have Python installed on your system. This project requires:
- **Python version >=3.11 and <3.12**

### Setup Virtual Environment

It's recommended to use a virtual environment for project dependencies. To set up and activate your virtual environment, follow these steps:

1. If using a virtual environment (highly recommended), activate it with the following command:

   On Windows:
   ```
   .venv\Scripts\activate.bat
   ```

### Install Dependencies

Install all required packages using the command below. This will ensure you have all the necessary libraries to run the project.

```
pip install -r requirements.txt
```

### Update Dependencies

To update the list of requirements after installing new packages, use:

```
pip freeze -l > requirements.txt
```

### Running the Application

To start the CLI application, use the command:

```
python main.py
```

### Using the Application

For processing 3D mesh and point cloud data, use the following command with your data:

```
python main.py --obj_file "data/mymesh.obj" --e57_file "data/mycloud.e57" --output_directory "output_folder" --grid_size 5x5x5 --box_size 5x5x5
```

This command will process the `.obj` and `.e57` files located in the `data` directory, then output the results to the specified `output_folder`. The `grid_size` and `box_size` parameters allow for customization of the processing parameters.


## Code Explanation

This project includes a Python script that processes 3D mesh files (OBJ format) and point cloud data (E57 format) to perform segmentation based on a specified grid and box size. The script provides a CLI interface for easy use.

### Key Functions:

- `center_data`: Centers the mesh and point cloud data around their respective centers to simplify further processing.
- `calculate_grid_division_points`: Calculates the points at which the mesh and point cloud will be divided based on the specified grid and box size.
- `segment_based_on_grid`: Segments the mesh and point cloud into smaller sections based on the calculated division points. It outputs these segments into the specified directory.
- `main`: The main function that sets up the CLI, parses the input arguments, and initiates the processing flow.

### How to Use:

The script is designed to be run from the command line with options to specify the input OBJ and E57 files, output directory, grid size, and box size. For detailed usage instructions, refer to the "Running the Application" section of this README.


python main.py --obj_file "data/EAT_V01_OBJ.obj" --e57_file "data/ETA_20240223.e57" --output_directory "output_directory" --grid_size "2x2x2" --box_size "5x5x5" --heights "1.5,5"