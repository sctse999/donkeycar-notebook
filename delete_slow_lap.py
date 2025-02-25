import os
import json
from tabulate import tabulate
from lap_utils import get_tub_path, create_lap_table_data, load_lap_results

def delete_slow_lap_time(tub_path):
    try:
        lap_results = load_lap_results(tub_path)
    except FileNotFoundError as e:
        print(str(e))
        return

    # Get paths to related files
    meta_path = os.path.join(tub_path, 'meta.json')
    manifest_path = os.path.join(tub_path, 'manifest.json')

    # List lap results to the user
    print("Lap Results (sorted in ascending order by duration):")
    table_data, headers = create_lap_table_data(lap_results['laps'])
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
    deleted_lap_results = []
    deleted_indexes = []
    original_lap_numbers = []
    
    for i, lap in enumerate(lap_results['laps']):
        if lap['duration'] >= slowest_lap_time:
            deleted_lap_results.append(lap)
            deleted_indexes.extend(range(lap['start_frame'], lap['end_frame'] + 1))
            original_lap_numbers.append(i + 1)  # Store original lap number

    # Generate table for deleted laps
    deleted_table_data, headers = create_lap_table_data(
        deleted_lap_results, 
        sort_by_duration=False,
        original_indices=original_lap_numbers
    )
    
    # Print the laps that will be deleted
    print("\nLaps to be deleted:")
    print(tabulate(deleted_table_data, headers=headers, tablefmt="plain"))

    # Calculate total images based on the maximum end frame
    num_images_to_delete = len(deleted_indexes)  # Total number of frames to delete

    # If no laps are to be deleted, inform the user and exit
    if num_images_to_delete == 0:
        print("No laps with a duration equal to or longer than the selected lap to delete.")
        return

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

    # Remove UUID from meta.json
    try:
        with open(meta_path, 'r') as file:
            meta_data = json.load(file)
            if 'uuid' in meta_data:
                del meta_data['uuid']
        
        with open(meta_path, 'w') as file:
            json.dump(meta_data, file)
    except Exception as e:
        print(f"Warning: Could not update meta.json: {e}")

    print(f"\nSoft deleted lap times equal to or longer than {slowest_lap_time:.2f} seconds.")
    print("Removed UUID from meta.json for re-upload.")

def main():
    tub_path = get_tub_path()
    delete_slow_lap_time(tub_path)

if __name__ == "__main__":
    main()