
# Copyright (c) 2025, Sayouzone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

#domain infos
KIS_OPENAPI_PROD: str = "https://openapi.koreainvestment.com:9443" # 서비스
KIS_OPENAPI_OPS: str = "ws://ops.koreainvestment.com:21000" # 웹소켓
KIS_OPENAPI_VPS: str = "https://openapivts.koreainvestment.com:29443" # 모의투자 서비스
KIS_OPENAPI_VOPS: str = "ws://ops.koreainvestment.com:31000" # 모의투자 웹소켓

def decode_euc_kr(response):
    """깨진 한글 인코딩 복원"""
    
    # 인코딩 변환 (EUC-KR Bytes -> Python Unicode String)
    # response.text를 바로 쓰지 않고, content(바이트)를 직접 디코딩하는 것이 안전합니다.
    try:
        content = response.content.decode('euc-kr')
        return content
    except UnicodeDecodeError:
        # euc-kr로 안 될 경우 cp949 시도 (확장 완성형)
        content = response.content.decode('cp949', errors='replace')
    
    return content

def get_filename(headers):
    content_disposition = headers.get("Content-Disposition", "")
    # filename="..." 또는 filename*=UTF-8''... 패턴 찾기
    matches = re.findall("fileName=\"(.+)\"", content_disposition)
    if len(matches) == 0:
        return None
    
    encoded_filename = matches[0]
    filename = encoded_filename.encode('latin1').decode('utf-8')
    logger.debug('Content-Disposition', content_disposition)
    #logger.info('filename', unquote(filename))

    return unquote(filename)
