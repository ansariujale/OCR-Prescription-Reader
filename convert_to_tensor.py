import tensorflow as tf
import json
from object_detection.utils import dataset_util
import os
import re

def load_label_map(label_map_path):
    label_map={}

    #regular expression to extract id and name frmo the label map
    id_pattern = re.compile(r"id:\s*(\d+)")
    name_pattern = re.compile(r"name: \s*'(.+)'")

    with open (r'C:\Users\aujal\OneDrive\Desktop\python_OCR_application\dataset\label_map.pbtxt','r',encoding= 'utf-8') as f:
        content= f.read()
        ids= id_pattern.findall(content)
        names= name_pattern.findall(content)
        
        for id  , name in zip(ids, names):
            label_map[name]= int(id)
    return label_map

def create_tf_example(image_path,annotations, width,height,label_map):
    with tf.gfile.GFile(r"C:\Users\aujal\OneDrive\Desktop\python_OCR_application\dataset\prescription\images", 'rb') as fid:
        encoded_image_data = fid.read()

    image_format = b'jpeg' if image_path.lower().endswith('.jpeg')else b'jpg'

    # Extract bounding box and labels
    xmin=[]
    ymin=[]
    xmax=[]
    ymax=[]
    classes=[]
    
     # Loop through each annotation (bounding box and label) for the image
    for annotations in annotations:
        shape= annotations['shape_attributes']
        label= annotations['region_attributes'].get('name','unknown') #get the medicine name

        if shape ['name'] == 'rect':
            x_min= shape['x']/width
            y_min= shape['y']/height
            x_max= (shape['x']+shape['width'])/width
            y_max= (shape['y']+shape['height'])/height

            xmin.append(x_min)
            ymin.append(y_min)
            xmax.append(x_max)
            ymax.append(y_max)

            classes.append(label_map.get(label,0))

    features = {
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(os.path.basename(image_path).encode('utf8')),
        'image/source_id': dataset_util.bytes_feature(os.path.basename(image_path).encode('utf8')),
        'image/encoded': dataset_util.bytes_feature(encoded_image_data),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),
        'image/object/class/label': dataset_util.int64_list_feature(classes)
    }

    return tf.train.Example(features=tf.train.Features(feature=features))

json_file_path=r"C:\Users\aujal\OneDrive\Desktop\python_OCR_application\dataset\prescription\images\Prescription_dataset.json"
image_dir= r"C:\Users\aujal\OneDrive\Desktop\python_OCR_application\dataset\prescription\images"
label_map_path= r"C:\Users\aujal\OneDrive\Desktop\python_OCR_application\labelmap.py"
output_dir= r"C:\Users\aujal\OneDrive\Desktop\ocr prescription reader\OCR-Prescription-Reader\outputtrfrecord"

def main(json_file_path,image_dir,label_map_path,output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    writer = tf.io.TFRecordWriter(os.path.join(output_dir, 'data.tfrecord'))

    # Load label map from the .pbtxt file (maps medicine names to class IDs)
    label_map=load_label_map(label_map_path)
    
    #load json annotation data
    with open(json_file_path, 'r') as f:
        data= json.load(f)
    
    #Loop through the images in JSON file
    for key,value in data['via_img_metadata'].items():
        image_filename= value['filename']
        image_path=os.path.join(image_dir, image_filename) #full image path
        
        #get the list of annotations (bounding boxes)
        annotations= value['regions']

        #Try reading the image and getting its dimensions
        try:
            with tf.io.gfile.GFile(image_path,'rb') as fid:
                image_data= fid.read()
                image = tf.image.decode_image(image_data)
                height,width,_ =image.shape
        except Exception as e:
            print(f"Could not process image {image_filename}.Error: {str(e)}")
            continue

        #Create a tensorflow example for the image and its annotations

        tf_example = create_tf_example(image_path, annotations, width, height, label_map)
        writer.write(tf_example.SerializeToString())
    writer.close()

if __name__ == "__main__":
    import argparse
    parser= argparse.ArgumentParser(description="Convert JSON annotations to TFRecord.")
    parser.add_argument('--json_file', type=str, required=True, help= "Path to the JSON file containing annotations.")
    parser.add_argument('--image_dir', type=str, required=True, help= "DIrectory containing the images.")
    parser.add_argument('--label_map', type=str, required=True, help= "Path to the label map file (.pbtxt).")
    parser.add_argument('--output_dir', type=str, required=True, help= "Directory to save the output TFRecord file.")

    args= parser.parse_args()
    main(args.json_file, args.image_dir, args.label_map, args.output_dir )