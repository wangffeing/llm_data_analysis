import logging
import os
import uuid
import magic
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from auth import verify_admin_permission

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"

# 创建线程池执行器
file_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="file_ops")

# 安全配置
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    '.csv': ['text/csv', 'application/csv', 'text/plain'],
    '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip'],
    '.xls': ['application/vnd.ms-excel'],
    '.json': ['application/json', 'text/json', 'text/plain'],
    '.txt': ['text/plain', 'text/csv']
}

async def is_safe_file_async(content: bytes, file_extension: str) -> bool:
    """异步验证文件内容是否安全"""
    try:
        # 检查文件大小
        if len(content) == 0:
            return False
        
        # 在线程池中执行MIME类型检查
        loop = asyncio.get_event_loop()
        try:
            mime_type = await loop.run_in_executor(
                file_executor, 
                lambda: magic.from_buffer(content, mime=True)
            )
            if mime_type not in ALLOWED_MIME_TYPES.get(file_extension, []):
                logger.warning(f"文件MIME类型不匹配: 期望{ALLOWED_MIME_TYPES.get(file_extension)}, 实际{mime_type}")
                return False
        except Exception as e:
            logger.warning(f"MIME类型检查失败: {e}")
            # 如果magic库不可用，进行基础内容检查
        
        # 检查文件头部是否包含恶意内容
        content_str = content[:1024].decode('utf-8', errors='ignore').lower()
        malicious_patterns = [
            '<script', 'jav1ascript:', 'vbscript:', 'onload=', 'onerror=',
            '<?php', '<%', '<meta', '<html', '<body'
        ]
        
        for pattern in malicious_patterns:
            if pattern in content_str:
                logger.warning(f"发现可疑内容模式: {pattern}")
                return False
        
        # 针对不同文件类型进行特定验证
        if file_extension in ['.csv', '.txt']:
            return await _validate_text_file_async(content)
        elif file_extension in ['.xlsx', '.xls']:
            return await _validate_excel_file_async(content)
        elif file_extension == '.json':
            return await _validate_json_file_async(content)
        
        return True
        
    except Exception as e:
        logger.error(f"文件安全检查失败: {e}")
        return False

async def _validate_text_file_async(content: bytes) -> bool:
    """异步验证文本文件"""
    def _sync_validate_text(content: bytes) -> bool:
        try:
            # 尝试解码为UTF-8
            text_content = content.decode('utf-8', errors='strict')
            # 检查是否包含过多的二进制字符
            non_printable_ratio = sum(1 for c in text_content if ord(c) < 32 and c not in '\t\n\r') / len(text_content)
            return non_printable_ratio < 0.1  # 非打印字符比例不超过10%
        except UnicodeDecodeError:
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(file_executor, _sync_validate_text, content)

async def _validate_excel_file_async(content: bytes) -> bool:
    """异步验证Excel文件"""
    def _sync_validate_excel(content: bytes) -> bool:
        try:
            # 简单检查Excel文件头
            excel_signatures = [
                b'\x50\x4B\x03\x04',  # XLSX (ZIP based)
                b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'  # XLS (OLE2 based)
            ]
            return any(content.startswith(sig) for sig in excel_signatures)
        except Exception:
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(file_executor, _sync_validate_excel, content)

async def _validate_json_file_async(content: bytes) -> bool:
    """异步验证JSON文件"""
    def _sync_validate_json(content: bytes) -> bool:
        try:
            import json
            json.loads(content.decode('utf-8'))
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(file_executor, _sync_validate_json, content)

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    import re
    # 移除路径遍历字符和其他危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除连续的点号（防止路径遍历）
    filename = re.sub(r'\.{2,}', '.', filename)
    # 限制长度
    return filename[:100]

async def _ensure_upload_dir_async() -> None:
    """异步确保上传目录存在"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        file_executor,
        lambda: os.makedirs(UPLOAD_DIR, exist_ok=True)
    )

async def _write_file_async(file_path: str, content: bytes) -> None:
    """异步写入文件"""
    def _sync_write_file(path: str, data: bytes) -> None:
        with open(path, "wb") as f:
            f.write(data)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(file_executor, _sync_write_file, file_path, content)

async def _verify_file_async(file_path: str, expected_size: int) -> bool:
    """异步验证保存的文件"""
    def _sync_verify_file(path: str, size: int) -> bool:
        return os.path.exists(path) and os.path.getsize(path) == size
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(file_executor, _sync_verify_file, file_path, expected_size)

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...)
):
    """异步安全的文件上传"""
    try:
        uploaded_files = []
        
        # 异步确保上传目录存在
        await _ensure_upload_dir_async()
        
        for file in files:
            # 验证文件名
            if not file.filename:
                raise HTTPException(status_code=400, detail="文件名不能为空")
            
            # 清理文件名
            safe_filename = sanitize_filename(file.filename)
            
            # 验证文件扩展名
            file_extension = os.path.splitext(safe_filename)[1].lower()
            # if file_extension not in ALLOWED_EXTENSIONS:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"不支持的文件类型: {file_extension}。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
            #     )
            
            # 读取文件内容
            content = await file.read()
            
            # 验证文件大小
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件过大: {len(content)} bytes。最大允许: {MAX_FILE_SIZE} bytes"
                )
            
            # 异步验证文件内容安全性
            # if not await is_safe_file_async(content, file_extension):
            #     raise HTTPException(status_code=400, detail="文件内容不安全或格式无效")
            
            # 生成安全的文件名
            file_id = str(uuid.uuid4())
            saved_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, saved_filename)
            
            # 异步保存文件
            await _write_file_async(file_path, content)
            
            # 异步验证保存的文件
            if not await _verify_file_async(file_path, len(content)):
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

async def _list_files_async() -> List[dict]:
    """异步列出文件"""
    def _sync_list_files() -> List[dict]:
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
        return files
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(file_executor, _sync_list_files)

@router.get("/files")
async def list_uploaded_files(_: bool = Depends(verify_admin_permission)):
    """异步列出已上传的文件（需要管理员权限）"""
    try:
        files = await _list_files_async()
        return {"files": files, "total_count": len(files)}
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文件列表失败")