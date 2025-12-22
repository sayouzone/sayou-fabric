"""
OpenDart 유틸리티 함수 및 상수
"""

# ============================================================
# 상수 정의
# ============================================================

API_URL = "https://opendart.fss.or.kr/api"
MAIN_URL = "https://dart.fss.or.kr/dsaf001/main.do"
PDF_URL = "https://dart.fss.or.kr/pdf/download/pdf.do?rcp_no={rcp_no}&dcm_no={dcm_no}"
PDF_MAIN_URL = "http://dart.fss.or.kr/pdf/download/main.do"
VIEWER_URL = "https://dart.fss.or.kr/report/viewer.do"

"""
공시정보: Public Disclosure, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS001
정기보고서 주요정보: Key Information in Periodic Reports, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS002
정기보고서 재무정보: Financial Information in Periodic Reports, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS003
지분공시 종합정보: Comprehensive Share Ownership Information, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS004
주요사항보고서 주요정보: Key Information in Reports on Material Facts, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS005
증권신고서 주요정보: Key Information in Registration Statements, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS006
"""

# 공시정보
disclosure_urls = {
    "공시검색": f"{API_URL}/list.json", # 공시 유형별, 회사별, 날짜별 등 여러가지 조건으로 공시보고서 검색기능을 제공합니다.
    "기업개황": f"{API_URL}/company.json", # DART에 등록되어있는 기업의 개황정보를 제공합니다.
    "공시서류원본파일": f"{API_URL}/document.xml", # 공시보고서 원본파일을 제공합니다.
    "고유번호": f"{API_URL}/corpCode.json" # DART에 등록되어있는 공시대상회사의 고유번호,회사명,종목코드, 최근변경일자를 파일로 제공합니다.
}

