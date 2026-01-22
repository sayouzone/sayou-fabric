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

import json
import pandas as pd

from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from .base_model import ResponseBody

"""
Koreainvestment (KIS) Data Models
"""

@dataclass
class DailyPriceParam:
    FID_COND_MRKT_DIV_CODE: str		# 조건 시장 분류 코드, J:KRX, NX:NXT, UN:통합
    FID_INPUT_ISCD: str				# 입력 종목코드, 종목코드 (ex 005930 삼성전자)

    FID_INPUT_DATE_1: Optional[str] = None			# 입력 날짜 1, 조회 시작일자
    FID_INPUT_DATE_2: Optional[str] = None			# 입력 날짜 2, 조회 종료일자 (최대 100개)
    FID_PERIOD_DIV_CODE: Optional[str] = None		# 기간분류코드, D:일봉 W:주봉, M:월봉, Y:년봉
    FID_ORG_ADJ_PRC: Optional[str] = None			# 수정주가 원주가 가격 여부, 0:수정주가 1:원주가

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class StockBasicInfo:
    """국내주식 개별 종목 정보 (output1)."""
    
    # API 응답에 포함될 수 있는 필드들
    # 현재 데이터에는 빈 배열이지만, 일반적인 국내주식 잔고 필드 구조
    prdy_vrss: str                        # 전일 대비
    prdy_vrss_sign: str                   # 전일 대비 부호
    prdy_ctrt: str                        # 전일 대비율
    stck_prdy_clpr: str                   # 주식 전일 종가
    acml_vol: str                         # 누적 거래량
    acml_tr_pbmn: str                     # 누적 거래 대금
    hts_kor_isnm: str                     # HTS 한글 종목명
    stck_prpr: str                        # 주식 현재가
    stck_shrn_iscd: str                   # 주식 단축 종목코드
    prdy_vol: str                         # 전일 거래량
    stck_mxpr: str                        # 주식 상한가
    stck_llam: str                        # 주식 하한가
    stck_oprc: str                        # 주식 시가2
    stck_hgpr: str                        # 주식 최고가
    stck_lwpr: str                        # 주식 최저가
    stck_prdy_oprc: str                   # 주식 전일 시가
    stck_prdy_hgpr: str                   # 주식 전일 최고가
    stck_prdy_lwpr: str                   # 주식 전일 최저가
    askp: str                             # 매도호가
    bidp: str                             # 매수호가
    prdy_vrss_vol: str                    # 전일 대비 거래량
    vol_tnrt: str                         # 거래량 회전율
    stck_fcam: str                        # 주식 액면가
    lstn_stcn: str                        # 상장 주수
    cpfn: str                             # 자본금
    hts_avls: str                         # HTS 시가총액
    per: str                              # PER
    eps: str                              # EPS
    pbr: str                              # PBR
    itewhol_loan_rmnd_ratem: str          # 전체 융자 잔고 비율

    FIELD_NAMES_KO = {
        "prdy_vrss": "전일 대비",
        "prdy_vrss_sign": "전일 대비 부호",
        "prdy_ctrt": "전일 대비율",
        "stck_prdy_clpr": "주식 전일 종가",
        "acml_vol": "누적 거래량",
        "acml_tr_pbmn": "누적 거래 대금",
        "hts_kor_isnm": "HTS 한글 종목명",
        "stck_prpr": "주식 현재가",
        "stck_shrn_iscd": "주식 단축 종목코드",
        "prdy_vol": "전일 거래량",
        "stck_mxpr": "주식 상한가",
        "stck_llam": "주식 하한가",
        "stck_oprc": "주식 시가2",
        "stck_hgpr": "주식 최고가",
        "stck_lwpr": "주식 최저가",
        "stck_prdy_oprc": "주식 전일 시가",
        "stck_prdy_hgpr": "주식 전일 최고가",
        "stck_prdy_lwpr": "주식 전일 최저가",
        "askp": "매도호가",
        "bidp": "매수호가",
        "prdy_vrss_vol": "전일 대비 거래량",
        "vol_tnrt": "거래량 회전율",
        "stck_fcam": "주식 액면가",
        "lstn_stcn": "상장 주수",
        "cpfn": "자본금",
        "hts_avls": "HTS 시가총액",
        "per": "PER",
        "eps": "EPS",
        "pbr": "PBR",
        "itewhol_loan_rmnd_ratem": "전체 융자 잔고 비율"
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StockBasicInfo":
        """딕셔너리에서 StockBasicInfo 객체 생성."""
        return cls(
            prdy_vrss=data.get("prdy_vrss", ""),
            prdy_vrss_sign=data.get("prdy_vrss_sign", ""),
            prdy_ctrt=data.get("prdy_ctrt", ""),
            stck_prdy_clpr=data.get("stck_prdy_clpr", ""),
            acml_vol=data.get("acml_vol", ""),
            acml_tr_pbmn=data.get("acml_tr_pbmn", ""),
            hts_kor_isnm=data.get("hts_kor_isnm", ""),
            stck_prpr=data.get("stck_prpr", ""),
            stck_shrn_iscd=data.get("stck_shrn_iscd", ""),
            prdy_vol=data.get("prdy_vol", ""),
            stck_mxpr=data.get("stck_mxpr", ""),
            stck_llam=data.get("stck_llam", ""),
            stck_oprc=data.get("stck_oprc", ""),
            stck_hgpr=data.get("stck_hgpr", ""),
            stck_lwpr=data.get("stck_lwpr", ""),
            stck_prdy_oprc=data.get("stck_prdy_oprc", ""),
            stck_prdy_hgpr=data.get("stck_prdy_hgpr", ""),
            stck_prdy_lwpr=data.get("stck_prdy_lwpr", ""),
            askp=data.get("askp", ""),
            bidp=data.get("bidp", ""),
            prdy_vrss_vol=data.get("prdy_vrss_vol", ""),
            vol_tnrt=data.get("vol_tnrt", ""),
            stck_fcam=data.get("stck_fcam", ""),
            lstn_stcn=data.get("lstn_stcn", ""),
            cpfn=data.get("cpfn", ""),
            hts_avls=data.get("hts_avls", ""),
            per=data.get("per", ""),
            eps=data.get("eps", ""),
            pbr=data.get("pbr", ""),
            itewhol_loan_rmnd_ratem=data.get("itewhol_loan_rmnd_ratem", "")
        )
    
    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(k, v):
            #print(k, v)
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            elif k in ["ft_ord_unpr3", "ft_ccld_unpr3", "ft_ccld_amt3"]:
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = float(v)
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(k, v)
            for k, v in self.__dict__.items()
            if v is not None
        }

