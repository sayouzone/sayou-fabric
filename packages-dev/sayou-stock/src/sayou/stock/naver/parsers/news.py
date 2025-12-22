import random
import time

from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List, Tuple, Optional
from urllib import parse

from ..client import NaverClient
from ..utils import (
    news_urls,
    finance_url,
    finance_api_url,
)

class NaverNewsParser:
    """
    뉴스 검색 클래스
    
    Independent Naver news pipeline (no NaverCrawler dependency).
    """

    max_per_category = 10
    
    def __init__(self, client: NaverClient, client_id, client_secret):
        self.client = client

        self.client_id = client_id
        self.client_secret = client_secret

    def fetch(
        self,
        category: str = "조회",
        query: str | None = None,
        url: str | None = None,
        max_articles: int = 100
    ) -> List[Dict]:
        """
        질문으로 Naver News API를 뉴스 목록을 조회한다.
        카테고리에 대한 뉴스 목록을 조회한다.
        
        Args:
            category (str): 조회, 카테고리 (정치, 경제, 사회, 생활/문화, IT/과학, 세계). 기본값: 조회
            query (str): 기사 검색 문구
            url (str): 뉴스 검색 URL
            max_articles (int): 최대 뉴스 갯수

        Returns:
            뉴스 Dictionary 목록
        """

        if category != "조회":
            return self._fetch_category_news()
        
        url = news_urls.get("openapi") if not url else url
        enc_text = parse.quote(query)
        #api_url = url.format(query=enc_text, display=max_articles)

        params = {
            "query": enc_text,
            "display": max_articles
        }
        
        api_headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        articles = []
        try:
            print(f"News 목록 URL: {url}, headers: {api_headers}, params: {params}")
            response = self.client._get(url, params=params, headers=api_headers)
            search_result = response.json()

            # JSON에서 link 정보 추출
            news_list = search_result.get('items', [])
            #print(f"Items: {news_list}")
            for news_item in news_list:
                article = {
                    'query': query,
                    'url': news_item.get("link")
                }
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Exception: {e}")
        
        return articles

    def parse(
        self,
        articles: List[Dict]
    ) -> List[Dict]:
        """
        뉴스 목록으로 뉴스 상세 정보를 가져온다.
        제목, 내용, 언론사, 입력일, 기자 목록
        카테고리 X

        Args:
            news_list (List): 신문 기사 URL 목록

        Returns:
            뉴스 상세 Dictionary 목록
        """

        for idx, article in enumerate(articles):
            news_url = article.get('url')
            
            if news_url and 'news.naver.com' in news_url:
                detail = NaverNewsDetail(self.client)
                article = detail.fetch(article)
            
            time.sleep(random.uniform(0.1, 0.3))

        return articles

    def _fetch_category_news(self):
        """
        카테고리별 뉴스 목록을 가져온다.
        """
        
        articles = []
        for category_name, category_url in news_urls.items():
            if category_name == "openapi":
                continue
            print(f"News 목록 URL: {category_url}")
            article_links = self._select_articles(category_url, self.max_per_category)

            for article in article_links:
                category = {
                    'query': category_name
                }
                category.update(article)
                articles.append(category)

        return articles

    def _select_articles(self, category_url, num_articles):

        article_links = []

        referer = "https://news.naver.com/"
        print(category_url, referer)
        response = self.client._get(category_url, referer=referer, timeout=30)
        #print(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            selectors = [
                'a.sa_text_lede',
                'a.sa_text_strong',
                '.sa_text a',
                '.cluster_text_headline a',
                '.cluster_text_lede a'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    #print(element)
                    url = element.get('href')
                    if (url and 'news.naver.com' in url and '/article/'in url
                        and '/comment/' not in url  # 댓글 페이지만 제외
                        and url not in article_links):
                        article_links.append({
                            "title": element.get_text().strip(),
                            "url": url,
                        })
                        if len(article_links) >= num_articles:
                            break
                if len(article_links) >= num_articles:
                    break

            print(f"✅ {len(article_links)}개의 기사 링크 수집 완료")

        except Exception as e:
            print(f" 기사 링크 수집 실패: {e}")

        return article_links[:num_articles]

