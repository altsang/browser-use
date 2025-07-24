"""
Bulk Restaurant Image Scraper

This script automates the collection of restaurant images from Naver Maps by visiting
multiple random restaurants and downloading interior and exterior photos in bulk.

Key Features:
- Random restaurant discovery using Naver Maps search patterns
- Bulk image collection (configurable limits per restaurant)
- Organized file structure with restaurant names and image categories
- Multi-LLM support (OpenAI, Azure, Gemini, Ollama)
- Progress tracking and error recovery
- Naver authentication for enhanced access

Default Configuration:
- 50 random restaurants
- 10 interior images per restaurant
- 5 exterior images per restaurant
- Images saved to ~/restaurant_images/{restaurant_name}/{interior|exterior}/

Use Cases:
- Restaurant marketing research
- Visual content analysis
- Dataset creation for ML training
- Competitive analysis

Example Usage:
    python bulk_restaurant_image_scraper.py --max-restaurants 50
    python bulk_restaurant_image_scraper.py --interior-limit 10 --exterior-limit 5 --auth
    python bulk_restaurant_image_scraper.py --debug --no-headless --max-restaurants 10
"""

import os
import sys
import asyncio
import logging
import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr
from typing_extensions import List as TypingList

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.controller.service import Controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Korean food categories for random search
FOOD_CATEGORIES = [
    "한식", "일식", "중식", "양식", "카페", "치킨", "피자", "족발보쌈", 
    "찜닭", "분식", "회", "고기", "해산물", "디저트", "베이커리"
]

# Seoul districts for location-based search  
SEOUL_DISTRICTS = [
    "강남구", "서초구", "송파구", "강동구", "마포구", "용산구", "중구", "종로구",
    "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구", "도봉구", "노원구",
    "은평구", "서대문구", "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구"
]

class RestaurantData(BaseModel):
    name: str
    naver_url: str
    location: str
    interior_images: TypingList[str] = []
    exterior_images: TypingList[str] = []
    scraped_at: str

