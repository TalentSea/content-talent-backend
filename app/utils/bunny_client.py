def create_bunny_video(title: str) -> dict:
    """
    Issues an HTTP POST request to Bunny Stream API to reserve an empty video container slot and return a bunny_video_id GUID.
    """
    pass

def get_bunny_video_status(bunny_video_id: str) -> dict:
    """
    Issues an HTTP GET request to Bunny Stream API to fetch live encodeProgress percentage and resolution availability.
    """
    pass

def delete_bunny_video(bunny_video_id: str) -> bool:
    """
    Issues an HTTP DELETE request to Bunny Stream API to permanently remove a video container and encoded video streams.
    """
    pass

def delete_bunny_storage_file(file_path: str) -> bool:
    """
    Issues an HTTP DELETE request to Bunny Storage API to remove a physical thumbnail or asset file from cloud storage.
    """
    pass
