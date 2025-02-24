import os
import json
from tabulate import tabulate

DEFAULT_PATHS = [
    "./basic/resource/red_line_tub",
    os.path.expanduser("~/mycar")
]

def get_tub_path():
    """Get tub path from user input with default options."""
    print("\nAvailable tub paths:")
    
    # List the default path
    print(f"1. {DEFAULT_PATHS[0]}")
    
    # List folders under ~/mycar/data
    mycar_data_path = os.path.join(DEFAULT_PATHS[1], "data")
    if os.path.exists(mycar_data_path):
        folders = [f for f in os.listdir(mycar_data_path) 
                  if os.path.isdir(os.path.join(mycar_data_path, f)) 
                  and os.path.exists(os.path.join(mycar_data_path, f, "images"))]
        for i, folder in enumerate(folders, 2):  # Start numbering from 2
            print(f"{i}. {os.path.join(mycar_data_path, folder)}")
    
    print("Or enter a custom path")
    
    while True:
        choice = input("\nSelect tub path (enter number or custom path, default is 1): ").strip()
        
        # Default to the first path if no input is given
        if choice == "":
            selected_path = DEFAULT_PATHS[0]
        # Check if input is a number corresponding to listed paths
        elif choice.isdigit() and 1 <= int(choice) <= len(folders) + 1:
            if int(choice) == 1:
                selected_path = DEFAULT_PATHS[0]
            else:
                selected_path = os.path.join(mycar_data_path, folders[int(choice) - 2])
        else:
            selected_path = os.path.expanduser(choice)  # Handle ~ in custom paths
            
        # Verify the path exists
        if os.path.exists(selected_path):
            return selected_path
        else:
            print(f"Error: Path {selected_path} does not exist. Please try again.")

def create_lap_table_data(laps, sort_by_duration=True, original_indices=None):
    """
    Create table data from lap results.
    Args:
        laps: List of lap dictionaries
        sort_by_duration: Whether to sort the table by duration
        original_indices: List of original lap numbers (optional)
    Returns:
        List of table rows, headers
    """
    table_data = []
    for i, lap in enumerate(laps):
        num_images = lap['end_frame'] - lap['start_frame'] + 1
        lap_num = original_indices[i] if original_indices else i + 1
        table_data.append([
            lap_num, 
            lap['start_frame'], 
            lap['end_frame'], 
            num_images, 
            f"{lap['duration']:.2f} seconds"
        ])
    
    if sort_by_duration:
        table_data.sort(key=lambda x: float(x[4].split()[0]))

    headers = ["Lap #", "Start Frame", "End Frame", "Number of Images", "Duration"]
    return table_data, headers

def load_lap_results(tub_path):
    """Load lap results from a tub directory."""
    lap_results_path = os.path.join(tub_path, 'lap_results.json')
    if not os.path.exists(lap_results_path):
        raise FileNotFoundError(f"{lap_results_path} does not exist. Please run generate_lap_result.py first.")
        
    with open(lap_results_path, 'r') as file:
        return json.load(file) 