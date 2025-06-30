import pydicom
import pandas as pd
import numpy as np
import os
import sys
import matplotlib
matplotlib.use('Agg')  # Add this at the start of your script, before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from tqdm import tqdm

# TODO: should check the actual pixel spacing and image origin before plotting the images

def plot_dicom_with_annotations(dcm, seed_x, seed_y, bbox_x, bbox_y, bbox_w, bbox_h, output_path):
    """Plot and save DICOM slice with the seed point and bounding box."""
    img = dcm.pixel_array
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(img, cmap='gray', origin='lower')

    # Overlay the bounding box (green)
    rect = patches.Rectangle(
        (bbox_x, bbox_y), bbox_w, bbox_h, linewidth=2, edgecolor='green', facecolor='none', label="Bounding Box"
    )
    ax.add_patch(rect)

    # Overlay the seed point (red star)
    ax.scatter(seed_x, seed_y, color='red', marker='*', s=20, label='Seed Point')

    # Add legend and save image
    ax.legend()
    plt.title(f"Slice {dcm.InstanceNumber}")
    # plt.axis("off")
    full_output_path = os.path.join(output_path, f"Slice-{dcm.InstanceNumber}.png")
    plt.savefig(full_output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Successfully saved annotation to: {full_output_path}")

def extract_and_visualize_annotations(dcm, annotations_df, sop_uid, output_path):
    """Extract seed points and bounding boxes from CSV and overlay them on corresponding DICOM slices."""
    print(f"Processing annotation for UID: {sop_uid}")
    
    # Get the specific row for this DICOM
    row = annotations_df[annotations_df['Instance UID'] == sop_uid]
    # Convert normalized coordinates to pixels
    img_size = dcm.pixel_array.shape[0]  # Get actual image size from DICOM
    print(f"Image size: {img_size}")
    
    try:
        bbox_x = int(float(row["x"]) * img_size)
        bbox_y = int(float(row["y"]) * img_size)
        bbox_w = int(float(row["width"]) * img_size)
        bbox_h = int(float(row["height"]) * img_size)
        
        print(f"Bounding box coordinates: x={bbox_x}, y={bbox_y}, w={bbox_w}, h={bbox_h}")
        
        # Compute seed point at bounding box center
        seed_x = bbox_x + bbox_w // 2
        seed_y = bbox_y + bbox_h // 2
        print(f"Seed point coordinates: x={seed_x}, y={seed_y}")
        
        # Save plot
        plot_dicom_with_annotations(dcm, seed_x, seed_y, bbox_x, bbox_y, bbox_w, bbox_h, output_path)
        
    except KeyError as e:
        print(f"Missing required column in annotations: {e}")
        print("Available columns:", list(row.index))
    except Exception as e:
        print(f"Error processing annotation: {str(e)}")

def main(data_folder, annotations_file, output_folder):
    """Main function to process DICOM files and create annotated visualizations."""
    print(f"Starting processing with:")
    print(f"Data folder: {data_folder}")
    print(f"Annotations file: {annotations_file}")
    print(f"Output folder: {output_folder}")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Load annotations
    print("Loading annotations...")
    annotations = pd.read_csv(annotations_file)
    print(f"Loaded {len(annotations)} annotations")
    
    # Get list of subjects
    subjects = [d for d in os.listdir(data_folder) if d.startswith('sub-')]
    subjects.sort()
    print(f"Found {len(subjects)} subjects")
    
    # Process each subject
    for patient_folder in tqdm(subjects, desc="Processing patients"):
        print(f'\nProcessing patient: {patient_folder}')
        patient_path = os.path.join(data_folder, patient_folder)
        
        try:
            sessions = [d for d in os.listdir(patient_path) if 'ses-' in d]
            print(f"Found {len(sessions)} sessions for patient {patient_folder}")
            
            for session in sessions:
                session_folder = os.path.join(patient_path, session)
                series_folders = [f for f in os.listdir(session_folder) if 'ser-' in f]
                print(f"Found {len(series_folders)} series in session {session}")
                
                for series_folder in series_folders:
                    series_path = os.path.join(session_folder, series_folder)
                    output_path = os.path.join(output_folder, patient_folder, session, series_folder)
                    
                    if os.path.isdir(series_path) and 'ser-' in series_folder and 'None' not in series_folder:
                        dicom_files = [f for f in os.listdir(series_path) if f.endswith('.dcm')]
                        print(f"Found {len(dicom_files)} DICOM files in series {series_folder}")
                        
                        if dicom_files:
                            os.makedirs(output_path, exist_ok=True)
                            
                            for dicom_file in dicom_files:
                                try:
                                    dcm_path = os.path.join(series_path, dicom_file)
                                    print(f"Reading DICOM file: {dcm_path}")
                                    dcm = pydicom.dcmread(dcm_path)
                                    
                                    if dcm.SOPInstanceUID in annotations['Instance UID'].values:
                                        print(f"Found matching annotation for {dcm.SOPInstanceUID}")
                                        extract_and_visualize_annotations(dcm, annotations, dcm.SOPInstanceUID, output_path)
                                    else:
                                        print(f'No annotation found for {dcm.SOPInstanceUID}')
                                
                                except Exception as e:
                                    print(f"Error processing {dcm_path}: {str(e)}")
                                    continue
                                    
        except Exception as e:
            print(f"Error processing patient {patient_folder}: {str(e)}")
            continue

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_annotation_seed.py <dicom_root_folder> <csv_path> <output_folder>")
        sys.exit(1)
        
    dicom_root_folder = sys.argv[1]
    csv_path = sys.argv[2]
    output_folder = sys.argv[3]
    
    if not os.path.exists(dicom_root_folder):
        print(f"Error: DICOM root folder not found: {dicom_root_folder}")
        sys.exit(1)
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
        
    main(dicom_root_folder, csv_path, output_folder)