# 정기보고서 주요정보
reports_urls = {
    "증자(감자) 현황": f"{API_URL}/irdsSttus.json",                    # 정기보고서(사업, 분기, 반기보고서) 내에 증자(감자) 현황을 제공합니다.
    "배당에 관한 사항": f"{API_URL}/alotMatter.json",                   # 정기보고서(사업, 분기, 반기보고서) 내에 배당에 관한 사항을 제공합니다.
    "자기주식 취득 및 처분 현황": f"{API_URL}/tesstkAcqsDspsSttus.json",   # 정기보고서(사업, 분기, 반기보고서) 내에 자기주식 취득 및 처분 현황을 제공합니다.
    "최대주주 현황": f"{API_URL}/hyslrSttus.json",                      # 정기보고서(사업, 분기, 반기보고서) 내에 최대주주 현황을 제공합니다.
    "최대주주 변동현황": f"{API_URL}/hyslrChgSttus.json",                # 정기보고서(사업, 분기, 반기보고서) 내에 최대주주 변동현황을 제공합니다.
    "소액주주 현황": f"{API_URL}/mrhlSttus.json",                       # 정기보고서(사업, 분기, 반기보고서) 내에 소액주주 현황을 제공합니다.
    "임원 현황": f"{API_URL}/exctvSttus.json",                         # 정기보고서(사업, 분기, 반기보고서) 내에 임원 현황을 제공합니다.
    "직원 현황": f"{API_URL}/empSttus.json",                           # 정기보고서(사업, 분기, 반기보고서) 내에 직원 현황을 제공합니다.
    "이사·감사의 개인별 보수현황(5억원 이상)": f"{API_URL}/hmvAuditIndvdlBySttus.json",         # 정기보고서(사업, 분기, 반기보고서) 내에 이사·감사의 개인별 보수현황(5억원 이상)을 제공합니다.
    "이사·감사 전체의 보수현황(보수지급금액 - 이사·감사 전체)": f"{API_URL}/hmvAuditAllSttus.json", # 정기보고서(사업, 분기, 반기보고서) 내에 이사·감사 전체의 보수현황(보수지급금액 - 이사·감사 전체)을 제공합니다.
    "개인별 보수지급 금액(5억이상 상위5인)": f"{API_URL}/indvdlByPay.json",                     # 정기보고서(사업, 분기, 반기보고서) 내에 개인별 보수지급 금액(5억이상 상위5인)을 제공합니다.
    "타법인 출자현황": f"{API_URL}/otrCprInvstmntSttus.json",                               # 정기보고서(사업, 분기, 반기보고서) 내에 타법인 출자현황을 제공합니다.
    "주식의 총수 현황": f"{API_URL}/stockTotqySttus.json",                                  # 정기보고서(사업, 분기, 반기보고서) 내에 주식의총수현황을 제공합니다.
    "채무증권 발행실적": f"{API_URL}/detScritsIsuAcmslt.json",                                 # 정기보고서(사업, 분기, 반기보고서) 내에 채무증권 발행실적을 제공합니다.
    "기업어음증권 미상환 잔액": f"{API_URL}/entrprsBilScritsNrdmpBlce.json",                     # 정기보고서(사업, 분기, 반기보고서) 내에 기업어음증권 미상환 잔액을 제공합니다.
    "단기사채 미상환 잔액": f"{API_URL}/srtpdPsndbtNrdmpBlce.json",                             # 정기보고서(사업, 분기, 반기보고서) 내에 단기사채 미상환 잔액을 제공합니다.
    "회사채 미상환 잔액": f"{API_URL}/cprndNrdmpBlce.json",                                     # 정기보고서(사업, 분기, 반기보고서) 내에 회사채 미상환 잔액을 제공합니다.
    "신종자본증권 미상환 잔액": f"{API_URL}/newCaplScritsNrdmpBlce.json",                        # 정기보고서(사업, 분기, 반기보고서) 내에 신종자본증권 미상환 잔액을 제공합니다.
    "조건부 자본증권 미상환 잔액": f"{API_URL}/cndlCaplScritsNrdmpBlce.json",                    # 정기보고서(사업, 분기, 반기보고서) 내에 조건부 자본증권 미상환 잔액을 제공합니다.
    "회계감사인의 명칭 및 감사의견": f"{API_URL}/accnutAdtorNmNdAdtOpinion.json",                 # 정기보고서(사업, 분기, 반기보고서) 내에 회계감사인의 명칭 및 감사의견을 제공합니다.
    "감사용역체결현황": f"{API_URL}/adtServcCnclsSttus.json",                                  # 정기보고서(사업, 분기, 반기보고서) 내에 감사용역체결현황을 제공합니다.
    "회계감사인과의 비감사용역 계약체결 현황": f"{API_URL}/accnutAdtorNonAdtServcCnclsSttus.json",  # 정기보고서(사업, 분기, 반기보고서) 내에 회계감사인과의 비감사용역 계약체결 현황을 제공합니다.
    "사외이사 및 그 변동현황": f"{API_URL}/outcmpnyDrctrNdChangeSttus.json",                    # 정기보고서(사업, 분기, 반기보고서) 내에 사외이사 및 그 변동현황을 제공합니다.
    "미등기임원 보수현황": f"{API_URL}/unrstExctvMendngSttus.json",                             # 정기보고서(사업, 분기, 반기보고서) 내에 미등기임원 보수현황을 제공합니다.
    "이사·감사 전체의 보수현황(주주총회 승인금액)": f"{API_URL}/drctrAdtAllMendngSttusGmtsckConfmAmount.json",      # 정기보고서(사업, 분기, 반기보고서) 내에 이사·감사 전체의 보수현황(주주총회 승인금액)을 제공합니다.
    "이사·감사 전체의 보수현황(보수지급금액 - 유형별)": f"{API_URL}/drctrAdtAllMendngSttusMendngPymntamtTyCl.json",  # 정기보고서(사업, 분기, 반기보고서) 내에 이사·감사 전체의 보수현황(보수지급금액 - 유형별)을 제공합니다.
    "공모자금의 사용내역": f"{API_URL}/pssrpCptalUseDtls.json",     # 정기보고서(사업, 분기, 반기보고서) 내에 공모자금의 사용내역을 제공합니다.
    "사모자금의 사용내역": f"{API_URL}/prvsrpCptalUseDtls.json",    # 정기보고서(사업, 분기, 반기보고서) 내에 사모자금의 사용내역을 제공합니다.
}

# 정기보고서 재무정보
finance_urls = {
    "단일회사 주요계정": f"{API_URL}/fnlttSinglAcnt.json",          # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 주요계정과목(재무상태표, 손익계산서)을 제공합니다.
    "다중회사 주요계정": f"{API_URL}/fnlttMultiAcnt.json",          # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 주요계정과목(재무상태표, 손익계산서)을 제공합니다. (대상법인 복수조회 복수조회 가능)
    "재무제표 원본파일(XBRL)": f"{API_URL}/fnlttXbrl.xml",          # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 원본파일(XBRL)을 제공합니다.
    "단일회사 전체 재무제표": f"{API_URL}/fnlttSinglAcntAll.json",   # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 모든계정과목을 제공합니다.
    "XBRL택사노미재무제표양식": f"{API_URL}/xbrlTaxonomy.json",      # 금융감독원 회계포탈에서 제공하는 IFRS 기반 XBRL 재무제표 공시용 표준계정과목체계(계정과목) 을 제공합니다.
    "단일회사 주요 재무지표": f"{API_URL}/fnlttSinglIndx.json",      # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 주요 재무지표를 제공합니다.
    "다중회사 주요 재무지표": f"{API_URL}/fnlttCmpnyIndx.json"       # 상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 주요 재무지표를 제공합니다.(대상법인 복수조회 가능)
}

