import os
import json
from tabulate import tabulate

def list_available_tubs(base_path):
    tubs = []
    for folder in os.listdir(base_path):
        tub_path = os.path.join(base_path, folder)
        if os.path.isdir(tub_path) and os.path.exists(os.path.join(tub_path, 'lap_results.json')):
            tubs.append(tub_path)
    return tubs

def get_tub_path():
    print("\nAvailable tub paths:")
    
    # List the default path
    print(f"1. ./basic/resource/red_line_tub")
    
    # List folders under ~/mycar/data
    mycar_data_path = os.path.join(os.path.expanduser("~/mycar"), "data")
    if os.path.exists(mycar_data_path):
        folders = [f for f in os.listdir(mycar_data_path) if os.path.isdir(os.path.join(mycar_data_path, f)) and os.path.exists(os.path.join(mycar_data_path, f, "images"))]
        for i, folder in enumerate(folders, 2):  # Start numbering from 2
            print(f"{i}. {os.path.join(mycar_data_path, folder)}")
    
    print("Or enter a custom path")
    
    while True:
        choice = input("\nSelect tub path (enter number or custom path, default is 1): ").strip()
        
        # Default to the first path if no input is given
        if choice == "":
            selected_path = "./basic/resource/red_line_tub"
        # Check if input is a number corresponding to listed paths
        elif choice.isdigit() and 1 <= int(choice) <= len(folders) + 1:
            if int(choice) == 1:
                selected_path = "./basic/resource/red_line_tub"
            else:
                selected_path = os.path.join(mycar_data_path, folders[int(choice) - 2])  # Adjust index for folder selection
        else:
            selected_path = os.path.expanduser(choice)  # Handle ~ in custom paths
            
        # Verify the path exists
        if os.path.exists(selected_path):
            return selected_path
        else:
            print(f"Error: Path {selected_path} does not exist. Please try again.")

def delete_slow_lap_time(lap_results_path, manifest_path):
    # Check if lap_results.json exists
    if not os.path.exists(lap_results_path):
        print(f"{lap_results_path} does not exist. Please run generate_lap_result.py first.")
        return

    # Read lap results
    with open(lap_results_path, 'r') as file:
        lap_results = json.load(file)

    # List lap results to the user
    print("Lap Results (sorted in ascending order by duration):")
    table_data = []
    
    for i, lap in enumerate(lap_results['laps'], 1):
        num_images = lap['end_frame'] - lap['start_frame'] + 1  # Calculate number of images
        table_data.append([i, lap['start_frame'], lap['end_frame'], num_images, f"{lap['duration']:.2f} seconds"])
    
    # Sort the table data by duration (ascending)
    table_data.sort(key=lambda x: float(x[4].split()[0]))  # Sort by duration

    # Print the table of lap results
    headers = ["Lap #", "Start Frame", "End Frame", "Number of Images", "Duration"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="plain"))

    # Get the lap number from the user
    lap_number = int(input("Enter the lap number to use as the threshold; all laps with a duration equal to or longer than this lap will be deleted: ")) - 1

    # Validate the lap number
    if lap_number < 0 or lap_number >= len(lap_results['laps']):
        print("Invalid lap number. Please try again.")
        return

    # Get the duration of the selected lap
    slowest_lap_time = lap_results['laps'][lap_number]['duration']
    print(f"\nYou have selected Lap {lap_number + 1} with a duration of {slowest_lap_time:.2f} seconds.")
    print("Laps with a duration equal to or longer than this will be deleted.")

    # Identify deleted laps and their frame indices
    deleted_laps = []
    deleted_indexes = []
    
    for i, lap in enumerate(lap_results['laps']):
        if lap['duration'] >= slowest_lap_time:  # Change to '>=' to delete slower laps
            num_images = lap['end_frame'] - lap['start_frame'] + 1  # Calculate number of images
            deleted_laps.append([i + 1, lap['start_frame'], lap['end_frame'], num_images, f"{lap['duration']:.2f} seconds"])
            # Add all frame indices from start_frame to end_frame
            deleted_indexes.extend(range(lap['start_frame'], lap['end_frame'] + 1))

    # Calculate total images based on the maximum end frame
    num_images_to_delete = len(deleted_indexes)  # Total number of frames to delete

    # If no laps are to be deleted, inform the user and exit
    if num_images_to_delete == 0:
        print("No laps with a duration equal to or longer than the selected lap to delete.")
        return

    # Print the laps that will be deleted
    print("\nLaps to be deleted:")
    print(tabulate(deleted_laps, headers=["Lap #", "Start Frame", "End Frame", "Number of Images", "Duration"], tablefmt="plain"))

    # Prompt the user for confirmation
    print(f"\nYou are about to delete {num_images_to_delete} images out of {len(lap_results['laps'])} total images.")
    confirm = input("Are you sure you want to proceed with the deletion? (y/n, default is n): ").strip().lower() or 'n'

    if confirm != 'y':
        print("Deletion canceled.")
        return

    # Update the manifest file
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as file:
                for line in file:
                    manifest.append(json.loads(line))  # Read each line as a JSON object
        except json.JSONDecodeError as e:
            print(f"Error reading manifest file: {e}")
            return

    # Update the last JSON object in the manifest with deleted_indexes
    if manifest:
        manifest[-1]['deleted_indexes'] = deleted_indexes

    # Write the updated manifest back to the file
    with open(manifest_path, 'w') as file:
        for entry in manifest:
            json.dump(entry, file)
            file.write('\n')  # Write each JSON object on a new line

    print(f"\nSoft deleted lap times equal to or longer than {slowest_lap_time:.2f} seconds.")

def main():
    selected_tub = get_tub_path()  # Get the tub path from the user
    lap_results_path = os.path.join(selected_tub, 'lap_results.json')
    manifest_path = os.path.join(selected_tub, 'manifest.json')

    delete_slow_lap_time(lap_results_path, manifest_path)

if __name__ == "__main__":
    main()