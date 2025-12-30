#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để copy ảnh từ local static/images vào Railway Volume
Chạy script này trên Railway để copy ảnh vào volume
"""

import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_railway_volume_path():
    """Tìm Railway Volume mount path thực tế"""
    # Railway Volume mount path thực tế từ logs
    volume_base = '/var/lib/containers/railwayapp/bind-mounts'
    if os.path.exists(volume_base):
        try:
            for mount_dir in os.listdir(volume_base):
                mount_path = os.path.join(volume_base, mount_dir)
                if os.path.isdir(mount_path):
                    for subdir in os.listdir(mount_path):
                        vol_path = os.path.join(mount_path, subdir)
                        if os.path.isdir(vol_path) and 'vol_' in subdir:
                            # Đây là volume mount path thực tế
                            if os.access(vol_path, os.W_OK):
                                logger.info(f"Found Railway Volume mount path: {vol_path}")
                                return vol_path
        except Exception as e:
            logger.error(f"Error scanning volume mounts: {e}")
    
    # Fallback: kiểm tra env var hoặc /app/static/images
    fallback_paths = [
        os.environ.get('RAILWAY_VOLUME_MOUNT_PATH'),
        '/app/static/images',
    ]
    
    for path in fallback_paths:
        if path and os.path.exists(path) and os.access(path, os.W_OK):
            logger.info(f"Found writable path (fallback): {path}")
            return path
    
    return None

def copy_images_to_volume():
    """Copy ảnh từ git static/images vào Railway Volume thực tế"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(BASE_DIR, 'static', 'images')
    
    if not os.path.exists(source_dir):
        logger.error(f"Source directory not found: {source_dir}")
        return False
    
    # Tìm volume thực tế từ bind-mounts (không phải mount point /app/static/images)
    volume_path = None
    volume_base = '/var/lib/containers/railwayapp/bind-mounts'
    if os.path.exists(volume_base):
        try:
            for mount_dir in os.listdir(volume_base):
                mount_path = os.path.join(volume_base, mount_dir)
                if os.path.isdir(mount_path):
                    for subdir in os.listdir(mount_path):
                        vol_path = os.path.join(mount_path, subdir)
                        if os.path.isdir(vol_path) and 'vol_' in subdir:
                            if os.access(vol_path, os.W_OK):
                                volume_path = vol_path
                                logger.info(f"Found Railway Volume: {volume_path}")
                                break
                    if volume_path:
                        break
        except Exception as e:
            logger.error(f"Error finding Railway Volume: {e}")
    
    if not volume_path:
        logger.warning("No Railway Volume found. Images will be served from git static/images")
        return False
    
    logger.info(f"Copying images from {source_dir} to {volume_path}")
    
    copied = 0
    skipped = 0
    errors = 0
    
    try:
        # Tạo thư mục nếu chưa có
        os.makedirs(volume_path, exist_ok=True)
        
        # Copy từng file
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(volume_path, filename)
            
            if os.path.isfile(source_file):
                if os.path.exists(dest_file):
                    logger.debug(f"Skipping {filename} (already exists)")
                    skipped += 1
                else:
                    try:
                        shutil.copy2(source_file, dest_file)
                        logger.info(f"Copied {filename}")
                        copied += 1
                    except Exception as e:
                        logger.error(f"Error copying {filename}: {e}")
                        errors += 1
            elif os.path.isdir(source_file):
                # Copy subdirectories (như activities/)
                dest_subdir = os.path.join(volume_path, filename)
                if not os.path.exists(dest_subdir):
                    shutil.copytree(source_file, dest_subdir)
                    logger.info(f"Copied directory {filename}/")
                    copied += 1
        
        logger.info(f"Copy completed: {copied} copied, {skipped} skipped, {errors} errors")
        return True
        
    except Exception as e:
        logger.error(f"Error copying images: {e}")
        return False

if __name__ == '__main__':
    copy_images_to_volume()

