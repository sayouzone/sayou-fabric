from typing import List, Dict, Any
from ..interfaces.base_doc import BaseDocRefiner, ContentBlock
class DocToMarkdownRefiner(BaseDocRefiner):
    """
    (Tier 2) Document 'Dict'를 Markdown으로 변환하는 '엔진'.
    
    [T2 기본 성능]
    - 'raw_attributes' (style, placeholder)를 해석하여 시맨틱 MD(e.g., #, ##) 생성.
    - 메타데이터를 Frontmatter로 변환.
    - Text, Table, Image(OCR), Chart(Text Rep) 등 모든 요소를 처리.
    - 푸터 등 특정 요소를 '무시'하는 기본 규칙 포함.
    
    Tier 3는 이 클래스를 상속하여 _handle_text 등의 '규칙'을 오버라이드합니다.
    """
    component_name = "DocToMarkdownRefiner"
    
    def initialize(
        self, 
        include_headers: bool = True, # 헤더는 기본 포함
        include_footers: bool = False, # 푸터는 기본 무시
        **kwargs
    ):
        """
        T2 엔진의 기본 동작 규칙을 설정합니다.
        """
        super().initialize(**kwargs)
        self.include_headers = include_headers
        self.include_footers = include_footers

    # --- Tier 1 Template Method 구현 ---
    
    def refine(self, doc_data: Dict[str, Any]) -> List[ContentBlock]:
        """Document 딕셔너리를 순회하며 ContentBlock 생성"""
        blocks: List[ContentBlock] = []
        
        # 1. 메타데이터 처리 (T2 기본 기능)
        blocks.extend(self._handle_doc_metadata(doc_data))

        # 2. 페이지 순회
        for page in doc_data.get("pages", []):
            
            if self.include_headers and "header_elements" in page:
                for element in page.get("header_elements", []):
                    blocks.extend(self._handle_element(element, is_header=True, is_footer=False))
            
            for element in page.get("elements", []):
                blocks.extend(self._handle_element(element, is_header=False, is_footer=False))

            if self.include_footers and "footer_elements" in page:
                for element in page.get("footer_elements", []):
                    # T2의 기본 규칙: include_footers가 True여도 _handle_element에서 
                    # is_footer=True 플래그를 보고 무시할 수 있음 (T3가 오버라이드 가능)
                    blocks.extend(self._handle_element(element, is_header=False, is_footer=True))
        
        return blocks

    # --- Tier 2의 핵심 헬퍼 (T3가 오버라이드 가능) ---

    def _handle_element(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[ContentBlock]:
        """
        [T2 기본 규칙] 푸터는 기본적으로 무시합니다.
        T3는 이 메서드를 오버라이드하여 푸터를 다르게 처리할 수 있습니다.
        """
        if is_footer and not self.include_footers:
            return []

        elem_type = element.get("type")
        
        if elem_type == "text":
            return self._handle_text(element, is_header, is_footer)
        
        if elem_type == "table":
            return self._handle_table(element, is_header, is_footer)
        
        if elem_type == "image":
            return self._handle_image(element, is_header, is_footer)
            
        if elem_type == "chart":
            return self._handle_chart(element, is_header, is_footer)
            
        return []

    def _handle_doc_metadata(self, doc_data: Dict[str, Any]) -> List[ContentBlock]:
        """(T2 기본 성능) 메타데이터를 Frontmatter로 변환합니다."""
        md_frontmatter = "---\n"
        metadata = doc_data.get("metadata", {})
        
        title = metadata.get("title")
        author = metadata.get("author")

        if title:
            md_frontmatter += f"title: {title}\n"
        if author:
            md_frontmatter += f"author: {author}\n"
        md_frontmatter += "---\n\n"
        
        return [ContentBlock(
            type="md", 
            content=md_frontmatter, 
            metadata={"page_num": 0, "id": "metadata", "is_footer": False}
        )]

    def _handle_text(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[ContentBlock]:
        """
        (T2 기본 성능) 
        'raw_attributes'를 '해석'하여 Heading (1-9) 및 List를 생성합니다.
        """
        text = element.get("text", "").strip()
        if not text:
            return []

        raw_attrs = element.get("raw_attributes", {})
        semantic_type = raw_attrs.get("semantic_type")

        content = None

        # 1. '●' (List) 처리
        if semantic_type == "list":
            level = raw_attrs.get("list_level", 0)
            indent = "  " * level
            content = f"{indent}- {text}"

        # 2. 'Heading 1-9' (제목) 처리
        elif semantic_type == "heading":
            level = raw_attrs.get("heading_level", 1)
            hashes = "#" * level
            content = f"{hashes} {text}"
        
        # 3. PPT 플레이스홀더 (레거시 호환)
        elif raw_attrs.get("placeholder_type") == "TITLE":
            content = f"# {text}"
        
        # 4. 그 외 (기본 텍스트)
        else:
            content = text

        return [ContentBlock(
            type="md",
            content=content,
            metadata={
                "page_num": element.get("meta", {}).get("page_num"), 
                "id": element.get("id"), 
                "style": raw_attrs.get("style"),
                "is_footer": is_footer
            }
        )]

    def _handle_table(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[ContentBlock]:
        """(T2 기본 성능) 2D List를 MD 테이블로 변환합니다."""
        md_table = ""
        table_data = element.get("data", [])
        
        if not table_data or not table_data[0]:
            return []

        header = table_data[0]
        md_table += "| " + " | ".join(map(str, header)) + " |\n"
        md_table += "| " + " | ".join(["---"] * len(header)) + " |\n"
        
        for row in table_data[1:]:
            md_table += "| " + " | ".join(map(str, row)) + " |\n"
            
        return [ContentBlock(
            type="md",
            content=md_table,
            metadata={
                "page_num": element.get("meta", {}).get("page_num"), 
                "id": element.get("id"),
                "is_footer": is_footer
            }
        )]
        
    def _handle_image(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[ContentBlock]:
        """(T2 기본 성능)
            - 'image_base64' 데이터를 MD 태그로 변환하지 않고, type="image_base64" 블록으로 '분리'하여 반환합니다.
            - 최종 사용자(e.g., example, loader)가 이 블록을 받아 파일로 저장하고 MD 링크를 생성할 책임을 집니다.
        """
        image_base64 = element.get("image_base64")
        image_base64 = element.get("image_base64")
        if not image_base64:
            return []

        ocr_text = (element.get("ocr_text") or "").strip()
        if not ocr_text:
            alt_text = "image"
        else:
            alt_text = ocr_text
            
        img_format = element.get("image_format", "png")

        return [ContentBlock(
            type="image_base64",
            content=image_base64,
            metadata={
                "page_num": element.get("meta", {}).get("page_num"),
                "id": element.get("id"),
                "is_footer": is_footer,
                "alt_text": alt_text,
                "format": img_format
            }
        )]
        
    def _handle_chart(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[ContentBlock]:
        """(T2 기본 성능) 차트의 'text_representation'을 MD로 반환합니다."""
        text_rep = element.get("text_representation")
        if not text_rep:
            return []
        
        content = f"--- Chart Data ---\n{text_rep}\n--------------------\n"
        
        return [ContentBlock(
            type="md",
            content=content,
            metadata={
                "page_num": element.get("meta", {}).get("page_num"),
                "id": element.get("id"),
                "is_footer": is_footer
            }
        )]