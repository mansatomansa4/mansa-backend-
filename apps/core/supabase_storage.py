"""
Supabase Storage utility for handling file uploads
"""
import os
import uuid
from typing import Optional
from django.conf import settings
from supabase import create_client, Client


class SupabaseStorage:
    """Handle file uploads to Supabase Storage"""
    
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        
        # Validate credentials
        if not self.url:
            raise ValueError("SUPABASE_URL is not configured in settings")
        if not self.key:
            raise ValueError("SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY must be configured")
        
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Supabase client: {e}")
    
    def upload_file(
        self, 
        file, 
        bucket_name: str, 
        folder: str = "", 
        filename: Optional[str] = None
    ) -> str:
        """
        Upload a file to Supabase Storage
        
        Args:
            file: Django UploadedFile object
            bucket_name: Supabase storage bucket name (e.g., 'events', 'projects')
            folder: Optional folder path within bucket
            filename: Optional custom filename, otherwise generates UUID-based name
        
        Returns:
            Public URL of uploaded file
        """
        if not filename:
            # Generate unique filename preserving extension
            ext = os.path.splitext(file.name)[1] if hasattr(file, 'name') else ''
            filename = f"{uuid.uuid4()}{ext}"
        
        # Build path
        path = f"{folder}/{filename}" if folder else filename
        
        # Upload file
        file_bytes = file.read()
        self.client.storage.from_(bucket_name).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": file.content_type if hasattr(file, 'content_type') else 'application/octet-stream'}
        )
        
        # Get public URL
        public_url = self.client.storage.from_(bucket_name).get_public_url(path)
        return public_url
    
    def delete_file(self, bucket_name: str, path: str) -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            bucket_name: Supabase storage bucket name
            path: File path within bucket
        
        Returns:
            True if deleted successfully
        """
        try:
            self.client.storage.from_(bucket_name).remove([path])
            return True
        except Exception as e:
            print(f"Error deleting file from Supabase: {e}")
            return False
    
    def get_public_url(self, bucket_name: str, path: str) -> str:
        """Get public URL for a file"""
        return self.client.storage.from_(bucket_name).get_public_url(path)


# Singleton instance
_storage_instance = None


def get_supabase_storage() -> SupabaseStorage:
    """Get or create Supabase storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SupabaseStorage()
    return _storage_instance
