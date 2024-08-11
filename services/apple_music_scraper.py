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

async def search_youtube(track_name: str, artist_name: str, playlist_name: str) -> str:
    try:
        query = f"{track_name} {artist_name} {playlist_name}"
        
        videosSearch = VideosSearch(query, limit=10)
        results = videosSearch.result()
        
        if results and results['result']:
            # Find the video with the highest view count
            best_match = max(results['result'], key=lambda x: int(x.get('viewCount', {'text': '0'})['text'].replace(',', '').split()[0]))
            
            if best_match:
                view_count = best_match.get('viewCount', {'text': 'Unknown'})['text']
                print(f"Searching YouTube for: {query}")
                print(f"Using video: {best_match['title']} (view count: {view_count})")
                return best_match['link']
            else:
                logger.warning(f"No video link found for query: {query}")
                return "No YouTube URL found"
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
            driver = webdriver.Chrome()
            driver.get(playlist_url)

            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.songs-list-row')))

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            playlist_element = soup.select_one('h1.headings__title')
            playlist_name = playlist_element.text.strip() if playlist_element else 'Unknown Playlist'

            curator_element = soup.select_one('.headings__subtitles a[data-testid="click-action"]')
            curator_name = curator_element.text.strip() if curator_element else 'Unknown Curator'

            tracks = []
            for track_element in soup.select('.songs-list-row'):
                track_name_element = track_element.select_one('.songs-list-row__song-name')
                track_name = track_name_element.text.strip() if track_name_element else 'Unknown Track'

                artist_element = track_element.select_one('.songs-list__col--secondary a')
                artist_name = artist_element.text.strip() if artist_element else 'Unknown Artist'

                track_number_element = track_element.select_one('.songs-list-row__rank')
                track_number = track_number_element.text.strip() if track_number_element else 'Unknown'

                tracks.append({
                    'name': track_name,
                    'artists': artist_name,
                    'playlist_name': playlist_name,
                    'curator_name': curator_name,
                    'track_number': track_number
                })

            logger.debug(f"Number of tracks found: {len(tracks)}")

            logger.info(f"Fetching YouTube URLs for {len(tracks)} tracks...")
            for i, track in enumerate(tracks[:1000]):
                youtube_url = await search_youtube(track['name'], track['artists'], track['playlist_name'])
                track['youtube_url'] = youtube_url
                await asyncio.sleep(1)
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} tracks")

            website_url = "https://ytmp3s.nu/D9K1/"
            driver.get(website_url)

            url_input = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "url"))
            )
            url_input.send_keys(tracks[0]['youtube_url'])

            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click()

            try:
                time.sleep(10)

                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.download-button"))
                )

                download_url = download_button.get_attribute('href')

                print(f"Download URL: {download_url}")

                download_button.click()
                logger.info(f"Download initiated for: {tracks[0]['name']} by {tracks[0]['artists']} from the '{tracks[0]['playlist_name']}' playlist")

            except Exception as e:
                logger.error(f"Failed to initiate download for: {tracks[0]['name']}. Error: {str(e)}")
                logger.debug(f"Page source: {driver.page_source}")

            driver.quit()

            return tracks[:1000]
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {str(e)}")
            logger.exception(e)
            return []

if __name__ == "__main__":
    async def main():
        service = AppleMusicService()
        playlist_url = "https://music.apple.com/us/playlist/your-playlist-url-here"
        tracks = await service.get_playlist_tracks(playlist_url)
        print(f"Tracks in the selected playlist: {len(tracks)}")
        for track in tracks[:5]:  # Print first 5 tracks as an example
            print(f"{track['name']} by {track['artists']} - YouTube URL: {track['youtube_url']}")

    asyncio.run(main())