from PIL import Image
import os
from pathlib import Path

def resize_image(image_path, target_size=(300, 300)):
    """Resize image to target size while maintaining aspect ratio with white padding"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate aspect ratio
            aspect = img.width / img.height
            target_aspect = target_size[0] / target_size[1]
            
            if aspect > target_aspect:
                # Image is wider than target
                new_width = target_size[0]
                new_height = int(new_width / aspect)
            else:
                # Image is taller than target
                new_height = target_size[1]
                new_width = int(new_height * aspect)
            
            # Resize image maintaining aspect ratio
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create new white background image
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            
            # Paste resized image centered on white background
            x = (target_size[0] - new_width) // 2
            y = (target_size[1] - new_height) // 2
            new_img.paste(img, (x, y))
            
            # Save with original filename
            new_img.save(image_path, 'JPEG', quality=95)
            print(f"Resized {image_path}")
            return True
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return False

def process_directory(directory, target_size=(300, 300)):
    """Process all jpg images in directory"""
    directory = Path(directory)
    processed = 0
    failed = 0
    
    for file_path in directory.glob('*.jpg'):
        if resize_image(file_path, target_size):
            processed += 1
        else:
            failed += 1
    
    print(f"\nProcessing complete:")
    print(f"Successfully processed: {processed}")
    print(f"Failed: {failed}")

if __name__ == '__main__':
    image_dir = Path('static/images')
    # Standard size for all images (300x300 with aspect ratio preserved)
    process_directory(image_dir, (300, 300))