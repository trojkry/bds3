import os
from werkzeug.utils import secure_filename
from flask import current_app, url_for

def handle_image_upload(product_id, file):
    ##Nahraje obrázek a vrátí jeho URL.
    if not file or not file.filename:
        return None

    original_filename = secure_filename(file.filename)
    filename = f"{product_id}_{original_filename}"
    upload_path = current_app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    return url_for('static', filename=f'uploads/products/{filename}')