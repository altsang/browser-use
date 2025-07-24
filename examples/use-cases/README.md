# Use Cases of Browser-Use

| File Name | Description |
|-----------|------------|
| `bulk_restaurant_image_scraper.py` | **NEW** - Bulk collection of restaurant images from 50 random Naver Maps restaurants (10 interior + 5 exterior each). |
| `captcha.py` | Automates CAPTCHA solving on a demo website. |  
| `check_appointment.py` | Checks for available visa appointment slots on the Greece MFA website. |
| `find_and_apply_to_jobs.py` | Searches for job listings, evaluates relevance based on a CV, and applies automatically. |
| `online_coding_agent.py` | Implements a multi-agent system for online code editors, with separate agents for coding and execution. |
| `post-twitter.py` | Provides a template for automated posting on X (Twitter), including new tweets, tagging, and replies. |
| `restaurant_standee_detection.py` | **RENAMED** - Advanced standee detection in Korean restaurant photos using YOLO-based computer vision and Naver Maps navigation. |
| `scrolling_page.py` | Automates webpage scrolling with various scrolling actions and text search functionality. |
| `twitter_post_using_cookies.py` | Automates posting on X (Twitter) using stored authentication cookies. |
| `web_voyager_agent.py` | A general-purpose web navigation agent for tasks like flight booking and course searching. |

## 🍽️ Restaurant Automation Scripts

### restaurant_standee_detection.py
**Purpose**: Automated standee detection in Korean restaurant photos using computer vision.

**Example Usage**:
```bash
# Basic standee detection with screenshots
python restaurant_standee_detection.py --no-headless --screenshots --auth

# Using different LLM providers
python restaurant_standee_detection.py --use-azure --model gpt-4o
python restaurant_standee_detection.py --use-gemini --model gemini-2.0-flash-exp
```

### bulk_restaurant_image_scraper.py  
**Purpose**: Bulk collection of restaurant images from random Naver Maps restaurants.

**Example Usage**:
```bash
# Default: 50 restaurants, 10 interior + 5 exterior images each
python bulk_restaurant_image_scraper.py --auth

# Custom configuration
python bulk_restaurant_image_scraper.py --max-restaurants 20 --interior-limit 5 --exterior-limit 3

# Resume interrupted session
python bulk_restaurant_image_scraper.py --resume --debug
```

Both scripts require Korean language support and work specifically with Naver Maps. Set `NAVER_USERNAME` and `NAVER_PASSWORD` environment variables for authenticated access.
