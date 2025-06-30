# python script to convert the nlst_annotation.json provided by Sybil authors 
# (https://drive.google.com/file/d/19aa5yIHPWu3NtjqvXDc8NYB2Ub9V-4WM/view)
# in nlst_annotations.json for better usability
# giurdeluca, 11022025
import json
import pandas as pd

def convert_json_to_csv(json_path, csv_path):
    """
    Convert the lung nodule annotations JSON file to a CSV.

    Parameters:
    - json_path: Path to the input JSON file
    - csv_path: Path to save the output CSV file
    """
    with open(json_path, "r") as file:
        data = json.load(file)

    records = []
    
    for series_id, images in data.items():
        for image_id, bboxes in images.items():
            for bbox in bboxes:
                records.append([
                    series_id, image_id, 
                    bbox["x"], bbox["y"], 
                    bbox["width"], bbox["height"]
                ])
    
    df = pd.DataFrame(records, columns=["Series UID", "Instance UID", "x", "y", "width", "height"])
    
    df.to_csv(csv_path, index=False)
    print(f"CSV saved to {csv_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert NLST annotations JSON to CSV.")
    parser.add_argument("json_path", type=str, help="Path to the input JSON file")
    parser.add_argument("csv_path", type=str, help="Path to save the output CSV file")
    
    args = parser.parse_args()
    
    convert_json_to_csv(args.json_path, args.csv_path)
    print(f"Converted {args.json_path} to {args.csv_path}")

# Example usage:
# python convert_annotation_json_to_csv.py nlst_annotation.json nlst_annotations.csv
# This will create a CSV file with columns: Series UID, Instance UID, x, y, width, height
# where Series UID is the unique identifier for the series, Instance UID is the unique identifier for the image, and x, y, width, height are the coordinates and dimensions
# of the bounding boxes for the nodules.
# The CSV can then be used for further analysis or visualization.