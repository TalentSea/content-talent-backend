from typing import List, Tuple, Optional

class VideoRepository:
    """
    Data access layer for performing CRUD operations on Video Peewee entities.
    """

    def create_video(self, video_data: dict, user_id: int):
        """
        Commits a new Video record into the database with initial status 'PENDING' linked to user_id.
        """
        pass

    def get_video_by_id(self, video_id: int, user_id: int):
        """
        Fetches a video record by integer primary key ID ensuring ownership authorization (user_id).
        """
        pass

    def get_video_by_bunny_id(self, bunny_video_id: str):
        """
        Fetches a video record by string Bunny GUID (bunny_video_id) for webhook event processing.
        """
        pass

    def get_all_videos_by_user(self, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List, int]:
        """
        Fetches a paginated list of video records and total count owned by the creator using Peewee paginate().
        """
        pass

    def update_video_metadata(self, video_id: int, user_id: int, update_data: dict):
        """
        Updates textual fields (title, description, category, tags) of a video asset in DB.
        """
        pass

    def update_video_status(self, bunny_video_id: str, status: str, encode_progress: int, is_playable: bool):
        """
        Updates state machine fields (status, encode_progress, is_playable) of a video record in DB.
        """
        pass

    def swap_main_thumbnail(self, video_id: int, user_id: int, new_main_url: str):
        """
        Updates main_thumbnail_url and pushes the previous main URL into alt_thumbnail_urls list.
        """
        pass

    def delete_alt_thumbnail_url(self, video_id: int, user_id: int, target_url: str):
        """
        Removes a target thumbnail URL entry from alt_thumbnail_urls array in DB.
        """
        pass

    def delete_video(self, video_id: int, user_id: int) -> bool:
        """
        Deletes a video record from DB and cascades playlist association cleanup.
        """
        pass
