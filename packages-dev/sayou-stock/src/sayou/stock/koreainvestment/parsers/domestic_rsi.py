# Copyright (c) 2025-2026, Sayouzone
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

import logging
import json
import os
import pandas as pd
import requests
import time

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..client import KoreainvestmentClient
from ..models import (
    RequestHeader,
    StockDailyPriceResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

from .domestic_price import DomesticPriceParser
from .domestic import DomesticParser

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomesticRSIParser:
    """KIS 국내 재무 데이터를 파싱하는 클래스"""

    def __init__(
        self,
        client: KoreainvestmentClient,
    ):
        self._client = client

        self._domestic_price_parser = DomesticPriceParser(client)
        self._domestic_parser = DomesticParser(client)
        self._token_manager = TokenManager(client)

    def daily_price(self, stock_code: str, period: int = 100) -> pd.DataFrame:
        """일봉 데이터 조회
        
        Args:
            stock_code: 종목코드 (6자리)
            period: 조회 기간 (일)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
    
        daily_price_response = self._domestic_price_parser.daily_price(stock_code)
        
        if daily_price_response.response_body.rt_cd != '0':
            raise Exception(f"API 에러: {daily_price_response.response_body.msg1}")
        
        # 데이터 파싱
        prices = daily_price_response.prices[:period]  # 최근 period개만 사용
        
        df = pd.DataFrame([{
            'date': item.stck_bsop_date,
            'open': int(item.stck_oprc),
            'high': int(item.stck_hgpr),
            'low': int(item.stck_lwpr),
            'close': int(item.stck_clpr),
            'volume': int(item.acml_vol)
        } for item in prices])
        
        # 날짜순 정렬 (과거→현재)
        df = df.sort_values('date').reset_index(drop=True)
        
        return df

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI(Relative Strength Index) 계산
        
        Args:
            prices: 종가 시리즈
            period: RSI 기간 (기본 14일)
        
        Returns:
            RSI 값 시리즈
        """
        delta = prices.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def rsi_screening(self, stock_codes: List[str], 
                          rsi_period: int = 14,
                          oversold_threshold: int = 30,
                          overbought_threshold: int = 70) -> pd.DataFrame:
        """RSI 기준으로 매수/매도 후보 종목 선택
        
        Args:
            stock_codes: 분석할 종목코드 리스트
            rsi_period: RSI 계산 기간
            oversold_threshold: 과매도 기준 (기본 30)
            overbought_threshold: 과매수 기준 (기본 70)
        
        Returns:
            종목 분석 결과 DataFrame
        """
        results = []
        
        for stock_code in stock_codes:
            try:
                # API 호출 제한 대응 (초당 20건)
                time.sleep(0.1)
                
                # 주가 데이터 조회
                df = self.daily_price(stock_code, period=100)
                
                # RSI 계산
                df['rsi'] = self.calculate_rsi(df['close'], period=rsi_period)
                
                # 최신 데이터
                latest = df.iloc[-1]
                current_rsi = latest['rsi']
                current_price = latest['close']
                
                # 종목명 조회 (옵션)
                stock_info = self._domestic_parser.search_stock_info(stock_code)
                stock_name = stock_info.info.prdt_name.replace("보통주", "").strip()
                
                # 신호 판단
                signal = None
                if current_rsi < oversold_threshold:
                    signal = "매수"
                elif current_rsi > overbought_threshold:
                    signal = "매도"
                else:
                    signal = "보류"
                
                results.append({
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': current_price,
                    'rsi': round(current_rsi, 2),
                    'signal': signal,
                    'date': latest['date']
                })
                
                print(f"{stock_code} ({stock_name}): RSI={current_rsi:.2f}, 신호={signal}")
                
            except Exception as e:
                print(f"{stock_code} 처리 실패: {str(e)}")
                continue
        
        result_df = pd.DataFrame(results)
        print(result_df)
        
        # 정렬 (매수 신호 우선, RSI 낮은 순)
        result_df = result_df.sort_values(['signal', 'rsi'], 
                                         ascending=[False, True])
        
        return result_df

    def advanced_rsi_screening(self, stock_codes: List[str]) -> pd.DataFrame:
        """RSI + 거래량 + 가격 모멘텀 복합 분석
        
        Args:
            stock_codes: 분석할 종목코드 리스트
        
        Returns:
            종목 분석 결과 DataFrame

        점수 체계:
            - rsi_oversold (1점): RSI < 30 (과매도 구간)
            - rsi_turning_up (1점): RSI 상승 반전
            - volume_surge (1점): 거래량 급증 (평균 대비 1.5배 이상)
            - golden_cross (1점): 단기 이평선이 장기 이평선 돌파
        
            최대 4점, 3점 이상 추천
        """
        
        results = []
        
        for stock_code in stock_codes:
            try:
                time.sleep(0.1)
                
                df = self.daily_price(stock_code, period=100)
                df['rsi'] = self.calculate_rsi(df['close'], period=14)
                
                # 거래량 이동평균
                df['volume_ma20'] = df['volume'].rolling(window=20).mean()
                
                # 가격 이동평균
                df['price_ma5'] = df['close'].rolling(window=5).mean()
                df['price_ma20'] = df['close'].rolling(window=20).mean()
                
                # 최신 데이터와 이전 데이터
                latest = df.iloc[-1]
                prev = df.iloc[-2]

                # 종목명 조회 (옵션)
                stock_info = self._domestic_parser.search_stock_info(stock_code)
                stock_name = stock_info.info.prdt_name.replace("보통주", "").strip()

                # ===== 복합 조건 체크 =====
            
                # 1. RSI 과매도 (RSI < 30)
                rsi_oversold = latest['rsi'] < 30
                
                # 2. RSI 상승 반전 (RSI가 전일보다 상승)
                rsi_turning_up = latest['rsi'] > prev['rsi']
                
                # 3. 거래량 급증 (평균 대비 1.5배 이상)
                volume_surge = latest['volume'] > latest['volume_ma20'] * 1.5
                
                # 4. 골든크로스 (5일선이 20일선 돌파)
                golden_cross = latest['price_ma5'] > latest['price_ma20']
                
                # 복합 조건 체크
                conditions = {
                    'rsi_oversold': rsi_oversold,
                    'rsi_turning_up': rsi_turning_up,
                    'volume_surge': volume_surge,
                    'golden_cross': golden_cross
                }
                
                score = sum(conditions.values())

                # 결과 저장
                result = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': latest['close'],
                    'rsi': round(latest['rsi'], 2),
                    'rsi_prev': round(prev['rsi'], 2),
                    'volume': latest['volume'],
                    'volume_ma20': int(latest['volume_ma20']),
                    'volume_ratio': round(latest['volume'] / latest['volume_ma20'], 2),
                    'ma5': int(latest['price_ma5']),
                    'ma20': int(latest['price_ma20']),
                    'score': score,
                    'rsi_oversold': '✓' if rsi_oversold else '✗',
                    'rsi_turning_up': '✓' if rsi_turning_up else '✗',
                    'volume_surge': '✓' if volume_surge else '✗',
                    'golden_cross': '✓' if golden_cross else '✗',
                    'date': latest['date']
                }
                
                results.append(result)
                
                print(f"완료 (점수: {score}/4)")
                
            except Exception as e:
                print(f"{stock_code} 처리 실패: {str(e)}")
                continue
        
        result_df = pd.DataFrame(results)

        # 정렬: 점수 높은 순 → RSI 낮은 순
        result_df = result_df.sort_values(['score', 'rsi'], ascending=[False, True])
        
        return result_df

    def advanced_rsi_screening_detailed(self, stock_codes: List[str],
                                   rsi_threshold: int = 30,
                                   volume_multiplier: float = 1.5) -> pd.DataFrame:
        """더 상세한 분석 버전 (파라미터 커스터마이징 가능)
        
        Args:
            stock_codes: 분석할 종목코드 리스트
            rsi_threshold: RSI 과매도 기준 (기본 30)
            volume_multiplier: 거래량 급증 배수 (기본 1.5)
        
        Returns:
            상세 분석 결과 DataFrame
        """
        results = []
        
        print("\n상세 분석 시작...")
        print(f"설정: RSI 기준={rsi_threshold}, 거래량 배수={volume_multiplier}")
        print("-" * 100)
        
        for idx, stock_code in enumerate(stock_codes, 1):
            try:
                time.sleep(0.1)
                
                print(f"[{idx}/{len(stock_codes)}] {stock_code} 분석 중...", end=" ")
                
                # 주가 데이터 조회
                df = self.daily_price(stock_code, period=100)
                
                # 기술적 지표 계산
                df['rsi'] = self.calculate_rsi(df['close'], period=14)
                df['volume_ma20'] = df['volume'].rolling(window=20).mean()
                df['price_ma5'] = df['close'].rolling(window=5).mean()
                df['price_ma20'] = df['close'].rolling(window=20).mean()
                df['price_ma60'] = df['close'].rolling(window=60).mean()
                
                # MACD 계산 (추가)
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                df['macd'] = exp1 - exp2
                df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                df['macd_hist'] = df['macd'] - df['macd_signal']
                
                # 볼린저 밴드 (추가)
                df['bb_middle'] = df['close'].rolling(window=20).mean()
                df['bb_std'] = df['close'].rolling(window=20).std()
                df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
                df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
                
                # 최신/이전 데이터
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                prev2 = df.iloc[-3]
                
                # 종목명 조회 (옵션)
                stock_info = self._domestic_parser.search_stock_info(stock_code)
                stock_name = stock_info.info.prdt_name.replace("보통주", "").strip()
                
                # ===== 기본 조건 =====
                rsi_oversold = latest['rsi'] < rsi_threshold
                rsi_turning_up = latest['rsi'] > prev['rsi']
                volume_surge = latest['volume'] > latest['volume_ma20'] * volume_multiplier
                golden_cross = latest['price_ma5'] > latest['price_ma20']
                
                # ===== 추가 조건 =====
                
                # MACD 골든크로스
                macd_golden = (latest['macd'] > latest['macd_signal'] and 
                            prev['macd'] <= prev['macd_signal'])
                
                # MACD 히스토그램 증가
                macd_hist_increasing = latest['macd_hist'] > prev['macd_hist']
                
                # 볼린저 밴드 하단 터치 (반등 가능성)
                bb_touch_lower = latest['close'] <= latest['bb_lower'] * 1.02
                
                # 가격이 60일 이평선 위
                above_ma60 = latest['close'] > latest['price_ma60']
                
                # RSI 다이버전스 (가격은 하락, RSI는 상승)
                rsi_divergence = (latest['close'] < prev2['close'] and 
                                latest['rsi'] > prev2['rsi'])
                
                # 조건별 점수
                basic_conditions = {
                    'rsi_oversold': rsi_oversold,
                    'rsi_turning_up': rsi_turning_up,
                    'volume_surge': volume_surge,
                    'golden_cross': golden_cross,
                }
                
                advanced_conditions = {
                    'macd_golden': macd_golden,
                    'macd_hist_increasing': macd_hist_increasing,
                    'bb_touch_lower': bb_touch_lower,
                    'above_ma60': above_ma60,
                    'rsi_divergence': rsi_divergence,
                }
                
                basic_score = sum(basic_conditions.values())
                advanced_score = sum(advanced_conditions.values())
                total_score = basic_score + advanced_score
                
                # 추천 등급
                if total_score >= 7:
                    recommendation = "강력추천"
                elif total_score >= 5:
                    recommendation = "추천"
                elif total_score >= 3:
                    recommendation = "관심"
                else:
                    recommendation = "보류"
                
                # 결과 저장
                result = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': latest['close'],
                    'recommendation': recommendation,
                    'total_score': total_score,
                    'basic_score': basic_score,
                    'advanced_score': advanced_score,
                    
                    # RSI 정보
                    'rsi': round(latest['rsi'], 2),
                    'rsi_change': round(latest['rsi'] - prev['rsi'], 2),
                    
                    # 거래량 정보
                    'volume_ratio': round(latest['volume'] / latest['volume_ma20'], 2),
                    
                    # 이동평균 정보
                    'ma5_vs_ma20': "위" if golden_cross else "아래",
                    'price_vs_ma60': "위" if above_ma60 else "아래",
                    
                    # MACD 정보
                    'macd': round(latest['macd'], 2),
                    'macd_signal': round(latest['macd_signal'], 2),
                    'macd_hist': round(latest['macd_hist'], 2),
                    
                    # 볼린저 밴드 정보
                    'bb_position': round((latest['close'] - latest['bb_lower']) / 
                                        (latest['bb_upper'] - latest['bb_lower']) * 100, 1),
                    
                    # 조건 체크
                    **{k: '✓' if v else '✗' for k, v in basic_conditions.items()},
                    **{k: '✓' if v else '✗' for k, v in advanced_conditions.items()},
                    
                    'date': latest['date']
                }
                
                results.append(result)
                
                print(f"완료 (점수: {total_score}/9, {recommendation})")
                
            except Exception as e:
                print(f"실패 - {str(e)}")
                continue
        
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(['total_score', 'rsi'], 
                                        ascending=[False, True])
        
        return result_df