class NaverNewsDetail:
    
    # 제목
    title_selectors = [
        '#title_area span',
        '#ct .media_end_head_headline',
        '.media_end_head_headline',
        'h2#title_area',
        '.news_end_title'
    ]

    # 본문
    content_selectors = [
        '#dic_area',
        'article#dic_area',
        '.go_trans._article_content',
        '._article_body_contents'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    def __init__(
        self,
        client: NaverClient
    ):
        self.client = client

    def fetch(
        self,
        url: str | None = None,
        article: Dict | None = None
    ):
        news_url = url if url else article.get('url')
        
        try:
            print(f"News Detail URL: {news_url}")
            response = self.client._get(news_url)
            response.raise_for_status()

            # 뉴스 상세 정보 파싱
            _article = self._parse_news(response.text)
            
            article.update(_article)


        except Exception as e:
            print(f"Error scraping {news_url}: {e}")

        finally:
            return article

    def _parse_news(
        self,
        html_text: str
    ) -> Dict:
        """
        HTML에서 뉴스 상세 정보를 파싱한다.
        제목, 본문 내용, 언론사, 입력일, 기자 목록

        Args:
            html_text (str): HTML 텍스트

        Returns:
            뉴스 상세 Dictionary
        """
        soup = BeautifulSoup(html_text, 'html.parser')

        # 제목
        title = self._parse_title(soup)
        # 본문 내용
        content = self._parse_content(soup)
        # 언론사
        press = self._parse_press(soup)
        # 입력일
        published_date = self._parse_published_date(soup)
        # 기자 목록
        authors = self._parse_authors(soup)
        # 카테고리
        category = self._parse_category(soup)

        article = {
            'title': title,
            'content': content,
            'press': press,
            'authors': (", ").join(authors),
            'category': category,
            'published_date': published_date,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        #print(f"Article: {article}")
        return article

    def _parse_title(
        self,
        soup
    ) -> str:
        """
        HTML에서 제목을 파싱한다.

        Args:
            soup:

        Returns:
            제목 문자열
        """
        title = "제목 없음"
        
        for selector in self.title_selectors:
            try:
                title_element = soup.select_one(selector)
                title = title_element.get_text(strip=True)
                break
            except:
                continue

        return title

    def _parse_content(
        self,
        soup
    ) -> str:
        """
        HTML에서 본문 내용을 파싱한다.

        Args:
            soup:

        Returns:
            본문 내용 문자열
        """
        content = "본문 없음"
        
        for selector in self.content_selectors:
            try:
                content_element = soup.select_one(selector)
                content = content_element.get_text(strip=True)
                break
            except:
                continue

        return content

    def _parse_press(
        self,
        soup
    ) -> str:
        """
        HTML에서 언론사를 파싱한다.

        Args:
            soup:

        Returns:
            언론사 문자열
        """
        press = "언론사 불명"
        
        try:
            press_element = soup.select_one('a.media_end_head_top_logo img')
            press = press_element.get('alt')
        except:
            try:
                press_element = soup.select_one('.media_end_head_top_logo_text')
                press = press_element['alt']
            except:
                pass

        return press

    def _parse_published_date(
        self,
        soup
    ) -> str:
        """
        HTML에서 뉴스 입력일을 파싱한다.

        Args:
            soup:

        Returns:
            뉴스 입력일 문자열
        """
        published_date = "뉴스 입력일 불명"
        
        try:
            date_element = soup.select_one('span.media_end_head_info_datestamp_time')
            published_date = date_element.get('data-date-time')
        except:
            published_date = datetime.now().strftime('%Y-%m-%d %H:%M')

        return published_date

    def _parse_authors(
        self,
        soup
    ) -> List:
        """
        HTML에서 기자 목록을 파싱한다.

        Args:
            soup:

        Returns:
            기자 목록
        """
        authors = []
        
        try:
            #author_elements = soup.select('em.media_end_head_journalist_name')
            #author = author_element.get_text(strip=True)
            
            author_elements = soup.select('span.byline_s')
            for author_element in author_elements:
                author = author_element.get_text(strip=True)
                authors.append(author)
        except Exception as e:
            print(f"Exception: {e}")

        return authors
    
    def _parse_category(
        self,
        soup
    ) -> str:
        """
        HTML에서 카테고리를 파싱한다.

        Args:
            soup:

        Returns:
            카테고리
        """
        authors = []
        
        try:
            category_element = soup.select_one('em.media_end_categorize_item')
            category = category_element.get_text(strip=True)
        except Exception as e:
            print(f"Exception: {e}")

        return category