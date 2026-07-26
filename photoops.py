"""
PhotoOPS - Automated Photo Separation and Deskewing Tool
"""
import cv2
import os
import argparse
import numpy as np

def photo_ops_process(image_path, output_dir="separated_photos"):
    print(f"Starting PhotoOPS on: {image_path}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Load the original color image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image '{image_path}'")
        return

    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Edge detection using Canny
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate edges to close small gaps in the contours
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # 4. Find external contours
    contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Extract base filename without extension (e.g., 'mifoto.jpg' -> 'mifoto')
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    count = 1
    
    # Minimum area to be considered a photo (Adjust based on your scanner's DPI)
    min_area = 50000 

    for c in contours:
        area = cv2.contourArea(c)
        if area > min_area:
            # 5. Get the rotated bounding rectangle
            rect = cv2.minAreaRect(c)
            center, size, angle = rect
            width, height = int(size[0]), int(size[1])

            # 6. Normalize the angle to avoid stretching the image
            if angle < -45:
                angle += 90
                width, height = height, width
            elif angle > 45:
                angle -= 90
                width, height = height, width

            # 7. Create a rotation matrix around the center of the detected photo
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            # 8. Rotate the entire original image
            rotated_img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC)

            # 9. Crop the straightened photo from the rotated image
            cropped_photo = cv2.getRectSubPix(rotated_img, (width, height), center)

            # Save the deskewed and cropped photo sequentially
            output_filename = f"{base_name}-{count}.jpg"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, cropped_photo)
            
            print(f"Saved: {output_path} | Size: {width}x{height} px | Angle corrected: {angle:.2f}°")
            count += 1

    print(f"PhotoOPS process finished. Found and deskewed {count - 1} photos.")

if __name__ == "__main__":
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(description="PhotoOPS - Automated Photo Separation and Deskewing Tool")
    parser.add_argument("image_path", help="Path to the scanned image file (e.g., mifoto.jpg)")
    parser.add_argument("-o", "--output", default="separated_photos", help="Output directory (default: separated_photos)")
    
    args = parser.parse_args()
    
    # Execution
    photo_ops_process(args.image_path, args.output)