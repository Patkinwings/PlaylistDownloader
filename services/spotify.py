import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .base import MusicService
from typing import List, Dict
import logging
import time
from youtubesearchpython import VideosSearch

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
class SpotifyService(MusicService):
    def __init__(self, config: Dict):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri'],
            scope='playlist-read-private'
        ))

    async def get_playlists(self) -> List[Dict]:
        playlists = self.sp.current_user_playlists()
        return [{'id': p['id'], 'name': p['name']} for p in playlists['items']]

    async def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        tracks = []
        offset = 0
        limit = 100  # Spotify's maximum limit per request

        while len(tracks) < 1000:
            results = self.sp.playlist_tracks(playlist_id, offset=offset, limit=limit)
            new_tracks = [
                {
                    'name': track['track']['name'],
                    'artists': ', '.join([artist['name'] for artist in track['track']['artists']])
                }
                for track in results['items']
                if track['track']
            ]
            tracks.extend(new_tracks)

            if len(new_tracks) < limit:
                # We've reached the end of the playlist
                break

            offset += limit

        logger.info(f"Fetching YouTube URLs for {len(tracks)} tracks...")
        # Find YouTube URLs for each track
        for i, track in enumerate(tracks[:1000]):
            query = f"{track['name']} {track['artists']}"
            youtube_url = search_youtube(query)
            track['youtube_url'] = youtube_url
            time.sleep(1)  # Add a 1-second delay between searches
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1} tracks")

        return tracks[:1000]  # Limit to 1000 tracks maximum

def test_youtube_search():
    test_query = "Metallica Enter Sandman"
    result = search_youtube(test_query)
    print(f"Test query: {test_query}")
    print(f"Test result: {result}")

if __name__ == "__main__":
    test_youtube_search()