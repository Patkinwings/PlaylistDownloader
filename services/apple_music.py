import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import json
import re
import time
import asyncio
from youtubesearchpython import VideosSearch
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def search_youtube(query: str) -> str:
    try:
        videosSearch = VideosSearch(query, limit=1)
        results = videosSearch.result()
        
        if results and results['result']:
            return results['result'][0]['link']
        else:
            logger.warning(f"No video link found for query: {query}")
            return "No YouTube URL found"
    except Exception as e:
        logger.error(f"Error searching YouTube for query '{query}': {str(e)}")
        return f"Error searching YouTube: {str(e)}"

class AppleMusicService:
    def __init__(self, config: Dict = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.config = config or {}

    async def get_playlists(self) -> List[Dict]:
        logger.info("Apple Music doesn't support listing public playlists.")
        return []

    async def get_playlist_tracks(self, playlist_url: str) -> List[Dict]:
        try:
            # Use Selenium to interact with the dynamic playlist page
            driver = webdriver.Chrome()
            driver.get(playlist_url)

            # Wait for the page to load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[property="music:song"]')))

            # Extract the track information from the dynamically loaded content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            tracks = []
            song_metas = soup.find_all('meta', property='music:song')
            
            for song_meta in song_metas:
                song_url = song_meta['content']
                song_name_meta = soup.find('meta', property=f'music:song:preview_url:secure_url', content=song_url)
                if song_name_meta:
                    track_number_meta = soup.find('meta', property='music:song:track', content=song_name_meta.find_next('meta', property='music:song:track')['content'])
                    track_name = song_url.split('/')[-2].replace('-', ' ').title()
                    
                    # Extract artist names from the song URL
                    artists = [name.title() for name in song_url.split('/')[3].split('-')]
                    
                    tracks.append({
                        'name': track_name,
                        'artists': ', '.join(artists),
                        'track_number': track_number_meta['content'] if track_number_meta else 'Unknown'
                    })
            
            logger.debug(f"Number of tracks found: {len(tracks)}")
            
            logger.info(f"Fetching YouTube URLs for {len(tracks)} tracks...")
            # Find YouTube URLs for each track
            for i, track in enumerate(tracks[:1000]):
                query = f"{track['name']} {track['artists']}"
                youtube_url = await search_youtube(query)
                track['youtube_url'] = youtube_url
                await asyncio.sleep(1)  # Add a 1-second delay between searches
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} tracks")

            # Navigate to the specific website
            website_url = "https://ytmp3s.nu/D9K1/"
            driver.get(website_url)

            # Find the input field and send the YouTube URL
            url_input = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "url"))
            )
            url_input.send_keys(tracks[0]['youtube_url'])

            # Find the submit button and click it
            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click()

            # Wait for the download button to appear and click it
            try:
                # Wait for some time to ensure the page has loaded
                time.sleep(10)
                
                # Try to find the download button
                download_button = WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[text()='Download']"))
                )
                
                # Get the href attribute
                download_url = download_button.get_attribute('href')
                
                # Print the download URL (optional, for debugging)
                print(f"Download URL: {download_url}")
                
                # Click the download button
                download_button.click()
                logger.info(f"Download initiated for: {tracks[0]['name']}")

            except Exception as e:
                logger.error(f"Failed to initiate download for: {tracks[0]['name']}. Error: {str(e)}")

            # Close the Selenium driver
            driver.quit()
            
            return tracks[:1000]  # Limit to 1000 tracks maximum
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {str(e)}")
            logger.exception(e)
            return []

__all__ = ['AppleMusicService']