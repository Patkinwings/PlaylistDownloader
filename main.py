import asyncio
import yaml
import click
from typing import Dict, List
from services.spotify import SpotifyService
from services.apple_music import AppleMusicService
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.apple_music_scraper import AppleMusicService
import time

def load_config() -> Dict:
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def get_service(service_name: str, config: Dict):
    if service_name == 'spotify':
        return SpotifyService(config['spotify'])
    elif service_name == 'apple_music':
        # Pass an empty dict if 'apple_music' config is not available
        return AppleMusicService(config.get('apple_music', {}))
    else:
        raise ValueError(f"Unknown service: {service_name}")

async def display_playlists(playlists: List[Dict]):
    for i, playlist in enumerate(playlists, 1):
        click.echo(f"{i}. {playlist['name']}")

async def display_tracks(tracks: List[Dict]):
    for i, track in enumerate(tracks, 1):
        youtube_url = track.get('youtube_url', 'No YouTube URL')
        click.echo(f"{i}. {track['name']} - {track['artists']} | YouTube: {youtube_url}")

async def run():
    config = load_config()
    service_name = click.prompt('Select music service', type=click.Choice(['spotify', 'apple_music']))
    
    try:
        music_service = get_service(service_name, config)
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        return

    try:
        if service_name == 'spotify':
            playlists = await music_service.get_playlists()
            await display_playlists(playlists)

            playlist_index = click.prompt('Select a playlist by number', type=int) - 1
            if playlist_index < 0 or playlist_index >= len(playlists):
                click.echo("Invalid playlist number.")
                return

            playlist_id = playlists[playlist_index]['id']
            tracks = await music_service.get_playlist_tracks(playlist_id)
        
        elif service_name == 'apple_music':
            playlist_url = click.prompt('Enter the Apple Music playlist URL')
            tracks = await music_service.get_playlist_tracks(playlist_url)
        
        click.echo("\nTracks in the selected playlist:")
        await display_tracks(tracks)

        # Interact with the website using Selenium
        driver = webdriver.Chrome()
        for track in tracks:
            youtube_url = track.get('youtube_url')
            if not youtube_url:
                click.echo(f"Skipping track '{track['name']}' - No YouTube URL available")
                continue

            # Navigate to the specific website
            website_url = "https://ytmp3s.nu/D9K1/"
            driver.get(website_url)

            # Store the original window handle
            original_window = driver.current_window_handle

            # Wait for the input field to be present and interact with it
            url_input = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "url"))
            )
            url_input.send_keys(youtube_url)

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
                click.echo(f"Download initiated for: {track['name']}")

                # Wait for the new tab to open
                WebDriverWait(driver, 2).until(EC.number_of_windows_to_be(2))

                # Switch to the new window
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                        break

                # Close the new tab
                driver.close()

                # Switch back to the original window
                driver.switch_to.window(original_window)

            except Exception as e:
                click.echo(f"Failed to initiate download for: {track['name']}. Error: {str(e)}")

            # Add a delay before the next iteration to avoid overwhelming the website
            time.sleep(5)

        # Close the webdriver
        driver.quit()
    
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")
        click.echo(f"Error details: {type(e).__name__}: {str(e)}")

if __name__ == '__main__':
    asyncio.run(run())

    