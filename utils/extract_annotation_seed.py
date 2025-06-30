import pydicom
import pandas as pd
import numpy as np
import os
import sys
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from tqdm import tqdm

def plot_dicom_with_annotations(dcm, center_x, center_y, bbox_x, bbox_y, bbox_w, bbox_h, output_path):
    """Plot and save DICOM slice with the center point and bounding box."""
    img = dcm.pixel_array
    fig, ax = plt.subplots(figsize=(8, 8))
    # Use origin='upper' for standard top-left coordinate system
    ax.imshow(img, cmap='gray', origin='upper')

    # Overlay the bounding box (green)
    rect = patches.Rectangle(
        (bbox_x, bbox_y), bbox_w, bbox_h, linewidth=2, edgecolor='green', facecolor='none', label="Bounding Box"
    )
    ax.add_patch(rect)

    # Overlay the center point (red star)
    ax.scatter(center_x, center_y, color='red', marker='*', s=50, label='Center Point')

    ax.legend()
    plt.title(f"Instance: {dcm.SOPInstanceUID}\nSlice: {dcm.InstanceNumber}")
    full_output_path = os.path.join(output_path, f"Slice-{dcm.InstanceNumber}.png")
    plt.savefig(full_output_path, bbox_inches='tight', dpi=150)
    plt.close()
    # print(f"Successfully saved annotation to: {full_output_path}")

def extract_and_visualize_annotations(dcm, annotations_df, sop_uid, output_path):
    """
    Extracts annotations, visualizes them, and returns the updated DataFrame.
    """
    try:
        row = annotations_df.loc[sop_uid]
        
        # Get actual image height and width from DICOM
        img_height, img_width = dcm.pixel_array.shape
        
        # Convert normalized coordinates to pixel coordinates
        bbox_x = int(float(row["x"]) * img_width)
        bbox_y = int(float(row["y"]) * img_height)
        bbox_w = int(float(row["width"]) * img_width)
        bbox_h = int(float(row["height"]) * img_height)
        
        # Compute center point at bounding box center
        center_x = bbox_x + bbox_w // 2
        center_y = bbox_y + bbox_h // 2
        
        # Save plot
        plot_dicom_with_annotations(dcm, center_x, center_y, bbox_x, bbox_y, bbox_w, bbox_h, output_path)
        
        # Update DataFrame with DICOM path and center coordinates using .loc
        dcm_path = dcm.filename if hasattr(dcm, 'filename') else 'N/A'
        annotations_df.loc[sop_uid, ['dcm_path', 'center_x', 'center_y']] = [dcm_path, center_x, center_y]

    except KeyError:
        # This case is now handled by the initial check in main, but good to keep
        print(f"No annotation row found for UID: {sop_uid}")
    except Exception as e:
        print(f"Error processing annotation for {sop_uid}: {str(e)}")
    
    return annotations_df

def main(data_folder, annotations_file, output_folder):
    """Main function to process DICOM files and create annotated visualizations."""
    print(f"Starting processing...\nData folder: {data_folder}\nAnnotations file: {annotations_file}\nOutput folder: {output_folder}")
    
    os.makedirs(output_folder, exist_ok=True)
    
    print("Loading annotations...")
    annotations = pd.read_csv(annotations_file)
    print(f"Loaded {len(annotations)} annotations")

    # Pre-add new columns and set index for massive performance gain
    annotations['dcm_path'] = ''
    annotations['center_x'] = np.nan
    annotations['center_y'] = np.nan
    annotations.set_index('Instance UID', inplace=True)
    
    all_dicom_files = []
    for root, _, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.dcm'):
                all_dicom_files.append(os.path.join(root, file))

    print(f"Found {len(all_dicom_files)} total DICOM files.")

    for dcm_path in tqdm(all_dicom_files, desc="Processing DICOMs"):
        try:
            dcm = pydicom.dcmread(dcm_path, stop_before_pixels=False)
            sop_uid = dcm.SOPInstanceUID
            
            # Use fast index lookup
            if sop_uid in annotations.index:
                # Create a specific output path for this series to keep images organized
                relative_path = os.path.relpath(os.path.dirname(dcm_path), data_folder)
                output_path = os.path.join(output_folder, relative_path)
                os.makedirs(output_path, exist_ok=True)
                
                # IMPORTANT: Re-assign the DataFrame to capture updates
                annotations = extract_and_visualize_annotations(dcm, annotations, sop_uid, output_path)

        except Exception as e:
            print(f"Error reading or processing {dcm_path}: {str(e)}")
            continue
            
    # Reset index to turn 'Instance UID' back into a column before saving
    annotations.reset_index(inplace=True)
    
    # Save the updated DataFrame to a new CSV file
    updated_csv_path = os.path.join(output_folder, 'updated_annotations.csv')
    annotations.to_csv(updated_csv_path, index=False)
    print(f"\nProcessing complete. Updated annotations saved to: {updated_csv_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_annotation_seed.py <dicom_root_folder> <csv_path> <output_folder>")
        sys.exit(1)
        
    dicom_root_folder = sys.argv[1]
    csv_path = sys.argv[2]
    output_folder = sys.argv[3]
    
    if not os.path.isdir(dicom_root_folder):
        print(f"Error: DICOM root folder not found: {dicom_root_folder}")
        sys.exit(1)
    if not os.path.isfile(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
        
    main(dicom_root_folder, csv_path, output_folder)