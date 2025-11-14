import fitz
import base64
from typing import List, Optional, Dict, Any
from sayou.document.interfaces.base_parser import BaseDocumentParser
from sayou.document.models import (
    Document, ImageElement, Page, TextElement, BoundingBox, 
    ElementMetadata, BaseElement
)

class PdfParser(BaseDocumentParser):
    """
    (Tier 2) fitz를 사용하여 PDF를 파싱하고, 'Document Model'을 반환합니다.
    """
    component_name = "PdfParser"
    SUPPORTED_TYPES = [".pdf"]

    def _parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        # 1. PDF 로드
        doc = self._load_document(file_bytes)
        pages_list = []

        # 2. 페이지 순회
        for page_num in range(doc.page_count):
            page_obj = self._process_page(doc, page_num, file_name)
            pages_list.append(page_obj)

        # 3. TOC(목차) 추출
        toc_list = []
        try:
            toc = doc.get_toc()
            for item in toc:
                level, title, page_num = item
                toc_list.append({"level": level, "title": title, "page_num": page_num})
        except Exception as e:
            self._log(f"Failed to extract TOC: {e}", level="warning")

        doc.close()

        # 4. 최종 Document 반환
        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="pdf",
            page_count=len(pages_list),
            pages=pages_list,
            toc=toc_list
        )

    def _load_document(self, file_bytes: bytes) -> fitz.Document:
        """fitz 문서 로드 및 에러 처리"""
        try:
            return fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"fitz failed to open PDF: {e}")

    def _process_page(self, doc: fitz.Document, page_num: int, file_name: str, **kwargs) -> Page:
        """단일 페이지 처리 로직 (스캔본 감지 추가)"""
        page = doc.load_page(page_num)
        elements_list = []
        page_text_dump = page.get_text()
        ocr_applied = False

        # 텍스트가 거의 없다면 (스캔본 의심)
        if not page_text_dump.strip() and self.ocr_engine:
            self._log(f"Page {page_num+1} seems to be scanned. Applying full-page OCR.")
            try:
                # 페이지를 고해상도 이미지로 렌더링
                pix = page.get_pixmap(dpi=kwargs.get("ocr_dpi", 200)) 
                img_bytes = pix.tobytes("png")
                ocr_text = self.ocr_engine.ocr_bytes(img_bytes, **kwargs)
                
                if ocr_text:
                    # 페이지 전체를 하나의 TextElement로 생성
                    full_page_bbox = BoundingBox(x0=0, y0=0, x1=page.rect.width, y1=page.rect.height)
                    elements_list.append(TextElement(
                        id=f"p{page_num+1}:full_ocr",
                        type="text",
                        bbox=full_page_bbox,
                        meta=ElementMetadata(page_num=page_num+1, id=f"p{page_num+1}:full_ocr"),
                        text=ocr_text
                    ))
                    page_text_dump = ocr_text
                    ocr_applied = True

            except Exception as e:
                self._log(f"Full-page OCR failed for page {page_num+1}: {e}", level="warning")

        if not ocr_applied:
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT, sort=True).get("blocks", [])
            for block in blocks:
                element = self._create_element_from_block(block, page_num, file_name, **kwargs)
                if element:
                    elements_list.append(element)

        return Page(
            page_num=page_num + 1,
            width=page.rect.width,
            height=page.rect.height,
            elements=elements_list,
            text=page_text_dump
        )

    def _create_element_from_block(self, block: Dict[str, Any], page_num: int, file_name: str, **kwargs) -> Optional[BaseElement]:
        """블록 딕셔너리를 Pydantic Element 객체로 변환"""
        b_type = block.get("type")
        bbox = block.get("bbox")
        
        pydantic_bbox = BoundingBox(
            x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]
        )
        
        meta = ElementMetadata(
            page_num=page_num + 1,
            id=f"p{page_num}:b{block.get('number', 0)}"
        )

        # Type 0: Text Block
        if b_type == 0:
            return self._process_text_block(block, pydantic_bbox, meta)

        # Type 1: Image Block
        elif b_type == 1:
            return self._process_image_block(block, pydantic_bbox, meta, **kwargs)

        return None

    def _process_text_block(self, block: Dict, bbox: BoundingBox, meta: ElementMetadata) -> Optional[TextElement]:
        """텍스트 블록 상세 처리"""
        block_text = ""
        # TODO: High-Fidelity (v0.1.0+) - 폰트/스타일 정보 추출
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "")
            block_text += " "
        
        block_text = block_text.strip()
        if not block_text: 
            return None

        return TextElement(
            id=meta.id,
            bbox=bbox,
            text=block_text,
            meta=meta
            # raw_attributes={"style": span.get("font")...} # v0.1.0
        )

    def _process_image_block(self, block: Dict, bbox: BoundingBox, meta: ElementMetadata, **kwargs) -> Optional[ImageElement]:
        """이미지 블록 처리: _process_image_data 헬퍼 사용"""
        try:
            image_bytes = block.get("image")
            if not image_bytes:
                return None
            ocr_enabled = kwargs.get("ocr_images", True) 

            return self._process_image_data(
                image_bytes=image_bytes,
                img_format=block.get("ext", "png"),
                elem_id=meta.id,
                page_num=meta.page_num,
                bbox=bbox,
                ocr_enabled=ocr_enabled
            )

        except Exception as e:
            self._log(f"Failed to process image block: {e}")
            return None