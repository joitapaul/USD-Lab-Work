import exifread
import os
import shutil
import json

def get_gps(tags):
    def convert_to_degrees(value):
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)

    try:
        lat_value = tags.get('GPS GPSLatitude')
        lat_ref = tags.get('GPS GPSLatitudeRef')
        lon_value = tags.get('GPS GPSLongitude')
        lon_ref = tags.get('GPS GPSLongitudeRef')

        if not lat_value or not lat_ref or not lon_value or not lon_ref:
            return None

        lat = convert_to_degrees(lat_value)
        if lat_ref.values[0] != 'N':
            lat = -lat

        lon = convert_to_degrees(lon_value)
        if lon_ref.values[0] != 'E':
            lon = -lon
        return lat, lon
    except:
        return None

def is_inside_adamas(lat, lon):
    # Adamas University area center based on common coordinates in the dataset
    adamas_lat, adamas_lon = 22.738, 88.457
    threshold = 0.01 # Approx 1km box
    if abs(lat - adamas_lat) < threshold and abs(lon - adamas_lon) < threshold:
        return "Inside_Adamas"
    return "Outside_Adamas"

def segment():
    source_dir = '.'
    target_dir = 'Segmented_Data'
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)

    for filename in os.listdir(source_dir):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        
        filepath = os.path.join(source_dir, filename)
        
        # Extract user name from filename
        # Format: ..._User Name.jpg
        user_name = "Unknown_User"
        name_part = os.path.splitext(filename)[0]
        if '_' in name_part:
            user_name = name_part.split('_')[-1].strip()

        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f)
            
            # Brand
            brand = str(tags.get('Image Make', 'Unknown_Brand')).strip()
            model = str(tags.get('Image Model', 'Unknown_Model')).strip()
            full_brand = f"{brand}_{model}" if brand != "Unknown_Brand" else "Unknown_Brand"
            
            # GPS
            gps = get_gps(tags)
            location_tag = "No_GPS_Data"
            if gps:
                location_tag = is_inside_adamas(gps[0], gps[1])
            
            # Segmentation 1: By Brand and User
            brand_path = os.path.join(target_dir, 'By_Brand', full_brand, user_name)
            os.makedirs(brand_path, exist_ok=True)
            shutil.copy2(filepath, os.path.join(brand_path, filename))
            
            # Segmentation 2: By Location (Inside/Outside)
            loc_path = os.path.join(target_dir, 'By_Location_Status', location_tag, user_name)
            os.makedirs(loc_path, exist_ok=True)
            shutil.copy2(filepath, os.path.join(loc_path, filename))

            # Segmentation 3: By Latitude Longitude
            if gps:
                coord_tag = f"{round(gps[0], 4)}_{round(gps[1], 4)}"
                coord_path = os.path.join(target_dir, 'By_Coordinates', coord_tag, user_name)
                os.makedirs(coord_path, exist_ok=True)
                shutil.copy2(filepath, os.path.join(coord_path, filename))
            else:
                none_coord_path = os.path.join(target_dir, 'By_Coordinates', 'No_GPS', user_name)
                os.makedirs(none_coord_path, exist_ok=True)
                shutil.copy2(filepath, os.path.join(none_coord_path, filename))

            # Segmentation 4: By Device Category (Android, apple, no_metadata)
            if brand == "Unknown_Brand":
                device_cat = "no_metadata"
            elif brand.lower() == "apple":
                device_cat = "apple"
            else:
                device_cat = "Android"
            
            device_cat_path = os.path.join(target_dir, 'By_Device_Category', device_cat, user_name)
            os.makedirs(device_cat_path, exist_ok=True)
            shutil.copy2(filepath, os.path.join(device_cat_path, filename))

    print(f"Segmentation complete. Check the '{target_dir}' folder.")

if __name__ == "__main__":
    segment()