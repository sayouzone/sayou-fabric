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

"""한국투자증권 국내주식 재무제표 API 응답 데이터 클래스."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .base_model import ResponseBody

# =============================================================================
# 국내주식 대차대조표 [v1_국내주식-078]
# =============================================================================

@dataclass
class BalanceSheet:
    """대차대조표 정보."""
    
    pdno: str                # 상품번호
    prdt_type_cd: str        # 상품유형코드
    mket_id_cd: str          # 시장ID코드
    scty_grp_id_cd: str      # 증권그룹ID코드
    excg_dvsn_cd: str        # 거래소구분코드
    setl_mmdd: str           # 결산월일
    lstg_stqt: int           # 상장주수
    lstg_cptl_amt: Decimal   # 상장자본금액
    cpta: Decimal            # 자본금
    papr: Decimal            # 액면가
    issu_pric: Decimal       # 발행가
    kospi200_item_yn: str    # 코스피200종목여부
    scts_mket_lstg_dt: str   # 유가증권시장상장일
    scts_mket_lstg_abol_dt: Optional[str]  # 유가증권시장상장폐지일
    kosdaq_mket_lstg_dt: Optional[str]     # 코스닥시장상장일
    kosdaq_mket_lstg_abol_dt: Optional[str]  # 코스닥시장상장폐지일
    frbd_mket_lstg_dt: str   # 해외시장상장일
    frbd_mket_lstg_abol_dt: Optional[str]  # 해외시장상장폐지일
    reits_kind_cd: str       # 리츠종류코드
    etf_dvsn_cd: str         # ETF구분코드
    oilf_fund_yn: str        # 유전펀드여부
    idx_bztp_lcls_cd: str    # 지수업종대분류코드
    idx_bztp_mcls_cd: str    # 지수업종중분류코드
    idx_bztp_scls_cd: str    # 지수업종소분류코드
    stck_kind_cd: str        # 주식종류코드
    mfnd_opng_dt: Optional[str]   # 펀드개시일
    mfnd_end_dt: Optional[str]    # 펀드종료일
    dpsi_erlm_cncl_dt: Optional[str]  # 예탁등록취소일
    etf_cu_qty: int          # ETF CU수량
    prdt_name: str           # 상품명
    prdt_name120: str        # 상품명120
    prdt_abrv_name: str      # 상품약어명
    std_pdno: str            # 표준상품번호 (ISIN)
    prdt_eng_name: str       # 상품영문명
    prdt_eng_name120: str    # 상품영문명120
    prdt_eng_abrv_name: str  # 상품영문약어명
    dpsi_aptm_erlm_yn: str   # 예탁지정등록여부
    etf_txtn_type_cd: str    # ETF과세유형코드
    etf_type_cd: str         # ETF유형코드
    lstg_abol_dt: Optional[str]  # 상장폐지일
    nwst_odst_dvsn_cd: str   # 신주구주구분코드
    sbst_pric: Decimal       # 대용가
    thco_sbst_pric: Decimal  # 당사대용가
    thco_sbst_pric_chng_dt: str  # 당사대용가변경일
    tr_stop_yn: str          # 거래정지여부
    admn_item_yn: str        # 관리종목여부
    thdt_clpr: Decimal       # 당일종가
    bfdy_clpr: Decimal       # 전일종가
    clpr_chng_dt: str        # 종가변경일
    std_idst_clsf_cd: str    # 표준산업분류코드
    std_idst_clsf_cd_name: str  # 표준산업분류코드명
    idx_bztp_lcls_cd_name: str  # 지수업종대분류코드명
    idx_bztp_mcls_cd_name: str  # 지수업종중분류코드명
    idx_bztp_scls_cd_name: str  # 지수업종소분류코드명
    ocr_no: str              # OCR번호
    crfd_item_yn: str        # 크라우드펀딩종목여부
    elec_scty_yn: str        # 전자증권여부
    issu_istt_cd: str        # 발행기관코드
    etf_chas_erng_rt_dbnb: Decimal  # ETF괴리수익률
    etf_etn_ivst_heed_item_yn: str  # ETF/ETN투자유의종목여부
    stln_int_rt_dvsn_cd: str  # 대차금리구분코드
    frnr_psnl_lmt_rt: Decimal  # 외국인개인한도율
    lstg_rqsr_issu_istt_cd: str  # 상장신청자발행기관코드
    lstg_rqsr_item_cd: str   # 상장신청자종목코드
    trst_istt_issu_istt_cd: str  # 신탁기관발행기관코드
    nxt_tr_stop_yn: str      # 익일거래정지여부
    cptt_trad_tr_psbl_yn: str  # 경쟁대량거래가능여부

    FIELD_NAMES_KO = {
        "pdno": "상품번호",
        "prdt_type_cd": "상품유형코드",
        "mket_id_cd": "시장ID코드",
        "scty_grp_id_cd": "증권그룹ID코드",
        "excg_dvsn_cd": "거래소구분코드",
        "setl_mmdd": "결산월일",
        "lstg_stqt": "상장주수",
        "lstg_cptl_amt": "상장자본금액",
        "cpta": "자본금",
        "papr": "액면가",
        "issu_pric": "발행가",
        "kospi200_item_yn": "코스피200종목여부",
        "scts_mket_lstg_dt": "유가증권시장상장일",
        "scts_mket_lstg_abol_dt": "유가증권시장상장폐지일",
        "kosdaq_mket_lstg_dt": "코스닥시장상장일",
        "kosdaq_mket_lstg_abol_dt": "코스닥시장상장폐지일",
        "frbd_mket_lstg_dt": "해외시장상장일",
        "frbd_mket_lstg_abol_dt": "해외시장상장폐지일",
        "reits_kind_cd": "리츠종류코드",
        "etf_dvsn_cd": "ETF구분코드",
        "oilf_fund_yn": "유전펀드여부",
        "idx_bztp_lcls_cd": "지수업종대분류코드",
        "idx_bztp_mcls_cd": "지수업종중분류코드",
        "idx_bztp_scls_cd": "지수업종소분류코드",
        "stck_kind_cd": "주식종류코드",
        "mfnd_opng_dt": "펀드개시일",
        "mfnd_end_dt": "펀드종료일",
        "dpsi_erlm_cncl_dt": "예탁등록취소일",
        "etf_cu_qty": "ETF CU수량",
        "prdt_name": "상품명",
        "prdt_name120": "상품명120",
        "prdt_abrv_name": "상품약어명",
        "std_pdno": "표준상품번호",
        "prdt_eng_name": "상품영문명",
        "prdt_eng_name120": "상품영문명120",
        "prdt_eng_abrv_name": "상품영문약어명",
        "dpsi_aptm_erlm_yn": "예탁지정등록여부",
        "etf_txtn_type_cd": "ETF과세유형코드",
        "etf_type_cd": "ETF유형코드",
        "lstg_abol_dt": "상장폐지일",
        "nwst_odst_dvsn_cd": "신주구주구분코드",
        "sbst_pric": "대용가",
        "thco_sbst_pric": "당사대용가",
        "thco_sbst_pric_chng_dt": "당사대용가변경일",
        "tr_stop_yn": "거래정지여부",
        "admn_item_yn": "관리종목여부",
        "thdt_clpr": "당일종가",
        "bfdy_clpr": "전일종가",
        "clpr_chng_dt": "종가변경일",
        "std_idst_clsf_cd": "표준산업분류코드",
        "std_idst_clsf_cd_name": "표준산업분류코드명",
        "idx_bztp_lcls_cd_name": "지수업종대분류코드명",
        "idx_bztp_mcls_cd_name": "지수업종중분류코드명",
        "idx_bztp_scls_cd_name": "지수업종소분류코드명",
        "ocr_no": "OCR번호",
        "crfd_item_yn": "크라우드펀딩종목여부",
        "elec_scty_yn": "전자증권여부",
        "issu_istt_cd": "발행기관코드",
        "etf_chas_erng_rt_dbnb": "ETF괴리수익률",
        "etf_etn_ivst_heed_item_yn": "ETF/ETN투자유의종목여부",
        "stln_int_rt_dvsn_cd": "대차금리구분코드",
        "frnr_psnl_lmt_rt": "외국인개인한도율",
        "lstg_rqsr_issu_istt_cd": "상장신청자발행기관코드",
        "lstg_rqsr_item_cd": "상장신청자종목코드",
        "trst_istt_issu_istt_cd": "신탁기관발행기관코드",
        "nxt_tr_stop_yn": "익일거래정지여부",
        "cptt_trad_tr_psbl_yn": "경쟁대량거래가능여부",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "BalanceSheet":
        """딕셔너리에서 BalanceSheet 객체 생성."""
        return cls(
            pdno=data["pdno"],
            prdt_type_cd=data["prdt_type_cd"],
            mket_id_cd=data["mket_id_cd"],
            scty_grp_id_cd=data["scty_grp_id_cd"],
            excg_dvsn_cd=data["excg_dvsn_cd"],
            setl_mmdd=data["setl_mmdd"],
            lstg_stqt=int(data["lstg_stqt"]),
            lstg_cptl_amt=Decimal(data["lstg_cptl_amt"]),
            cpta=Decimal(data["cpta"]),
            papr=Decimal(data["papr"]),
            issu_pric=Decimal(data["issu_pric"]),
            kospi200_item_yn=data["kospi200_item_yn"],
            scts_mket_lstg_dt=data["scts_mket_lstg_dt"],
            scts_mket_lstg_abol_dt=data.get("scts_mket_lstg_abol_dt") or None,
            kosdaq_mket_lstg_dt=data.get("kosdaq_mket_lstg_dt") or None,
            kosdaq_mket_lstg_abol_dt=data.get("kosdaq_mket_lstg_abol_dt") or None,
            frbd_mket_lstg_dt=data["frbd_mket_lstg_dt"],
            frbd_mket_lstg_abol_dt=data.get("frbd_mket_lstg_abol_dt") or None,
            reits_kind_cd=data.get("reits_kind_cd", ""),
            etf_dvsn_cd=data["etf_dvsn_cd"],
            oilf_fund_yn=data["oilf_fund_yn"],
            idx_bztp_lcls_cd=data["idx_bztp_lcls_cd"],
            idx_bztp_mcls_cd=data["idx_bztp_mcls_cd"],
            idx_bztp_scls_cd=data["idx_bztp_scls_cd"],
            stck_kind_cd=data["stck_kind_cd"],
            mfnd_opng_dt=data.get("mfnd_opng_dt") or None,
            mfnd_end_dt=data.get("mfnd_end_dt") or None,
            dpsi_erlm_cncl_dt=data.get("dpsi_erlm_cncl_dt") or None,
            etf_cu_qty=int(data["etf_cu_qty"]),
            prdt_name=data["prdt_name"],
            prdt_name120=data["prdt_name120"],
            prdt_abrv_name=data["prdt_abrv_name"],
            std_pdno=data["std_pdno"],
            prdt_eng_name=data["prdt_eng_name"],
            prdt_eng_name120=data["prdt_eng_name120"],
            prdt_eng_abrv_name=data["prdt_eng_abrv_name"],
            dpsi_aptm_erlm_yn=data["dpsi_aptm_erlm_yn"],
            etf_txtn_type_cd=data["etf_txtn_type_cd"],
            etf_type_cd=data.get("etf_type_cd", ""),
            lstg_abol_dt=data.get("lstg_abol_dt") or None,
            nwst_odst_dvsn_cd=data["nwst_odst_dvsn_cd"],
            sbst_pric=Decimal(data["sbst_pric"]),
            thco_sbst_pric=Decimal(data["thco_sbst_pric"]),
            thco_sbst_pric_chng_dt=data["thco_sbst_pric_chng_dt"],
            tr_stop_yn=data["tr_stop_yn"],
            admn_item_yn=data["admn_item_yn"],
            thdt_clpr=Decimal(data["thdt_clpr"]),
            bfdy_clpr=Decimal(data["bfdy_clpr"]),
            clpr_chng_dt=data["clpr_chng_dt"],
            std_idst_clsf_cd=data["std_idst_clsf_cd"],
            std_idst_clsf_cd_name=data["std_idst_clsf_cd_name"],
            idx_bztp_lcls_cd_name=data["idx_bztp_lcls_cd_name"],
            idx_bztp_mcls_cd_name=data["idx_bztp_mcls_cd_name"],
            idx_bztp_scls_cd_name=data["idx_bztp_scls_cd_name"],
            ocr_no=data["ocr_no"],
            crfd_item_yn=data.get("crfd_item_yn", ""),
            elec_scty_yn=data["elec_scty_yn"],
            issu_istt_cd=data["issu_istt_cd"],
            etf_chas_erng_rt_dbnb=Decimal(data["etf_chas_erng_rt_dbnb"]),
            etf_etn_ivst_heed_item_yn=data["etf_etn_ivst_heed_item_yn"],
            stln_int_rt_dvsn_cd=data["stln_int_rt_dvsn_cd"],
            frnr_psnl_lmt_rt=Decimal(data["frnr_psnl_lmt_rt"]),
            lstg_rqsr_issu_istt_cd=data.get("lstg_rqsr_issu_istt_cd", ""),
            lstg_rqsr_item_cd=data.get("lstg_rqsr_item_cd", ""),
            trst_istt_issu_istt_cd=data.get("trst_istt_issu_istt_cd", ""),
            nxt_tr_stop_yn=data["nxt_tr_stop_yn"],
            cptt_trad_tr_psbl_yn=data["cptt_trad_tr_psbl_yn"],
        )

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
class BalanceSheetResponse:
    """대차대조표 조회 API 응답."""
    
    response_body: ResponseBody
    balance_sheet: Optional[BalanceSheet]  # 대차대조표

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "BalanceSheetResponse":
        output = data.get("output")
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            balance_sheet=BalanceSheet.from_dict(output) if output else None,
        )


# =============================================================================
# 국내주식 손익계산서 [v1_국내주식-079]
# =============================================================================

@dataclass
class IncomeStatement:
    """손익계산서 정보."""
    
    stac_yymm: str           # 결산년월
    sale_account: Decimal    # 매출액
    sale_cost: Decimal       # 매출원가
    sale_totl_prfi: Decimal  # 매출총이익
    depr_cost: Decimal       # 감가상각비
    sell_mang: Decimal       # 판매관리비
    bsop_prti: Decimal       # 영업이익
    bsop_non_ernn: Decimal   # 영업외수익
    bsop_non_expn: Decimal   # 영업외비용
    op_prfi: Decimal         # 경상이익
    spec_prfi: Decimal       # 특별이익
    spec_loss: Decimal       # 특별손실
    thtr_ntin: Decimal       # 당기순이익

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "sale_account": "매출액",
        "sale_cost": "매출원가",
        "sale_totl_prfi": "매출총이익",
        "depr_cost": "감가상각비",
        "sell_mang": "판매관리비",
        "bsop_prti": "영업이익",
        "bsop_non_ernn": "영업외수익",
        "bsop_non_expn": "영업외비용",
        "op_prfi": "경상이익",
        "spec_prfi": "특별이익",
        "spec_loss": "특별손실",
        "thtr_ntin": "당기순이익",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "IncomeStatement":
        return cls(
            stac_yymm=data["stac_yymm"],
            sale_account=Decimal(data["sale_account"]),
            sale_cost=Decimal(data["sale_cost"]),
            sale_totl_prfi=Decimal(data["sale_totl_prfi"]),
            depr_cost=Decimal(data["depr_cost"]),
            sell_mang=Decimal(data["sell_mang"]),
            bsop_prti=Decimal(data["bsop_prti"]),
            bsop_non_ernn=Decimal(data["bsop_non_ernn"]),
            bsop_non_expn=Decimal(data["bsop_non_expn"]),
            op_prfi=Decimal(data["op_prfi"]),
            spec_prfi=Decimal(data["spec_prfi"]),
            spec_loss=Decimal(data["spec_loss"]),
            thtr_ntin=Decimal(data["thtr_ntin"]),
        )

    def to_korean(self) -> dict:
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
class IncomeStatementResponse:
    """손익계산서 조회 API 응답."""
    
    response_body: ResponseBody
    statements: list[IncomeStatement]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "IncomeStatementResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            statements=[IncomeStatement.from_dict(item) for item in data.get("output", [])],
        )


# =============================================================================
# 국내주식 재무비율 [v1_국내주식-080]
# =============================================================================

@dataclass
class FinancialRatio:
    """재무비율 정보."""
    
    stac_yymm: str        # 결산년월
    grs: Decimal          # 매출액증가율
    bsop_prfi_inrt: Decimal  # 영업이익증가율
    ntin_inrt: Decimal    # 순이익증가율
    roe_val: Decimal      # ROE
    eps: Decimal          # EPS (주당순이익)
    sps: Decimal          # SPS (주당매출액)
    bps: Decimal          # BPS (주당순자산)
    rsrv_rate: Decimal    # 유보율
    lblt_rate: Decimal    # 부채비율

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "grs": "매출액증가율",
        "bsop_prfi_inrt": "영업이익증가율",
        "ntin_inrt": "순이익증가율",
        "roe_val": "ROE",
        "eps": "EPS",
        "sps": "SPS",
        "bps": "BPS",
        "rsrv_rate": "유보율",
        "lblt_rate": "부채비율",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "FinancialRatio":
        return cls(
            stac_yymm=data["stac_yymm"],
            grs=Decimal(data["grs"]),
            bsop_prfi_inrt=Decimal(data["bsop_prfi_inrt"]),
            ntin_inrt=Decimal(data["ntin_inrt"]),
            roe_val=Decimal(data["roe_val"]),
            eps=Decimal(data["eps"]),
            sps=Decimal(data["sps"]),
            bps=Decimal(data["bps"]),
            rsrv_rate=Decimal(data["rsrv_rate"]),
            lblt_rate=Decimal(data["lblt_rate"]),
        )

    def to_korean(self) -> dict:
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
class FinancialRatioResponse:
    """재무비율 조회 API 응답."""
    
    response_body: ResponseBody
    ratios: list[FinancialRatio]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "FinancialRatioResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            ratios=[FinancialRatio.from_dict(item) for item in data.get("output", [])],
        )


# =============================================================================
# 국내주식 수익성비율 [v1_국내주식-081]
# =============================================================================

@dataclass
class ProfitRatio:
    """수익성비율 정보."""
    
    stac_yymm: str              # 결산년월
    cptl_ntin_rate: Decimal     # 총자본순이익률 (ROA)
    self_cptl_ntin_inrt: Decimal  # 자기자본순이익률 (ROE)
    sale_ntin_rate: Decimal     # 매출액순이익률
    sale_totl_rate: Decimal     # 매출총이익률

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "cptl_ntin_rate": "총자본순이익률(ROA)",
        "self_cptl_ntin_inrt": "자기자본순이익률(ROE)",
        "sale_ntin_rate": "매출액순이익률",
        "sale_totl_rate": "매출총이익률",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "ProfitRatio":
        return cls(
            stac_yymm=data["stac_yymm"],
            cptl_ntin_rate=Decimal(data["cptl_ntin_rate"]),
            self_cptl_ntin_inrt=Decimal(data["self_cptl_ntin_inrt"]),
            sale_ntin_rate=Decimal(data["sale_ntin_rate"]),
            sale_totl_rate=Decimal(data["sale_totl_rate"]),
        )

    def to_korean(self) -> dict:
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
class ProfitRatioResponse:
    """수익성비율 조회 API 응답."""
    
    response_body: ResponseBody
    ratios: list[ProfitRatio]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "ProfitRatioResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            ratios=[ProfitRatio.from_dict(item) for item in data.get("output", [])],
        )


# =============================================================================
# 국내주식 기타주요비율 [v1_국내주식-082]
# =============================================================================

@dataclass
class OtherMajorRatio:
    """기타주요비율 정보."""
    
    stac_yymm: str        # 결산년월
    payout_rate: Decimal  # 배당성향
    eva: Decimal          # EVA (경제적부가가치)
    ebitda: Decimal       # EBITDA
    ev_ebitda: Decimal    # EV/EBITDA

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "payout_rate": "배당성향",
        "eva": "EVA",
        "ebitda": "EBITDA",
        "ev_ebitda": "EV/EBITDA",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "OtherMajorRatio":
        return cls(
            stac_yymm=data["stac_yymm"],
            payout_rate=Decimal(data["payout_rate"]),
            eva=Decimal(data["eva"]),
            ebitda=Decimal(data["ebitda"]),
            ev_ebitda=Decimal(data["ev_ebitda"]),
        )

    def to_korean(self) -> dict:
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
class OtherMajorRatioResponse:
    """기타주요비율 조회 API 응답."""
    
    response_body: ResponseBody
    ratios: list[OtherMajorRatio]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "OtherMajorRatioResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            ratios=[OtherMajorRatio.from_dict(item) for item in data.get("output", [])],
        )


# =============================================================================
# 국내주식 안정성비율 [v1_국내주식-083]
# =============================================================================

@dataclass
class StabilityRatio:
    """안정성비율 정보."""
    
    stac_yymm: str       # 결산년월
    lblt_rate: Decimal   # 부채비율
    bram_depn: Decimal   # 차입금의존도
    crnt_rate: Decimal   # 유동비율
    quck_rate: Decimal   # 당좌비율

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "lblt_rate": "부채비율",
        "bram_depn": "차입금의존도",
        "crnt_rate": "유동비율",
        "quck_rate": "당좌비율",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StabilityRatio":
        return cls(
            stac_yymm=data["stac_yymm"],
            lblt_rate=Decimal(data["lblt_rate"]),
            bram_depn=Decimal(data["bram_depn"]),
            crnt_rate=Decimal(data["crnt_rate"]),
            quck_rate=Decimal(data["quck_rate"]),
        )

    def to_korean(self) -> dict:
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
class StabilityRatioResponse:
    """안정성비율 조회 API 응답."""
    
    response_body: ResponseBody
    ratios: list[StabilityRatio]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "StabilityRatioResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            ratios=[StabilityRatio.from_dict(item) for item in data.get("output", [])],
        )


# =============================================================================
# 국내주식 성장성비율 [v1_국내주식-085]
# =============================================================================

@dataclass
class GrowthRatio:
    """성장성비율 정보."""
    
    stac_yymm: str           # 결산년월
    grs: Decimal             # 매출액증가율
    bsop_prfi_inrt: Decimal  # 영업이익증가율
    equt_inrt: Decimal       # 자기자본증가율
    totl_aset_inrt: Decimal  # 총자산증가율

    FIELD_NAMES_KO = {
        "stac_yymm": "결산년월",
        "grs": "매출액증가율",
        "bsop_prfi_inrt": "영업이익증가율",
        "equt_inrt": "자기자본증가율",
        "totl_aset_inrt": "총자산증가율",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "GrowthRatio":
        return cls(
            stac_yymm=data["stac_yymm"],
            grs=Decimal(data["grs"]),
            bsop_prfi_inrt=Decimal(data["bsop_prfi_inrt"]),
            equt_inrt=Decimal(data["equt_inrt"]),
            totl_aset_inrt=Decimal(data["totl_aset_inrt"]),
        )

    def to_korean(self) -> dict:
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
class GrowthRatioResponse:
    """성장성비율 조회 API 응답."""
    
    response_body: ResponseBody
    ratios: list[GrowthRatio]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "GrowthRatioResponse":
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            ratios=[GrowthRatio.from_dict(item) for item in data.get("output", [])],
        )