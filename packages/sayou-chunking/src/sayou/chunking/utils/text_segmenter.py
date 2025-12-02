import re
from typing import List


class TextSegmenter:
    @staticmethod
    def split_with_protection(
        text: str,
        separators: List[str],
        protected_patterns: List[str],
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        if not text:
            return []

        final_chunks = []

        if not protected_patterns:
            return TextSegmenter.recursive_split(
                text, separators, chunk_size, chunk_overlap
            )

        combined_pattern = f"({'|'.join(protected_patterns)})"
        parts = re.split(combined_pattern, text, flags=re.MULTILINE | re.DOTALL)

        for part in parts:
            if not part:
                continue

            is_protected = False
            for pat in protected_patterns:
                if re.fullmatch(pat, part, flags=re.MULTILINE | re.DOTALL):
                    is_protected = True
                    break

            if is_protected:
                final_chunks.append(part)
            else:
                sub_chunks = TextSegmenter.recursive_split(
                    part, separators, chunk_size, chunk_overlap
                )
                final_chunks.extend(sub_chunks)

        return final_chunks

    @staticmethod
    def recursive_split(
        text: str, separators: List[str], chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        final_chunks = []

        if not separators:
            return [text]

        separator = separators[0]
        next_separators = separators[1:]

        if separator == "":
            return list(text)

        try:
            splits = re.split(f"({separator})", text)
        except:
            splits = [text]

        current_doc = []
        total_len = 0

        for split in splits:
            if not split:
                continue
            if split == separator:
                if current_doc:
                    current_doc[-1] += split
                continue

            if total_len + len(split) > chunk_size:
                if current_doc:
                    final_chunks.append("".join(current_doc))
                    current_doc = []
                    total_len = 0

                if len(split) > chunk_size:
                    final_chunks.extend(
                        TextSegmenter.recursive_split(
                            split, next_separators, chunk_size, chunk_overlap
                        )
                    )
                else:
                    current_doc.append(split)
                    total_len += len(split)
            else:
                current_doc.append(split)
                total_len += len(split)

        if current_doc:
            final_chunks.append("".join(current_doc))

        return final_chunks
