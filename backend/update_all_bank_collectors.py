"""
Script to update all bank option chain collectors with Redis expiry caching
This script applies the same Redis caching pattern to all bank collectors
"""

import re
import os

# List of all bank collectors (excluding indices which are already done)
banks = [
    'icicibank', 'sbin', 'kotakbank', 'axisbank', 
    'bankbaroda', 'pnb', 'canbk', 'aubank', 'indusindbk', 
    'idfcfirstb', 'federalbnk'
]

def update_collector(bank_name):
    """Update a single bank collector with Redis caching"""
    filename = f'nse_{bank_name}_option_chain_collector.py'
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'from redis_expiry_cache import get_expiry_cache' in content:
            print(f"✅ {filename} already has Redis caching")
            return True
        
        # 1. Add import
        if 'from dotenv import load_dotenv' in content:
            content = content.replace(
                'from dotenv import load_dotenv',
                'from dotenv import load_dotenv\nfrom redis_expiry_cache import get_expiry_cache'
            )
        
        # 2. Add expiry_cache to __init__
        if 'self.collection = None' in content and 'self.expiry_cache' not in content:
            content = content.replace(
                '        self.collection = None\n        self._connect_mongo()',
                '        self.collection = None\n        self.expiry_cache = get_expiry_cache()\n        self._connect_mongo()'
            )
        
        # 3. Update _fetch_expiry_dates_with_retry method
        pattern = r'(def _fetch_expiry_dates_with_retry\(self\) -> Optional\[str\]:.*?Returns: First expiry date string.*?\n        )'
        
        new_method = '''def _fetch_expiry_dates_with_retry(self) -> Optional[str]:
        """
        Fetch expiry dates from NSE API with retry logic
        First checks Redis cache, then fetches from API if not cached
        Returns: First expiry date string (e.g., "25-Nov-2025") or None if all retries fail
        """
        # First, try to get from Redis cache
        cached_expiry = self.expiry_cache.get_expiry(SYMBOL)
        if cached_expiry:
            logger.info(f"Using cached {SYMBOL} expiry date: {cached_expiry}")
            return cached_expiry
        
        # If not in cache, fetch from API
        logger.info(f"{SYMBOL} expiry date not found in cache, fetching from API...")
        headers = self._get_headers()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching expiry dates for {SYMBOL} from API (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(EXPIRY_API_URL, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract expiry dates
                expiry_dates = data.get("expiryDates", [])
                
                if not expiry_dates or not isinstance(expiry_dates, list):
                    logger.error(f"Unexpected expiry dates format: {type(expiry_dates)}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                if len(expiry_dates) == 0:
                    logger.error("No expiry dates found in response")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Always pick the first expiry date
                first_expiry = expiry_dates[0]
                logger.info(f"Successfully fetched {SYMBOL} expiry dates. Using first expiry: {first_expiry}")
                
                # Cache the expiry date for today
                try:
                    self.expiry_cache.set_expiry(SYMBOL, first_expiry)
                    logger.info(f"Cached {SYMBOL} expiry date: {first_expiry}")
                except Exception as cache_error:
                    logger.warning(f"Failed to cache expiry date: {str(cache_error)}")
                    # Continue even if caching fails
                
                return first_expiry
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {SYMBOL} expiry dates")
                    
            except Exception as e:
                logger.error(f"Unexpected error (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {SYMBOL} expiry dates")
        
        return None
        '''
        
        # Find and replace the entire method
        old_method_pattern = r'def _fetch_expiry_dates_with_retry\(self\) -> Optional\[str\]:.*?return None\n    '
        content = re.sub(old_method_pattern, new_method + '    ', content, flags=re.DOTALL)
        
        # 4. Add get_current_expiry method before close()
        if 'def get_current_expiry(self)' not in content:
            get_expiry_method = '''    def get_current_expiry(self) -> Optional[str]:
        """
        Get current expiry date from cache or API
        Returns: Expiry date string or None
        """
        # Try cache first
        cached_expiry = self.expiry_cache.get_expiry(SYMBOL)
        if cached_expiry:
            return cached_expiry
        
        # If not in cache, try to fetch (this will cache it)
        return self._fetch_expiry_dates_with_retry()
    
    '''
            content = content.replace(
                '    def close(self):',
                get_expiry_method + '    def close(self):'
            )
        
        # Write back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {filename}: {str(e)}")
        return False

if __name__ == '__main__':
    print("Updating all bank collectors with Redis expiry caching...\n")
    success_count = 0
    for bank in banks:
        if update_collector(bank):
            success_count += 1
    
    print(f"\n✅ Successfully updated {success_count}/{len(banks)} bank collectors")

