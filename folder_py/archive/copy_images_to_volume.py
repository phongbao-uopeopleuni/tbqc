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
            logger.info(f"Scanning volume base: {volume_base}")
            for mount_dir in os.listdir(volume_base):
                mount_path = os.path.join(volume_base, mount_dir)
                logger.debug(f"Checking mount dir: {mount_path}")
                if os.path.isdir(mount_path):
                    for subdir in os.listdir(mount_path):
                        vol_path = os.path.join(mount_path, subdir)
                        logger.debug(f"Checking subdir: {vol_path}")
                        if os.path.isdir(vol_path) and 'vol_' in subdir:
                            # Đây là volume mount path thực tế
                            if os.access(vol_path, os.W_OK):
                                logger.info(f"Found Railway Volume mount path: {vol_path}")
                                return vol_path
                            else:
                                logger.warning(f"Volume path exists but not writable: {vol_path}")
        except Exception as e:
            logger.error(f"Error scanning volume mounts: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Fallback: kiểm tra env var
    env_volume_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if env_volume_path and os.path.exists(env_volume_path) and os.access(env_volume_path, os.W_OK):
        logger.info(f"Found volume path from env var: {env_volume_path}")
        return env_volume_path
    
    logger.warning("No Railway Volume found")
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
        for filename in source_files:
            source_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(volume_path, filename)
            
            if os.path.isfile(source_file):
                # Kiểm tra xem file đã tồn tại và có cùng size không
                if os.path.exists(dest_file):
                    try:
                        source_size = os.path.getsize(source_file)
                        dest_size = os.path.getsize(dest_file)
                        if source_size == dest_size:
                            logger.debug(f"Skipping {filename} (already exists, same size)")
                            skipped += 1
                            continue
                        else:
                            logger.info(f"Overwriting {filename} (size differs: {source_size} vs {dest_size})")
                    except Exception as e:
                        logger.debug(f"Could not check file size for {filename}: {e}")
                
                try:
                    shutil.copy2(source_file, dest_file)
                    file_size = os.path.getsize(dest_file)
                    logger.info(f"Copied {filename} ({file_size} bytes)")
                    copied += 1
                except Exception as e:
                    logger.error(f"Error copying {filename}: {e}")
                    errors += 1
            elif os.path.isdir(source_file):
                # Copy subdirectories (như activities/)
                dest_subdir = os.path.join(volume_path, filename)
                if os.path.exists(dest_subdir):
                    # Xóa và copy lại để đảm bảo đồng bộ
                    try:
                        shutil.rmtree(dest_subdir)
                        logger.debug(f"Removed existing directory {filename}/")
                    except Exception as e:
                        logger.warning(f"Could not remove {dest_subdir}: {e}")
                try:
                    shutil.copytree(source_file, dest_subdir)
                    logger.info(f"Copied directory {filename}/")
                    copied += 1
                except Exception as e:
                    logger.error(f"Error copying directory {filename}: {e}")
                    errors += 1
        
        logger.info(f"Copy completed: {copied} copied, {skipped} skipped, {errors} errors")
        
        # Verify: list một số files trong volume để confirm
        if os.path.exists(volume_path):
            try:
                vol_files = os.listdir(volume_path)
                logger.info(f"Volume now contains {len(vol_files)} items")
                if vol_files:
                    logger.info(f"Sample files in volume: {vol_files[:5]}")
            except Exception as e:
                logger.warning(f"Could not list volume contents: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error copying images: {e}")
        return False

if __name__ == '__main__':
    copy_images_to_volume()

