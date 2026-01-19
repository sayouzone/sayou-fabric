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
    """대차대조표 정보"""
    stac_yymm: str           # 결산 년월
    cras: str                # 유동자산
    fxas: str                # 고정자산
    total_aset: str          # 자산총계
    flow_lblt: str           # 유동부채
    fix_lblt: str            # 고정부채
    total_lblt: str          # 부채총계
    cpfn: str                # 자본금
    cfp_surp: str            # 자본 잉여금
    prfi_surp: str           # 이익 잉여금
    total_cptl: str          # 자본총계

    FIELD_NAMES_KO = {
        "stac_yymm": "결산 년월",
        "cras": "유동자산",
        "fxas": "고정자산",
        "total_aset": "자산총계",
        "flow_lblt": "유동부채",
        "fix_lblt": "고정부채",
        "total_lblt": "부채총계",
        "cpfn": "자본금",
        "cfp_surp": "자본 잉여금",
        "prfi_surp": "이익 잉여금",
        "total_cptl": "자본총계",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "BalanceSheet":
        return cls(
            stac_yymm=data.get("stac_yymm"),
            cras=data.get("cras"),
            fxas=data.get("fxas"),
            total_aset=data.get("total_aset"),
            flow_lblt=data.get("flow_lblt"),
            fix_lblt=data.get("fix_lblt"),
            total_lblt=data.get("total_lblt"),
            cpfn=data.get("cpfn"),
            cfp_surp=data.get("cfp_surp"),
            prfi_surp=data.get("prfi_surp"),
            total_cptl=data.get("total_cptl"),
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
    balance_sheets: list[BalanceSheet]  # 대차대조표

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "BalanceSheetResponse":
        output = data.get("output", [])
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            balance_sheets=[BalanceSheet.from_dict(item) for item in output],
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