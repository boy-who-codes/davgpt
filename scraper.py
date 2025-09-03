import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
import urllib3
import os
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DAVScraper:
    def __init__(self):
        self.base_url = os.getenv('WEBSITE_URL', 'http://davkoylanagar.com/')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.scraped_urls = set()
        self.all_data = []
    
    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s.,!?()-]', '', text)
        return text
    
    def extract_links(self, soup, base_url):
        """Extract all internal links from the page"""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include internal links
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)
        
        return links
    
    def scrape_page_comprehensive(self, url, category="general"):
        """Comprehensive page scraping with deep content extraction"""
        if url in self.scraped_urls:
            return None
            
        try:
            print(f"🕷️ Scraping: {url}")
            self.scraped_urls.add(url)
            
            response = requests.get(url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']):
                element.decompose()
            
            # Extract title
            title_elem = soup.find('title')
            title = self.clean_text(title_elem.get_text()) if title_elem else "DAV Koyla Nagar"
            
            # Extract all meaningful content
            content_parts = []
            
            # Get headings (important content)
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = heading.get_text(strip=True)
                if text and len(text) > 3:
                    content_parts.append(f"HEADING: {self.clean_text(text)}")
            
            # Get paragraphs
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(self.clean_text(text))
            
            # Get list items
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(f"• {self.clean_text(text)}")
            
            # Get table data
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if any(cell for cell in cells):
                        content_parts.append(" | ".join(cells))
            
            # Get div content (fallback)
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 500:
                    content_parts.append(self.clean_text(text))
            
            # Join all content
            content = ' '.join(content_parts)
            
            # If still no content, get body text
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    content = self.clean_text(body.get_text(separator=' ', strip=True))
            
            # Extract internal links for further scraping
            internal_links = self.extract_links(soup, url)
            
            if content and len(content) > 50:
                page_data = {
                    'url': url,
                    'title': title,
                    'content': content[:3000],  # Increased limit
                    'category': category,
                    'scraped_at': datetime.now().isoformat(),
                    'internal_links': list(internal_links)
                }
                
                self.all_data.append(page_data)
                return page_data, internal_links
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
        
        return None, set()
    
    def scrape_all_comprehensive(self):
        """Comprehensive scraping of entire website"""
        print(f"🚀 Starting comprehensive scrape of {self.base_url}")
        
        # Start with main page
        main_data, main_links = self.scrape_page_comprehensive(self.base_url, 'home')
        
        # Queue of URLs to scrape
        urls_to_scrape = list(main_links) if main_links else []
        
        # Common page patterns to try
        common_pages = [
            'about', 'about-us', 'admission', 'admissions', 'fees', 'fee-structure',
            'contact', 'contact-us', 'facilities', 'academics', 'events', 'news',
            'notices', 'gallery', 'staff', 'faculty', 'principal', 'timings',
            'curriculum', 'infrastructure', 'activities', 'sports', 'library'
        ]
        
        for page in common_pages:
            urls_to_scrape.append(f"{self.base_url.rstrip('/')}/{page}")
            urls_to_scrape.append(f"{self.base_url.rstrip('/')}/{page}.html")
        
        # Scrape all discovered URLs
        scraped_count = 0
        for url in urls_to_scrape[:50]:  # Limit to prevent infinite scraping
            if url not in self.scraped_urls:
                data, new_links = self.scrape_page_comprehensive(url)
                if data:
                    scraped_count += 1
                    # Add newly discovered links
                    for new_link in new_links:
                        if new_link not in urls_to_scrape and len(urls_to_scrape) < 100:
                            urls_to_scrape.append(new_link)
                
                time.sleep(0.5)  # Be respectful
        
        # Remove duplicates and save
        unique_data = []
        seen_content = set()
        
        for item in self.all_data:
            content_hash = hash(item['content'][:200])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_data.append(item)
        
        # Save to file
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(unique_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Scraped {scraped_count} pages, saved {len(unique_data)} unique entries")
        return len(unique_data) > 0
    
    def scrape_all(self):
        """Main scraping method"""
        return self.scrape_all_comprehensive()
    
    def get_scraped_data(self):
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
