import logging
import os
import uuid
import magic
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from auth import verify_admin_permission

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 安全配置
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    '.csv': ['text/csv', 'application/csv', 'text/plain'],
    '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    '.xls': ['application/vnd.ms-excel'],
    '.json': ['application/json', 'text/json', 'text/plain'],
    '.txt': ['text/plain', 'text/csv']
}

def is_safe_file(content: bytes, file_extension: str) -> bool:
    """验证文件内容是否安全"""
    try:
        # 检查文件大小
        if len(content) == 0:
            return False
        
        # 使用 python-magic 检查真实文件类型
        try:
            mime_type = magic.from_buffer(content, mime=True)
            if mime_type not in ALLOWED_MIME_TYPES.get(file_extension, []):
                logger.warning(f"文件MIME类型不匹配: 期望{ALLOWED_MIME_TYPES.get(file_extension)}, 实际{mime_type}")
                return False
        except Exception as e:
            logger.warning(f"MIME类型检查失败: {e}")
            # 如果magic库不可用，进行基础内容检查
        
        # 检查文件头部是否包含恶意内容
        content_str = content[:1024].decode('utf-8', errors='ignore').lower()
        malicious_patterns = [
            '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
            '<?php', '<%', '<meta', '<html', '<body'
        ]
        
        for pattern in malicious_patterns:
            if pattern in content_str:
                logger.warning(f"发现可疑内容模式: {pattern}")
                return False
        
        # 针对不同文件类型进行特定验证
        if file_extension in ['.csv', '.txt']:
            return _validate_text_file(content)
        elif file_extension in ['.xlsx', '.xls']:
            return _validate_excel_file(content)
        elif file_extension == '.json':
            return _validate_json_file(content)
        
        return True
        
    except Exception as e:
        logger.error(f"文件安全检查失败: {e}")
        return False

def _validate_text_file(content: bytes) -> bool:
    """验证文本文件"""
    try:
        # 尝试解码为UTF-8
        text_content = content.decode('utf-8', errors='strict')
        # 检查是否包含过多的二进制字符
        non_printable_ratio = sum(1 for c in text_content if ord(c) < 32 and c not in '\t\n\r') / len(text_content)
        return non_printable_ratio < 0.1  # 非打印字符比例不超过10%
    except UnicodeDecodeError:
        return False

def _validate_excel_file(content: bytes) -> bool:
    """验证Excel文件"""
    try:
        # 简单检查Excel文件头
        excel_signatures = [
            b'\x50\x4B\x03\x04',  # XLSX (ZIP based)
            b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'  # XLS (OLE2 based)
        ]
        return any(content.startswith(sig) for sig in excel_signatures)
    except Exception:
        return False

def _validate_json_file(content: bytes) -> bool:
    """验证JSON文件"""
    try:
        import json
        json.loads(content.decode('utf-8'))
        return True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    import re
    # 移除路径遍历字符和其他危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除连续的点号（防止路径遍历）
    filename = re.sub(r'\.{2,}', '.', filename)
    # 限制长度
    return filename[:100]

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...)
):
    """安全的文件上传"""
    try:
        uploaded_files = []
        
        for file in files:
            # 验证文件名
            if not file.filename:
                raise HTTPException(status_code=400, detail="文件名不能为空")
            
            # 清理文件名
            safe_filename = sanitize_filename(file.filename)
            
            # 验证文件扩展名
            file_extension = os.path.splitext(safe_filename)[1].lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"不支持的文件类型: {file_extension}。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
                )
            
            # 读取文件内容
            content = await file.read()
            
            # 验证文件大小
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件过大: {len(content)} bytes。最大允许: {MAX_FILE_SIZE} bytes"
                )
            
            # 验证文件内容安全性
            if not is_safe_file(content, file_extension):
                raise HTTPException(status_code=400, detail="文件内容不安全或格式无效")
            
            # 生成安全的文件名
            file_id = str(uuid.uuid4())
            saved_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, saved_filename)
            
            # 确保上传目录存在且安全
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 验证保存的文件
            if not os.path.exists(file_path) or os.path.getsize(file_path) != len(content):
                raise HTTPException(status_code=500, detail="文件保存失败")
                        
            uploaded_files.append({
                "file_id": file_id,
                "original_name": safe_filename,
                "saved_path": file_path,
                "saved_name": saved_filename,
                "file_type": file_extension,
                "file_size": len(content)
            })
            
            logger.info(f"文件上传成功: {safe_filename} -> {saved_filename}")
        
        return {"uploaded_files": uploaded_files, "total_count": len(uploaded_files)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail="文件上传处理失败")

@router.get("/files")
async def list_uploaded_files(_: bool = Depends(verify_admin_permission)):
    """列出已上传的文件（需要管理员权限）"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "modified_time": os.path.getmtime(file_path)
                })
        return {"files": files, "total_count": len(files)}
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文件列表失败")