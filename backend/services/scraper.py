import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from loguru import logger
import time
from urllib.parse import urljoin, urlparse


class MedicalScraper:
    """Scrapes medical articles from trusted sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://www.who.int"
    
    def get_who_fact_sheet_links(self, max_topics: int = None) -> List[Dict[str, str]]:
        """
        Scrape WHO fact sheets page to get all topic links
        
        Args:
            max_topics: Maximum number of topics to scrape (None = scrape all)
            
        Returns:
            List of dicts with 'title' and 'url'
        """
        try:
            url = f"{self.base_url}/news-room/fact-sheets"
            logger.info(f"Fetching WHO fact sheets from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find all fact sheet links
            # WHO fact sheets are typically in a list or grid format
            links = []
            
            # Try different selectors to find fact sheet links
            fact_sheet_links = soup.find_all('a', href=True)
            
            for link in fact_sheet_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Filter for fact sheet links
                if '/news-room/fact-sheets/detail/' in href and title:
                    full_url = urljoin(self.base_url, href)
                    
                    # Avoid duplicates
                    if not any(item['url'] == full_url for item in links):
                        links.append({
                            'title': title,
                            'url': full_url
                        })
                        
                        # Stop if max_topics is set and reached
                        if max_topics and len(links) >= max_topics:
                            break
            
            logger.info(f"✓ Found {len(links)} WHO fact sheet links")
            return links if not max_topics else links[:max_topics]
            
        except Exception as e:
            logger.error(f"✗ Failed to get WHO fact sheet links: {e}")
            return []
    
    def scrape_who_fact_sheet(self, url: str, title: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single WHO fact sheet page with section extraction
        
        Args:
            url: URL of the fact sheet
            title: Title of the fact sheet
            
        Returns:
            Dict with scraped content including sections
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()
            
            # Extract main content
            content_selectors = [
                'article',
                'main',
                '.sf-content-block',
                '.detail-page',
                '#PageContent',
                '.page-content'
            ]
            
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                content_div = soup.find('body')
            
            # Extract content with section information
            sections = []
            current_section = None
            current_content = []
            
            if content_div:
                for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'div']):
                    text = element.get_text(separator=' ', strip=True)
                    
                    # Check if it's a heading (new section)
                    if element.name in ['h2', 'h3', 'h4']:
                        # Save previous section if exists
                        if current_section and current_content:
                            section_text = '\n\n'.join(current_content)
                            if len(section_text) > 30:
                                sections.append({
                                    'section': current_section,
                                    'content': section_text
                                })
                        
                        # Start new section
                        current_section = text if text else "General"
                        current_content = []
                    
                    # Add content to current section (only if we have a section)
                    elif current_section and len(text) > 30 and not text.startswith('http'):
                        current_content.append(text)
                
                # Save last section
                if current_section and current_content:
                    section_text = '\n\n'.join(current_content)
                    if len(section_text) > 30:
                        sections.append({
                            'section': current_section,
                            'content': section_text
                        })
            
            if not sections:
                logger.warning(f"⚠ No sections found for: {title}")
                return None
            
            # Combine all content
            full_text = '\n\n'.join([s['content'] for s in sections])
            
            if len(full_text) < 100:
                logger.warning(f"⚠ Content too short for: {title}")
                return None
            
            logger.info(f"✓ Scraped: {title} ({len(sections)} sections, {len(full_text)} chars)")
            
            return {
                'url': url,
                'title': title,
                'content': full_text,
                'sections': sections,  # Include section information
                'source': 'WHO'
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to scrape {url}: {e}")
            return None
    



def scrape_who_fact_sheets(max_topics: int = None, delay: float = 3.0) -> List[Dict[str, str]]:
    """
    Main function to scrape WHO fact sheets
    
    Args:
        max_topics: Maximum number of topics to scrape (None = scrape all)
        delay: Delay between requests (be polite to WHO servers)
        
    Returns:
        List of scraped fact sheets
    """
    scraper = MedicalScraper()
    
    logger.info("\n" + "="*60)
    logger.info("SCRAPING WHO FACT SHEETS")
    logger.info("="*60)
    
    # Step 1: Get all fact sheet links
    logger.info("\n[1/2] Getting fact sheet links...")
    fact_sheets = scraper.get_who_fact_sheet_links(max_topics=max_topics)
    
    if not fact_sheets:
        logger.error("✗ No fact sheets found")
        return []
    
    # Step 2: Scrape each fact sheet
    logger.info(f"\n[2/2] Scraping {len(fact_sheets)} fact sheets...")
    results = []
    
    for i, sheet in enumerate(fact_sheets):
        logger.info(f"\nScraping {i+1}/{len(fact_sheets)}: {sheet['title']}")
        
        result = scraper.scrape_who_fact_sheet(sheet['url'], sheet['title'])
        
        if result:
            # Add topic categorization (simple keyword-based for MVP)
            result['topic'] = categorize_topic(sheet['title'])
            results.append(result)
        
        # Be polite - delay between requests
        if i < len(fact_sheets) - 1:
            time.sleep(delay)
    
    logger.info(f"\n✓ Successfully scraped {len(results)} fact sheets")
    return results


def categorize_topic(title: str) -> str:
    """Categorize health topic based on title keywords"""
    title_lower = title.lower()
    
    # Define categories
    categories = {
        'diabetes': ['diabetes', 'blood sugar', 'insulin'],
        'cardiovascular': ['heart', 'cardiovascular', 'hypertension', 'blood pressure', 'stroke'],
        'respiratory': ['asthma', 'copd', 'pneumonia', 'tuberculosis', 'respiratory'],
        'infectious': ['covid', 'malaria', 'hiv', 'aids', 'hepatitis', 'measles', 'influenza'],
        'mental_health': ['mental', 'depression', 'anxiety', 'suicide', 'dementia'],
        'cancer': ['cancer', 'tumor', 'malignant'],
        'nutrition': ['obesity', 'malnutrition', 'diet', 'nutrition'],
        'maternal': ['pregnancy', 'maternal', 'abortion', 'contraception'],
        'general': []
    }
    
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    
    return 'general'


def scrape_medical_data(max_topics: int = None) -> List[Dict[str, str]]:
    """
    Main function to scrape WHO fact sheets
    
    Args:
        max_topics: Maximum WHO topics to scrape (None = scrape all)
        
    Returns:
        List of scraped WHO fact sheets
    """
    # Scrape WHO fact sheets only
    results = scrape_who_fact_sheets(max_topics=max_topics)
    
    logger.info(f"\n✓ Total articles scraped: {len(results)}")
    return results


if __name__ == "__main__":
    results = scrape_medical_data(use_who=True, max_who_topics=20)
    
    # Print summary
    for result in results:
        print(f"\nTitle: {result['title']}")
        print(f"Topic: {result.get('topic', 'N/A')}")
        print(f"URL: {result['url']}")
        print(f"Content length: {len(result['content'])} characters")
max