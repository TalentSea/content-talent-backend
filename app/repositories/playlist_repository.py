from typing import List, Tuple, Optional

class PlaylistRepository:
    """
    Data access layer for performing CRUD operations on Playlist Peewee entities.
    """

    def create_playlist(self, playlist_data: dict, user_id: int):
        """
        Commits a new Playlist record into DB and attaches initial video IDs in junction table.
        """
        pass

    def get_playlist_by_id(self, playlist_id: int, user_id: int, page: int = 1, limit: int = 20) -> Tuple[Optional[object], List, int]:
        """
        Retrieves a playlist by ID ensuring ownership check along with paginated attached videos and total count.
        """
        pass

    def get_all_playlists_by_user(self, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List, int]:
        """
        Fetches a paginated list of playlists created by user_id along with total count using Peewee paginate().
        """
        pass

    def update_playlist(self, playlist_id: int, user_id: int, update_data: dict):
        """
        Updates playlist textual metadata (name, description) and replaces attached video associations.
        """
        pass

    def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        """
        Deletes a playlist record from DB and clears junction table links.
        """
        pass

    def get_available_videos_for_playlist(self, playlist_id: int, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List, int]:
        """
        Executes Peewee query returning paginated list of creator videos NOT attached to the specified playlist.
        """
        pass