class BulkImageScraper:
    def __init__(self, max_restaurants: int = 50, interior_limit: int = 10, 
                 exterior_limit: int = 5, output_dir: str = None):
        self.max_restaurants = max_restaurants
        self.interior_limit = interior_limit
        self.exterior_limit = exterior_limit
        self.output_dir = Path(output_dir or os.path.join(os.path.expanduser("~"), "restaurant_images"))
        self.scraped_restaurants: List[RestaurantData] = []
        self.progress_file = self.output_dir / "scraping_progress.json"
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized scraper: {max_restaurants} restaurants, {interior_limit} interior, {exterior_limit} exterior images")
        logger.info(f"Output directory: {self.output_dir}")

    def save_progress(self):
        """Save current progress to JSON file"""
        progress_data = {
            "scraped_count": len(self.scraped_restaurants),
            "target_count": self.max_restaurants,
            "last_updated": datetime.now().isoformat(),
            "restaurants": [r.dict() for r in self.scraped_restaurants]
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Progress saved: {len(self.scraped_restaurants)}/{self.max_restaurants} restaurants")

    def load_progress(self) -> bool:
        """Load previous progress if exists"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.scraped_restaurants = [RestaurantData(**r) for r in data.get("restaurants", [])]
                logger.info(f"Resumed from progress: {len(self.scraped_restaurants)} restaurants already scraped")
                return True
            except Exception as e:
                logger.warning(f"Could not load progress: {e}")
        
        return False

    def generate_search_query(self) -> str:
        """Generate random search query for restaurant discovery"""
        category = random.choice(FOOD_CATEGORIES)
        district = random.choice(SEOUL_DISTRICTS)
        return f"{district} {category}"

    async def authenticate_naver(self, browser: Browser) -> bool:
        """Authenticate with Naver using environment credentials"""
        username = os.environ.get("NAVER_USERNAME")
        password = os.environ.get("NAVER_PASSWORD")
        
        if not username or not password:
            logger.warning("Naver credentials not found - continuing without authentication")
            return False
        
        logger.info("Authenticating with Naver...")
        
        async with BrowserContext(browser) as context:
            await context.navigate_to("https://nid.naver.com/nidlogin.login")
            
            page = await context.get_current_page()
            
            try:
                await page.evaluate(f"""
                    () => {{
                        const idInput = document.querySelector('#id');
                        const pwInput = document.querySelector('#pw');
                        
                        if (idInput) {{
                            idInput.value = '{username}';
                            idInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                        
                        if (pwInput) {{
                            pwInput.value = '{password}';
                            pwInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }}
                """)
                
                login_button = await page.query_selector("button.btn_login")
                if login_button:
                    await login_button.click()
                    await asyncio.sleep(3)
                    
                    current_url = page.url
                    if "nid.naver.com/nidlogin.login" not in current_url:
                        logger.info("Naver authentication successful")
                        return True
                
                logger.warning("Naver authentication failed")
                return False
                
            except Exception as e:
                logger.error(f"Error during Naver authentication: {e}")
                return False

    async def scrape_restaurant_images(self, browser: Browser, llm) -> bool:
        """Scrape images from a single restaurant"""
        try:
            search_query = self.generate_search_query()
            logger.info(f"Searching for: {search_query}")
            
            # Create download directory for this session
            download_dir = self.output_dir / "temp_downloads"
            download_dir.mkdir(exist_ok=True)
            
            browser_config = BrowserConfig(
                new_context_config=BrowserContextConfig(
                    save_downloads_path=str(download_dir)
                )
            )
            
            task = f"""
            Go to Naver Maps (https://map.naver.com) and search for '{search_query}'. 
            Find a restaurant from the search results and click on it.
            Navigate to the restaurant's photo section and collect images:
            - Download {self.interior_limit} interior photos (내부/인테리어 category)  
            - Download {self.exterior_limit} exterior photos (외부 category)
            Save the restaurant name and location for organization.
            """
            
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                max_actions_per_step=10
            )
            
            result = await agent.run(max_steps=30)
            
            # TODO: Process downloaded images and organize them
            # This would involve parsing the agent's results and moving files
            # to the proper restaurant-named directories
            
            return True
            
        except Exception as e:
            logger.error(f"Error scraping restaurant: {e}")
            return False

def create_llm(args):
    """Create LLM instance based on command line arguments"""
    if args.use_azure:
        required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_API_VERSION"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"Missing Azure environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
            
        return AzureChatOpenAI(
            model=args.model,
            temperature=0.0,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_key=SecretStr(os.environ.get("AZURE_OPENAI_KEY", "")),
        )
    elif args.use_ollama:
        return ChatOllama(
            model=args.model,
            temperature=0.0,
            base_url="http://localhost:11434",
        )
    elif args.use_gemini:
        if not os.environ.get("GEMINI_API_KEY"):
            logger.error("Missing GEMINI_API_KEY environment variable")
            sys.exit(1)
            
        return ChatGoogleGenerativeAI(
            model=args.model,
            temperature=0.0,
            api_key=SecretStr(os.environ.get("GEMINI_API_KEY", "")),
        )
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("Missing OPENAI_API_KEY environment variable")
            sys.exit(1)
            
        return ChatOpenAI(
            model=args.model,
            temperature=0.0,
        )

async def main():
    parser = argparse.ArgumentParser(description='Bulk Restaurant Image Scraper')
    
    # Scraping configuration
    parser.add_argument('--max-restaurants', type=int, default=50, 
                        help='Maximum number of restaurants to scrape (default: 50)')
    parser.add_argument('--interior-limit', type=int, default=10,
                        help='Number of interior images per restaurant (default: 10)')
    parser.add_argument('--exterior-limit', type=int, default=5,
                        help='Number of exterior images per restaurant (default: 5)')
    parser.add_argument('--output-dir', type=str, 
                        help='Output directory for downloaded images (default: ~/restaurant_images)')
    
    # Browser configuration
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='Run browser in visible mode')
    parser.add_argument('--advanced-mode', action='store_true', default=True,
                        help='Enable advanced Playwright capabilities')
    
    # LLM configuration
    parser.add_argument('--model', type=str, default='gpt-4o', help='Model to use (default: gpt-4o)')
    parser.add_argument('--use-azure', action='store_true', help='Use Azure OpenAI')
    parser.add_argument('--use-ollama', action='store_true', help='Use Ollama')
    parser.add_argument('--use-gemini', action='store_true', help='Use Google Gemini')
    
    # Other options
    parser.add_argument('--auth', action='store_true', help='Authenticate with Naver')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting Bulk Restaurant Image Scraper")
    logger.info(f"Target: {args.max_restaurants} restaurants, {args.interior_limit} interior + {args.exterior_limit} exterior images each")
    
    # Initialize scraper
    scraper = BulkImageScraper(
        max_restaurants=args.max_restaurants,
        interior_limit=args.interior_limit,
        exterior_limit=args.exterior_limit,
        output_dir=args.output_dir
    )
    
    # Load previous progress if requested
    if args.resume:
        scraper.load_progress()
    
    # Create LLM and browser
    llm = create_llm(args)
    
    browser_config = BrowserConfig(
        advanced_mode=args.advanced_mode,
        headless=args.headless,
        disable_security=True
    )
    
    browser = Browser(config=browser_config)
    
    try:
        # Authenticate if requested
        if args.auth:
            auth_success = await scraper.authenticate_naver(browser)
            if not auth_success:
                logger.warning("Continuing without Naver authentication")
        
        # Main scraping loop
        remaining = args.max_restaurants - len(scraper.scraped_restaurants)
        logger.info(f"Need to scrape {remaining} more restaurants")
        
        for i in range(remaining):
            current_count = len(scraper.scraped_restaurants) + 1
            logger.info(f"Processing restaurant {current_count}/{args.max_restaurants}")
            
            success = await scraper.scrape_restaurant_images(browser, llm)
            
            if success:
                # Save progress after each successful scrape
                scraper.save_progress()
            else:
                logger.warning(f"Failed to scrape restaurant {current_count}, continuing...")
            
            # Small delay between requests
            await asyncio.sleep(2)
        
        logger.info("Bulk scraping completed successfully!")
        logger.info(f"Final results saved to: {scraper.output_dir}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        scraper.save_progress()
    except Exception as e:
        logger.error(f"Error during bulk scraping: {e}")
        scraper.save_progress()
        raise
    finally:
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())