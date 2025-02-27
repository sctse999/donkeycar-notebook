'''

refer to @08. Detect red line in a tub.ipynb and @functions_red_line.ipynb. 
 write a program to 
1. Loop all jpg images  ./basic/resource/red_line_tub/images in correct sequence.  The images are named nnn_cam_image_array_.jpg and they are captured by a car running in a racing track. 
2. Detect if there is a red line in the image.
3. If there is a red line in the image, it means the lap is start/end. We should start timing the  lap or end the last timing. 
4.After looping though all the images, list all laps and the time taken for each lap. In each lap, indicate the start and end index (inferred from the image name). To deduce the time, assume 20 images are taken per second. 


'''

try:
    import os
    import cv2
    import numpy as np
    from glob import glob
    import json
    from tabulate import tabulate
    from lap_utils import get_tub_path, create_lap_table_data
except ImportError as e:
    print("Error: Required packages are not installed.")
    print("Please install the required packages using pip:")
    print("pip install opencv-python numpy tabulate")
    exit(1)

# Global configuration
MASK_TOP_PERCENT = 0.75  # Mask top 75% of image
DEFAULT_THRESHOLD = 0.2  # Default threshold for red line detection
FRAMES_PER_SECOND = 20  # Images captured per second

# Add new global configuration
MIN_LAP_DURATION = 2.0  # Minimum seconds between red line detections

# Default tub paths
DEFAULT_PATHS = [
    "./basic/resource/red_line_tub",
    os.path.expanduser("~/mycar")
]

def calculate_mask(image):
    # Convert the image to HSV colorspace 
    image_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    # Calculate the 0-10 hue mask
    lower_red = np.array([0,100,100])
    upper_red = np.array([10,255,255])
    mask0 = cv2.inRange(image_hsv, lower_red, upper_red)

    # Calculate the 170-180 hue mask
    lower_red = np.array([170,100,100])
    upper_red = np.array([180,255,255])
    mask1 = cv2.inRange(image_hsv, lower_red, upper_red)

    # Combine masks
    mask = mask0 + mask1

    # Mask top portion according to configured percentage
    height, width = mask.shape
    mask = cv2.rectangle(mask, (0, 0), (width, int(height * MASK_TOP_PERCENT)), 0, -1)

    return mask

def calculate_red_pixel_percentage(image, mask):
    # For percentage calculation, only consider the unmasked portion of the image
    height, width, _ = image.shape
    roi_height = int(height * (1 - MASK_TOP_PERCENT))  # Consider only unmasked portion
    total_pixels = roi_height * width
    red_pixels = np.count_nonzero(mask)
    return red_pixels / total_pixels

def detect_red_line(image, threshold=DEFAULT_THRESHOLD):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mask = calculate_mask(image)
    red_percentage = calculate_red_pixel_percentage(image, mask)
    return red_percentage > threshold

def analyze_laps():
    tub_path = get_tub_path()
    
    # Construct images path
    images_path = os.path.join(tub_path, "images")
    
    # Check if images directory exists
    if not os.path.exists(images_path):
        print(f"Error: Images directory not found: {images_path}")
        return
    
    print(f"\nAnalyzing images in: {images_path}")
    
    # Get all jpg files and sort them by number
    image_files = glob(os.path.join(images_path, "*_cam_image_array_.jpg"))
    if not image_files:
        print(f"Error: No images found in {images_path}")
        return
        
    image_files.sort(key=lambda x: int(os.path.basename(x).split('_')[0]))
    
    print(f"Found {len(image_files)} images to process")
    
    laps = []
    current_lap_start = None
    last_red_line_frame = None
    
    # Process each image
    for img_path in image_files:
        frame_number = int(os.path.basename(img_path).split('_')[0])
        try:
            image = cv2.imread(img_path)
            if image is None:
                print(f"Warning: Could not read image: {img_path}")
                continue
                
            if detect_red_line(image):
                # Check if this is a new red line detection (not consecutive)
                if last_red_line_frame is None or \
                   (frame_number - last_red_line_frame) / FRAMES_PER_SECOND >= MIN_LAP_DURATION:
                    
                    if current_lap_start is None:
                        # Start new lap
                        current_lap_start = frame_number
                    else:
                        # End current lap
                        lap_info = {
                            'start_frame': current_lap_start,
                            'end_frame': frame_number,
                            'duration': (frame_number - current_lap_start) / FRAMES_PER_SECOND
                        }
                        laps.append(lap_info)
                        current_lap_start = frame_number  # Start new lap immediately
                
                last_red_line_frame = frame_number
                
        except Exception as e:
            print(f"Error processing image {img_path}: {str(e)}")
    
    # After processing all images and before printing results
    if not laps:
        print("No laps detected")
        return
    
    # Prepare results dictionary
    results = {
        'total_laps': len(laps),
        'laps': laps,
        'metadata': {
            'frames_per_second': FRAMES_PER_SECOND,
            'images_processed': len(image_files),
            'tub_path': tub_path
        }
    }
    
    # Save results to JSON file
    output_file = os.path.join(tub_path, 'lap_results.json')
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\nResults saved to {output_file}")
    except Exception as e:
        print(f"\nError saving results to file: {str(e)}")
    
    # Print results to console
    print(f"\nFound {len(laps)} complete laps:")
    
    # Use shared table creation function
    table_data, headers = create_lap_table_data(laps)
    print("\n" + tabulate(table_data, headers=headers, tablefmt="plain"))

if __name__ == "__main__":
    analyze_laps()