# 지분공시 종합정보
ownership_urls = {
    "대량보유 상황보고": f"{API_URL}/majorstock.json",  # 주식등의 대량보유상황보고서 내에 대량보유 상황보고 정보를 제공합니다.
    "임원ㆍ주요주주 소유보고": f"{API_URL}/elestock.json" # 임원ㆍ주요주주특정증권등 소유상황보고서 내에 임원ㆍ주요주주 소유보고 정보를 제공합니다.
}

# 주요사항보고서 주요정보
material_facts_urls = {
    "자산양수도(기타), 풋백옵션": f"{API_URL}/astInhtrfEtcPtbkOpt.json", # 주요사항보고서(자산양수도(기타), 풋백옵션) 내에 주요 정보를 제공합니다.
    "부도발생": f"{API_URL}/dfOcr.json",                            # 주요사항보고서(부도발생) 내에 주요 정보를 제공합니다.
    "영업정지": f"{API_URL}/bsnSp.json",                            # 주요사항보고서(영업정지) 내에 주요 정보를 제공합니다.
    "회생절차 개시신청": f"{API_URL}/ctrcvsBgrq.json",                # 주요사항보고서(회생절차 개시신청) 내에 주요 정보를 제공합니다.
    "해산사유 발생": f"{API_URL}/dsRsOcr.json",                      # 주요사항보고서(해산사유 발생) 내에 주요 정보를 제공합니다.
    "유상증자 결정": f"{API_URL}/piicDecsn.json",                    # 주요사항보고서(유상증자 결정) 내에 주요 정보를 제공합니다.
    "무상증자 결정": f"{API_URL}/fricDecsn.json",                    # 주요사항보고서(무상증자 결정) 내에 주요 정보를 제공합니다.
    "유무상증자 결정": f"{API_URL}/pifricDecsn.json",                 # 주요사항보고서(유무상증자 결정) 내에 주요 정보를 제공합니다.
    "감자 결정": f"{API_URL}/crDecsn.json",                         # 주요사항보고서(감자 결정) 내에 주요 정보를 제공합니다.
    "채권은행 등의 관리절차 개시": f"{API_URL}/bnkMngtPcbg.json",        # 주요사항보고서(채권은행 등의 관리절차 개시) 내에 주요 정보를 제공합니다.
    "소송 등의 제기": f"{API_URL}/lwstLg.json",                      # 주요사항보고서(소송 등의 제기) 내에 주요 정보를 제공합니다.
    "해외 증권시장 주권등 상장 결정": f"{API_URL}/ovLstDecsn.json",      # 주요사항보고서(해외 증권시장 주권등 상장 결정) 내에 주요 정보를 제공합니다.
    "해외 증권시장 주권등 상장폐지 결정": f"{API_URL}/ovDlstDecsn.json",  # 주요사항보고서(해외 증권시장 주권등 상장폐지 결정) 내에 주요 정보를 제공합니다.
    "해외 증권시장 주권등 상장": f"{API_URL}/ovLst.json",               # 주요사항보고서(해외 증권시장 주권등 상장) 내에 주요 정보를 제공합니다.
    "해외 증권시장 주권등 상장폐지": f"{API_URL}/ovDlst.json",           # 주요사항보고서(해외 증권시장 주권등 상장폐지) 내에 주요 정보를 제공합니다.
    "전환사채권 발행결정": f"{API_URL}/cvbdIsDecsn.json",              # 주요사항보고서(전환사채권 발행결정) 내에 주요 정보를 제공합니다.
    "신주인수권부사채권 발행결정": f"{API_URL}/bdwtIsDecsn.json",        # 주요사항보고서(신주인수권부사채권 발행결정) 내에 주요 정보를 제공합니다.
    "교환사채권 발행결정": f"{API_URL}/exbdIsDecsn.json",              # 주요사항보고서(교환사채권 발행결정) 내에 주요 정보를 제공합니다.
    "채권은행 등의 관리절차 중단": f"{API_URL}/bnkMngtPcsp.json",        # 주요사항보고서(채권은행 등의 관리절차 중단) 내에 주요 정보를 제공합니다.
    "상각형 조건부자본증권 발행결정": f"{API_URL}/wdCocobdIsDecsn.json",  # 주요사항보고서(상각형 조건부자본증권 발행결정) 내에 주요 정보를 제공합니다.
    "자기주식 취득 결정": f"{API_URL}/tsstkAqDecsn.json",                  # 주요사항보고서(자기주식 취득 결정) 내에 주요 정보를 제공합니다.
    "자기주식 처분 결정": f"{API_URL}/tsstkDpDecsn.json",                  # 주요사항보고서(자기주식 처분 결정) 내에 주요 정보를 제공합니다.
    "자기주식취득 신탁계약 체결 결정": f"{API_URL}/tsstkAqTrctrCnsDecsn.json", # 주요사항보고서(자기주식취득 신탁계약 체결 결정) 내에 주요 정보를 제공합니다.
    "자기주식취득 신탁계약 해지 결정": f"{API_URL}/tsstkAqTrctrCcDecsn.json",  # 주요사항보고서(자기주식취득 신탁계약 해지 결정) 내에 주요 정보를 제공합니다.
    "영업양수 결정": f"{API_URL}/bsnInhDecsn.json",                           # 주요사항보고서(영업양수 결정) 내에 주요 정보를 제공합니다.
    "영업양도 결정": f"{API_URL}/bsnTrfDecsn.json",                           # 주요사항보고서(영업양도 결정) 내에 주요 정보를 제공합니다.
    "유형자산 양수 결정": f"{API_URL}/tgastInhDecsn.json",                     # 주요사항보고서(유형자산 양수 결정) 내에 주요 정보를 제공합니다.
    "유형자산 양도 결정": f"{API_URL}/tgastTrfDecsn.json",                     # 주요사항보고서(유형자산 양도 결정) 내에 주요 정보를 제공합니다.
    "타법인 주식 및 출자증권 양수결정": f"{API_URL}/otcprStkInvscrInhDecsn.json", # 주요사항보고서(타법인 주식 및 출자증권 양수결정) 내에 주요 정보를 제공합니다.
    "타법인 주식 및 출자증권 양도결정": f"{API_URL}/otcprStkInvscrTrfDecsn.json", # 주요사항보고서(타법인 주식 및 출자증권 양도결정) 내에 주요 정보를 제공합니다.
    "주권 관련 사채권 양수 결정": f"{API_URL}/stkrtbdInhDecsn.json",            # 주요사항보고서(주권 관련 사채권 양수 결정) 내에 주요 정보를 제공합니다.
    "주권 관련 사채권 양도 결정": f"{API_URL}/stkrtbdTrfDecsn.json",            # 주요사항보고서(주권 관련 사채권 양도 결정) 내에 주요 정보를 제공합니다.
    "회사합병 결정": f"{API_URL}/cmpMgDecsn.json",                           # 주요사항보고서(회사합병 결정) 내에 주요 정보를 제공합니다.
    "회사분할 결정": f"{API_URL}/cmpDvDecsn.json",                           # 주요사항보고서(회사분할 결정) 내에 주요 정보를 제공합니다.
    "회사분할합병 결정": f"{API_URL}/cmpDvmgDecsn.json",                      # 주요사항보고서(회사분할합병 결정) 내에 주요 정보를 제공합니다.
    "주식교환·이전 결정": f"{API_URL}/stkExtrDecsn.json",                     # 주요사항보고서(주식교환·이전 결정) 내에 주요 정보를 제공합니다.
}

