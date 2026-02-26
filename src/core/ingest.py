import fitz  # PyMuPDF
import docx
import io
import numpy as np
from PIL import Image
from fastapi import UploadFile
from rapidocr_onnxruntime import RapidOCR
# 引入线程池
from concurrent.futures import ThreadPoolExecutor, as_completed

# 初始化 OCR 引擎 (标准 CPU 模式)
ocr_engine = RapidOCR()


def parse_file(file: UploadFile) -> str:
    filename = file.filename.lower()
    file.file.seek(0)
    content = file.file.read()

    try:
        if filename.endswith((".png", ".jpg", ".jpeg")):
            return _read_image(content)
        elif filename.endswith(".pdf"):
            return _read_pdf(content)
        elif filename.endswith(".docx"):
            return _read_docx(content)
        elif filename.endswith((".txt", ".md")):
            return str(content, encoding="utf-8")
        else:
            return "ERROR: 不支持的文件格式。"
    except Exception as e:
        return f"ERROR: 文件解析底层错误 - {str(e)}"


def _read_image(file_bytes) -> str:
    """
    单张图片处理
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(image)
        result, _ = ocr_engine(img_array)
        if not result:
            return ""
        return "\n".join([line[1] for line in result])
    except Exception as e:
        return f"OCR 识别失败: {str(e)}"


# --- 并行处理工作函数 ---
def _process_page_task(page_num, img_data):
    """
    子线程函数：处理单页 OCR
    """
    try:
        # 在子线程中重新转换图片
        image = Image.open(io.BytesIO(img_data))
        img_array = np.array(image)

        # 运行 OCR
        result, _ = ocr_engine(img_array)

        if not result:
            text = ""
        else:
            text = "\n".join([line[1] for line in result])

        return page_num, f"\n[Page {page_num + 1} OCR Result]\n{text}\n"
    except Exception as e:
        return page_num, f"[Error Page {page_num}]"


def _read_pdf(file_bytes) -> str:
    """
    🚀 CPU 多线程加速版 PDF 读取
    """
    text_content = []
    MAX_PAGES = 8  # 截断策略：只看前5后3

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)

        # 1. 确定处理范围
        if total_pages <= MAX_PAGES:
            pages_to_process = range(total_pages)
        else:
            # 前5页 + 后3页
            pages_to_process = list(range(5)) + list(range(total_pages - 3, total_pages))
            print(f"⚠️ PDF 过大 ({total_pages}页)，启动多线程处理关键页面...")

        results = {}
        ocr_futures = []

        # 2. 启动线程池 (利用多核 CPU)
        # max_workers=4 比较稳妥，不影响电脑做别的事
        with ThreadPoolExecutor(max_workers=4) as executor:
            for page_num in pages_to_process:
                page = doc[page_num]

                # 尝试提取文本
                text = page.get_text(sort=True)

                # 如果是清晰文本页，直接用
                if len(text.strip()) > 50:
                    results[page_num] = text
                else:
                    # 如果是扫描页，提交给线程池
                    # print(f"🚀 [线程提交] OCR 第 {page_num + 1} 页")

                    # 降低 DPI 到 150 (速度快，精度够用)
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")

                    ocr_futures.append(executor.submit(_process_page_task, page_num, img_data))

            # 3. 收集结果
            for future in as_completed(ocr_futures):
                p_num, p_text = future.result()
                results[p_num] = p_text

        # 4. 拼装
        final_text = []
        for p in sorted(pages_to_process):
            final_text.append(results.get(p, ""))

        if total_pages > MAX_PAGES:
            final_text.insert(5, "\n...[中间页面已省略]...\n")

        return "\n".join(final_text)

    except Exception as e:
        return f"PDF 解析异常: {str(e)}"


def _read_docx(file_bytes) -> str:
    try:
        file_stream = io.BytesIO(file_bytes)
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Word 解析失败: {str(e)}"