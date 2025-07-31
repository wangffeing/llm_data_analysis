import logging
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """上传文件"""
    try:
        uploaded_files = []
        
        for file in files:
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            saved_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, saved_filename)
            
            # 保存文件
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
                        
            uploaded_files.append({
                "file_id": file_id,
                "original_name": file.filename,
                "saved_path": file_path,
                "saved_name": saved_filename,
                "file_type": file_extension
            })
        
        return {"uploaded_files": uploaded_files}
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail="文件上传失败")

@router.get("/files")
async def list_uploaded_files():
    """列出已上传的文件"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path)
                })
        return {"files": files}
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文件列表失败")