# 증권신고서 주요정보
registration_urls = {
    "지분증권": f"{API_URL}/estkRs.json",           # 증권신고서(지분증권) 내에 요약 정보를 제공합니다.
    "채무증권": f"{API_URL}/bdRs.json",             # 증권신고서(채무증권) 내에 요약 정보를 제공합니다.
    "증권예탁증권": f"{API_URL}/stkdpRs.json",       # 증권신고서(증권예탁증권) 내에 요약 정보를 제공합니다.
    "합병": f"{API_URL}/mgRs.json",                # 증권신고서(합병) 내에 요약 정보를 제공합니다.
    "주식의포괄적교환·이전": f"{API_URL}/extrRs.json",  # 증권신고서(주식의포괄적교환·이전) 내에 요약 정보를 제공합니다.
    "분할": f"{API_URL}/dvRs.json"                 # 증권신고서(분할) 내에 요약 정보를 제공합니다.
}

quarters = {
    "1": "11013", # 1분기보고서
    "2": "11012", # 반기보고서
    "3": "11014", # 3분기보고서
    "4": "11011"  # 사업보고서
}

def decode_euc_kr(text):
    """깨진 한글 인코딩 복원"""
    # EUC-KR로 인코딩된 문자열이 Latin-1(ISO-8859-1)로 잘못 해석된 경우
    try:
        enc_text = text.encode('latin-1').decode('euc-kr')
        return enc_text
    except:
        pass
    
    # CP949로 시도
    try:
        enc_text = text.encode('latin-1').decode('cp949')
        return enc_text
    except:
        pass
    
    return text