@dataclass
class StockCurrentPrice:
    iscd_stat_cls_code: str        #종목 상태 구분 코드
    marg_rate: str                 #증거금 비율
    rprs_mrkt_kor_name: str        #대표 시장 한글 명
    new_hgpr_lwpr_cls_code: str    #신 고가 저가 구분 코드
    bstp_kor_isnm: str             #업종 한글 종목명
    temp_stop_yn: str              #임시 정지 여부
    oprc_rang_cont_yn: str         #시가 범위 연장 여부
    clpr_rang_cont_yn: str         #종가 범위 연장 여부
    crdt_able_yn: str              #신용 가능 여부
    grmn_rate_cls_code: str        #보증금 비율 구분 코드
    elw_pblc_yn: str               #ELW 발행 여부
    stck_prpr: str                 #주식 현재가
    prdy_vrss: str                 #전일 대비
    prdy_vrss_sign: str            #전일 대비 부호
    prdy_ctrt: str                 #전일 대비율
    acml_tr_pbmn: str              #누적 거래 대금
    acml_vol: str                  #누적 거래량
    prdy_vrss_vol_rate: str        #전일 대비 거래량 비율
    stck_oprc: str                 #주식 시가2
    stck_hgpr: str                 #주식 최고가
    stck_lwpr: str                 #주식 최저가
    stck_mxpr: str                 #주식 상한가
    stck_llam: str                 #주식 하한가
    stck_sdpr: str                 #주식 기준가
    wghn_avrg_stck_prc: str        #가중 평균 주식 가격
    hts_frgn_ehrt: str             #HTS 외국인 소진율
    frgn_ntby_qty: str             #외국인 순매수 수량
    pgtr_ntby_qty: str             #프로그램매매 순매수 수량
    pvt_scnd_dmrs_prc: str         #피벗 2차 디저항 가격
    pvt_frst_dmrs_prc: str         #피벗 1차 디저항 가격
    pvt_pont_val: str              #피벗 포인트 값
    pvt_frst_dmsp_prc: str         #피벗 1차 디지지 가격
    pvt_scnd_dmsp_prc: str         #피벗 2차 디지지 가격
    dmrs_val: str                  #디저항 값
    dmsp_val: str                  #디지지 값
    cpfn: str                      #자본금
    rstc_wdth_prc: str             #제한 폭 가격
    stck_fcam: str                 #주식 액면가
    stck_sspr: str                 #주식 대용가
    aspr_unit: str                 #호가단위
    hts_deal_qty_unit_val: str     #HTS 매매 수량 단위 값
    lstn_stcn: str                 #상장 주수
    hts_avls: str                  #HTS 시가총액
    per: str                       #PER
    pbr: str                       #PBR
    stac_month: str                #결산 월
    vol_tnrt: str                  #거래량 회전율
    eps: str                       #EPS
    bps: str                       #BPS
    d250_hgpr: str                 #250일 최고가
    d250_hgpr_date: str            #250일 최고가 일자
    d250_hgpr_vrss_prpr_rate: str  #250일 최고가 대비 현재가 비율
    d250_lwpr: str                 #250일 최저가
    d250_lwpr_date: str            #250일 최저가 일자
    d250_lwpr_vrss_prpr_rate: str  #250일 최저가 대비 현재가 비율
    stck_dryy_hgpr: str            #주식 연중 최고가
    dryy_hgpr_vrss_prpr_rate: str  #연중 최고가 대비 현재가 비율
    dryy_hgpr_date: str            #연중 최고가 일자
    stck_dryy_lwpr: str            #주식 연중 최저가
    dryy_lwpr_vrss_prpr_rate: str  #연중 최저가 대비 현재가 비율
    dryy_lwpr_date: str            #연중 최저가 일자
    w52_hgpr: str                  #52주일 최고가
    w52_hgpr_vrss_prpr_ctrt: str   #52주일 최고가 대비 현재가 대비
    w52_hgpr_date: str             #52주일 최고가 일자
    w52_lwpr: str                  #52주일 최저가
    w52_lwpr_vrss_prpr_ctrt: str   #52주일 최저가 대비 현재가 대비
    w52_lwpr_date: str             #52주일 최저가 일자
    whol_loan_rmnd_rate: str       #전체 융자 잔고 비율
    ssts_yn: str                   #공매도가능여부
    stck_shrn_iscd: str            #주식 단축 종목코드
    fcam_cnnm: str                 #액면가 통화명
    cpfn_cnnm: str                 #자본금 통화명
    apprch_rate: str               #접근도
    frgn_hldn_qty: str             #외국인 보유 수량
    vi_cls_code: str               #VI적용구분코드
    ovtm_vi_cls_code: str          #시간외단일가VI적용구분코드
    last_ssts_cntg_qty: str        #최종 공매도 체결 수량
    invt_caful_yn: str             #투자유의여부
    mrkt_warn_cls_code: str        #시장경고코드
    short_over_yn: str             #단기과열여부
    sltr_yn: str                   #정리매매여부
    mang_issu_cls_code: str        #관리종목여부

    FIELD_NAMES_KO = {
        "iscd_stat_cls_code": "종목 상태 구분 코드",
        "marg_rate": "증거금 비율",
        "rprs_mrkt_kor_name": "대표 시장 한글 명",
        "new_hgpr_lwpr_cls_code": "신 고가 저가 구분 코드",
        "bstp_kor_isnm": "업종 한글 종목명",
        "temp_stop_yn": "임시 정지 여부",
        "oprc_rang_cont_yn": "시가 범위 연장 여부",
        "clpr_rang_cont_yn": "종가 범위 연장 여부",
        "crdt_able_yn": "신용 가능 여부",
        "grmn_rate_cls_code": "보증금 비율 구분 코드",
        "elw_pblc_yn": "ELW 발행 여부",
        "stck_prpr": "주식 현재가",
        "prdy_vrss": "전일 대비",
        "prdy_vrss_sign": "전일 대비 부호",
        "prdy_ctrt": "전일 대비율",
        "acml_tr_pbmn": "누적 거래 대금",
        "acml_vol": "누적 거래량",
        "prdy_vrss_vol_rate": "전일 대비 거래량 비율",
        "stck_oprc": "주식 시가2",
        "stck_hgpr": "주식 최고가",
        "stck_lwpr": "주식 최저가",
        "stck_mxpr": "주식 상한가",
        "stck_llam": "주식 하한가",
        "stck_sdpr": "주식 기준가",
        "wghn_avrg_stck_prc": "가중 평균 주식 가격",
        "hts_frgn_ehrt": "HTS 외국인 소진율",
        "frgn_ntby_qty": "외국인 순매수 수량",
        "pgtr_ntby_qty": "프로그램매매 순매수 수량",
        "pvt_scnd_dmrs_prc": "피벗 2차 디저항 가격",
        "pvt_frst_dmrs_prc": "피벗 1차 디저항 가격",
        "pvt_pont_val": "피벗 포인트 값",
        "pvt_frst_dmsp_prc": "피벗 1차 디지지 가격",
        "pvt_scnd_dmsp_prc": "피벗 2차 디지지 가격",
        "dmrs_val": "디저항 값",
        "dmsp_val": "디지지 값",
        "cpfn": "자본금",
        "rstc_wdth_prc": "제한 폭 가격",
        "stck_fcam": "주식 액면가",
        "stck_sspr": "주식 대용가",
        "aspr_unit": "호가단위",
        "hts_deal_qty_unit_val": "HTS 매매 수량 단위 값",
        "lstn_stcn": "상장 주수",
        "hts_avls": "HTS 시가총액",
        "per": "PER",
        "pbr": "PBR",
        "stac_month": "결산 월",
        "vol_tnrt": "거래량 회전율",
        "eps": "EPS",
        "bps": "BPS",
        "d250_hgpr": "250일 최고가",
        "d250_hgpr_date": "250일 최고가 일자",
        "d250_hgpr_vrss_prpr_rate": "250일 최고가 대비 현재가 비율",
        "d250_lwpr": "250일 최저가",
        "d250_lwpr_date": "250일 최저가 일자",
        "d250_lwpr_vrss_prpr_rate": "250일 최저가 대비 현재가 비율",
        "stck_dryy_hgpr": "주식 연중 최고가",
        "dryy_hgpr_vrss_prpr_rate": "연중 최고가 대비 현재가 비율",
        "dryy_hgpr_date": "연중 최고가 일자",
        "stck_dryy_lwpr": "주식 연중 최저가",
        "dryy_lwpr_vrss_prpr_rate": "연중 최저가 대비 현재가 비율",
        "dryy_lwpr_date": "연중 최저가 일자",
        "w52_hgpr": "52주일 최고가",
        "w52_hgpr_vrss_prpr_ctrt": "52주일 최고가 대비 현재가 대비",
        "w52_hgpr_date": "52주일 최고가 일자",
        "w52_lwpr": "52주일 최저가",
        "w52_lwpr_vrss_prpr_ctrt": "52주일 최저가 대비 현재가 대비",
        "w52_lwpr_date": "52주일 최저가 일자",
        "whol_loan_rmnd_rate": "전체 융자 잔고 비율",
        "ssts_yn": "공매도가능여부",
        "stck_shrn_iscd": "주식 단축 종목코드",
        "fcam_cnnm": "액면가 통화명",
        "cpfn_cnnm": "자본금 통화명",
        "apprch_rate": "접근도",
        "frgn_hldn_qty": "외국인 보유 수량",
        "vi_cls_code": "VI적용구분코드",
        "ovtm_vi_cls_code": "시간외단일가VI적용구분코드",
        "last_ssts_cntg_qty": "최종 공매도 체결 수량",
        "invt_caful_yn": "투자유의여부",
        "mrkt_warn_cls_code": "시장경고코드",
        "short_over_yn": "단기과열여부",
        "sltr_yn": "정리매매여부",
        "mang_issu_cls_code": "관리종목여부",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StockCurrentPrice":
        """딕셔너리에서 StockCurrentPrice 객체 생성."""
        return cls(
            iscd_stat_cls_code=data.get("iscd_stat_cls_code", ""),
            marg_rate=data.get("marg_rate", ""),
            rprs_mrkt_kor_name=data.get("rprs_mrkt_kor_name", ""),
            new_hgpr_lwpr_cls_code=data.get("new_hgpr_lwpr_cls_code", ""),
            bstp_kor_isnm=data.get("bstp_kor_isnm", ""),
            temp_stop_yn=data.get("temp_stop_yn", ""),
            oprc_rang_cont_yn=data.get("oprc_rang_cont_yn", ""),
            clpr_rang_cont_yn=data.get("clpr_rang_cont_yn", ""),
            crdt_able_yn=data.get("crdt_able_yn", ""),
            grmn_rate_cls_code=data.get("grmn_rate_cls_code", ""),
            elw_pblc_yn=data.get("elw_pblc_yn", ""),
            stck_prpr=data.get("stck_prpr", ""),
            prdy_vrss=data.get("prdy_vrss", ""),
            prdy_vrss_sign=data.get("prdy_vrss_sign", ""),
            prdy_ctrt=data.get("prdy_ctrt", ""),
            acml_tr_pbmn=data.get("acml_tr_pbmn", ""),
            acml_vol=data.get("acml_vol", ""),
            prdy_vrss_vol_rate=data.get("prdy_vrss_vol_rate", ""),
            stck_oprc=data.get("stck_oprc", ""),
            stck_hgpr=data.get("stck_hgpr", ""),
            stck_lwpr=data.get("stck_lwpr", ""),
            stck_mxpr=data.get("stck_mxpr", ""),
            stck_llam=data.get("stck_llam", ""),
            stck_sdpr=data.get("stck_sdpr", ""),
            wghn_avrg_stck_prc=data.get("wghn_avrg_stck_prc", ""),
            hts_frgn_ehrt=data.get("hts_frgn_ehrt", ""),
            frgn_ntby_qty=data.get("frgn_ntby_qty", ""),
            pgtr_ntby_qty=data.get("pgtr_ntby_qty", ""),
            pvt_scnd_dmrs_prc=data.get("pvt_scnd_dmrs_prc", ""),
            pvt_frst_dmrs_prc=data.get("pvt_frst_dmrs_prc", ""),
            pvt_pont_val=data.get("pvt_pont_val", ""),
            pvt_frst_dmsp_prc=data.get("pvt_frst_dmsp_prc", ""),
            pvt_scnd_dmsp_prc=data.get("pvt_scnd_dmsp_prc", ""),
            dmrs_val=data.get("dmrs_val", ""),
            dmsp_val=data.get("dmsp_val", ""),
            cpfn=data.get("cpfn", ""),
            rstc_wdth_prc=data.get("rstc_wdth_prc", ""),
            stck_fcam=data.get("stck_fcam", ""),
            stck_sspr=data.get("stck_sspr", ""),
            aspr_unit=data.get("aspr_unit", ""),
            hts_deal_qty_unit_val=data.get("hts_deal_qty_unit_val", ""),
            lstn_stcn=data.get("lstn_stcn", ""),
            hts_avls=data.get("hts_avls", ""),
            per=data.get("per", ""),
            pbr=data.get("pbr", ""),
            stac_month=data.get("stac_month", ""),
            vol_tnrt=data.get("vol_tnrt", ""),
            eps=data.get("eps", ""),
            bps=data.get("bps", ""),
            d250_hgpr=data.get("d250_hgpr", ""),
            d250_hgpr_date=data.get("d250_hgpr_date", ""),
            d250_hgpr_vrss_prpr_rate=data.get("d250_hgpr_vrss_prpr_rate", ""),
            d250_lwpr=data.get("d250_lwpr", ""),
            d250_lwpr_date=data.get("d250_lwpr_date", ""),
            d250_lwpr_vrss_prpr_rate=data.get("d250_lwpr_vrss_prpr_rate", ""),
            stck_dryy_hgpr=data.get("stck_dryy_hgpr", ""),
            dryy_hgpr_vrss_prpr_rate=data.get("dryy_hgpr_vrss_prpr_rate", ""),
            dryy_hgpr_date=data.get("dryy_hgpr_date", ""),
            stck_dryy_lwpr=data.get("stck_dryy_lwpr", ""),
            dryy_lwpr_vrss_prpr_rate=data.get("dryy_lwpr_vrss_prpr_rate", ""),
            dryy_lwpr_date=data.get("dryy_lwpr_date", ""),
            w52_hgpr=data.get("w52_hgpr", ""),
            w52_hgpr_vrss_prpr_ctrt=data.get("w52_hgpr_vrss_prpr_ctrt", ""),
            w52_hgpr_date=data.get("w52_hgpr_date", ""),
            w52_lwpr=data.get("w52_lwpr", ""),
            w52_lwpr_vrss_prpr_ctrt=data.get("w52_lwpr_vrss_prpr_ctrt", ""),
            w52_lwpr_date=data.get("w52_lwpr_date", ""),
            whol_loan_rmnd_rate=data.get("whol_loan_rmnd_rate", ""),
            ssts_yn=data.get("ssts_yn", ""),
            stck_shrn_iscd=data.get("stck_shrn_iscd", ""),
            fcam_cnnm=data.get("fcam_cnnm", ""),
            cpfn_cnnm=data.get("cpfn_cnnm", ""),
            apprch_rate=data.get("apprch_rate", ""),
            frgn_hldn_qty=data.get("frgn_hldn_qty", ""),
            vi_cls_code=data.get("vi_cls_code", ""),
            ovtm_vi_cls_code=data.get("ovtm_vi_cls_code", ""),
            last_ssts_cntg_qty=data.get("last_ssts_cntg_qty", ""),
            invt_caful_yn=data.get("invt_caful_yn", ""),
            mrkt_warn_cls_code=data.get("mrkt_warn_cls_code", ""),
            short_over_yn=data.get("short_over_yn", ""),
            sltr_yn=data.get("sltr_yn", ""),
            mang_issu_cls_code=data.get("mang_issu_cls_code", ""),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(k, v):
            #print(k, v)
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            elif k in ["ft_ord_unpr3", "ft_ccld_unpr3", "ft_ccld_amt3"]:
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = float(v)
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(k, v)
            for k, v in self.__dict__.items()
            if v is not None
        }

@dataclass
class StockDailyPrice:
    """국내주식 가격 정보."""
    
    stck_bsop_date: str               # 주식 영업 일자
    stck_oprc: str                    # 주식 시가2
    stck_hgpr: str                    # 주식 최고가
    stck_lwpr: str                    # 주식 최저가
    stck_clpr: str                    # 주식 종가
    acml_vol: str                     # 누적 거래량
    prdy_vrss_vol_rate: str           # 전일 대비 거래량 비율
    prdy_vrss: str                    # 전일 대비
    prdy_vrss_sign: str               # 전일 대비 부호
    prdy_ctrt: str                    # 전일 대비율
    hts_frgn_ehrt: str                # HTS 외국인 소진율
    frgn_ntby_qty: str                # 외국인 순매수 수량
    flng_cls_code: str                # 락 구분 코드
    acml_prtt_rate: str               # 누적 분할 비율

    FIELD_NAMES_KO = {
        "stck_bsop_date": "주식 영업 일자",
        "stck_oprc": "주식 시가2",
        "stck_hgpr": "주식 최고가",
        "stck_lwpr": "주식 최저가",
        "stck_clpr": "주식 종가",
        "acml_vol": "누적 거래량",
        "prdy_vrss_vol_rate": "전일 대비 거래량 비율",
        "prdy_vrss": "전일 대비",
        "prdy_vrss_sign": "전일 대비 부호",
        "prdy_ctrt": "전일 대비율",
        "hts_frgn_ehrt": "HTS 외국인 소진율",
        "frgn_ntby_qty": "외국인 순매수 수량",
        "flng_cls_code": "락 구분 코드",
        "acml_prtt_rate": "누적 분할 비율",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StockDailyPrice":
        """딕셔너리에서 StockDailyPrice 객체 생성."""
        return cls(
            stck_bsop_date=data.get("stck_bsop_date", ""),
            stck_oprc=data.get("stck_oprc", ""),
            stck_hgpr=data.get("stck_hgpr", ""),
            stck_lwpr=data.get("stck_lwpr", ""),
            stck_clpr=data.get("stck_clpr", ""),
            acml_vol=data.get("acml_vol", ""),
            prdy_vrss_vol_rate=data.get("prdy_vrss_vol_rate", ""),
            prdy_vrss=data.get("prdy_vrss", ""),
            prdy_vrss_sign=data.get("prdy_vrss_sign", ""),
            prdy_ctrt=data.get("prdy_ctrt", ""),
            hts_frgn_ehrt=data.get("hts_frgn_ehrt", ""),
            frgn_ntby_qty=data.get("frgn_ntby_qty", ""),
            flng_cls_code=data.get("flng_cls_code", ""),
            acml_prtt_rate=data.get("acml_prtt_rate", ""),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(k, v):
            #print(k, v)
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            elif k in ["prdy_vrss_vol_rate", "acml_prtt_rate"]:
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = float(v)
                return f"{normalized:,.4f}"  # 소수점 이하 2자리까지 표시
            elif k in ["prdy_ctrt", "hts_frgn_ehrt"]:
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = float(v)
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(k, v)
            for k, v in self.__dict__.items()
            if v is not None
        }

@dataclass
class StockDailyItemchartPrice:
    """국내주식 가격 정보."""
    
    stck_bsop_date: str               # 주식 영업 일자
    stck_clpr: str                    # 주식 종가
    stck_oprc: str                    # 주식 시가
    stck_hgpr: str                    # 주식 최고가
    stck_lwpr: str                    # 주식 최저가
    acml_vol: str                     # 누적 거래량
    acml_tr_pbmn: str                 # 누적 거래 대금
    flng_cls_code: str                # 락 구분 코드
    prtt_rate: str                    # 분할 비율
    mod_yn: str                       # 변경 여부
    prdy_vrss_sign: str               # 전일 대비 부호
    prdy_vrss: str                    # 전일 대비
    revl_issu_reas: str               # 재평가사유코드

    FIELD_NAMES_KO = {
        "stck_bsop_date": "주식 영업 일자",
        "stck_clpr": "주식 종가",
        "stck_oprc": "주식 시가",
        "stck_hgpr": "주식 최고가",
        "stck_lwpr": "주식 최저가",
        "acml_vol": "누적 거래량",
        "acml_tr_pbmn": "누적 거래 대금",
        "flng_cls_code": "락 구분 코드",
        "prtt_rate": "분할 비율",
        "mod_yn": "변경 여부",
        "prdy_vrss_sign": "전일 대비 부호",
        "prdy_vrss": "전일 대비",
        "revl_issu_reas": "재평가사유코드",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StockDailyItemchartPrice":
        """딕셔너리에서 StockDailyItemchartPrice 객체 생성."""
        return cls(
            stck_bsop_date=data.get("stck_bsop_date", ""),
            stck_clpr=data.get("stck_clpr", ""),
            stck_oprc=data.get("stck_oprc", ""),
            stck_hgpr=data.get("stck_hgpr", ""),
            stck_lwpr=data.get("stck_lwpr", ""),
            acml_vol=data.get("acml_vol", ""),
            acml_tr_pbmn=data.get("acml_tr_pbmn", ""),
            flng_cls_code=data.get("flng_cls_code", ""),
            prtt_rate=data.get("prtt_rate", ""),
            mod_yn=data.get("mod_yn", ""),
            prdy_vrss_sign=data.get("prdy_vrss_sign", ""),
            prdy_vrss=data.get("prdy_vrss", ""),
            revl_issu_reas=data.get("revl_issu_reas", ""),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(k, v):
            #print(k, v)
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            elif k in ["ft_ord_unpr3", "ft_ccld_unpr3", "ft_ccld_amt3"]:
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = float(v)
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(k, v)
            for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class BalanceResponseBody(ResponseBody):
    ctx_area_fk100: str  # 연속조회검색조건100
    ctx_area_nk100: str  # 연속조회키100

    FIELD_NAMES_KO = {
        "rt_cd": "성공 실패 여부",
        "msg_cd": "응답코드",
        "msg1": "응답메세지",
        "ctx_area_fk100": "연속조회검색조건100",
        "ctx_area_nk100": "연속조회키100",
    }

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            key = self.FIELD_NAMES_KO.get(k, k)
            if isinstance(v, Decimal):
                result[key] = f"{v:,.2f}"
            else:
                result[key] = v
        return result

@dataclass
class StockCurrentPriceResponse:
    """국내주식 일일가격 조회 API 응답."""
    
    response_body: ResponseBody
    price: StockCurrentPrice

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "StockCurrentPriceResponse":
        """딕셔너리에서 StockCurrentPriceResponse 객체 생성."""
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
            ),
            price=StockCurrentPrice.from_dict(data.get("output1", {})),
        )

@dataclass
class StockDailyPriceResponse:
    """국내주식 일일가격 조회 API 응답."""
    
    response_body: ResponseBody
    prices: list[StockDailyPrice] # 개별 종목 잔고 목록 (output1)

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "StockDailyPriceResponse":
        """딕셔너리에서 StockDailyPriceResponse 객체 생성."""
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
            ),
            prices=[StockDailyPrice.from_dict(item) for item in data.get("output", [])],
        )

@dataclass
class StockDailyItemchartPriceResponse:
    """국내주식 일일가격 조회 API 응답."""
    
    response_body: ResponseBody
    info: StockBasicInfo
    prices: list[StockDailyItemchartPrice] # 개별 종목 잔고 목록 (output1)

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "StockDailyItemchartPriceResponse":
        """딕셔너리에서 StockDailyItemchartPriceResponse 객체 생성."""
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
            ),
            info=StockBasicInfo.from_dict(data.get("output1", {})),
            prices=[StockDailyItemchartPrice.from_dict(item) for item in data.get("output2", [])],
        )
