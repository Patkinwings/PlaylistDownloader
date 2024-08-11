from abc import ABC, abstractmethod
from typing import List, Dict

class MusicService(ABC):
    @abstractmethod
    async def get_playlists(self) -> List[Dict]:
        """
        Retrieve a list of playlists for the authenticated user.
        
        Returns:
            A list of dictionaries, each containing 'id' and 'name' of a playlist.
        """
        pass

    @abstractmethod
    async def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """
        Retrieve a list of track names for a given playlist.
        
        Args:
            playlist_id (str): The ID of the playlist to retrieve tracks from.
        
        Returns:
            A list of track names.
        """
        pass