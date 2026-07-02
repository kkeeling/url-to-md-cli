"""
YouTube to Markdown converter module.

This module provides functionality to convert YouTube video transcripts to Markdown format
using the youtube-transcript-api library and LLM processing. It includes robust error
handling, transcript preference logic, and retry mechanisms for reliable conversion.

Example:
    ```python
    from kb_for_prompt.molecules.youtube_converter import convert_youtube_to_markdown
    
    # Convert a YouTube video to markdown
    markdown_content, video_url = convert_youtube_to_markdown(
        "dQw4w9WgXcQ", 
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    # Convert with custom retry settings
    markdown_content, video_url = convert_youtube_to_markdown(
        "dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        max_retries=5
    )
    ```
"""

import time
import re
from typing import Dict, Any, Tuple
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Import LLM client and utilities
from kb_for_prompt.organisms.llm_client import LiteLlmClient, SimpleLlmClient
from kb_for_prompt.templates.youtube_prompt import YOUTUBE_TRANSCRIPT_PROMPT
from kb_for_prompt.atoms.error_utils import ConversionError


class YouTubeConverter:
    """
    Converter class for YouTube video transcripts.
    
    This class handles the extraction of YouTube video transcripts and their
    conversion to well-formatted markdown articles using LLM processing.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the YouTube converter with an LLM client.
        
        Args:
            llm_client: An LLM client instance (LiteLlmClient or SimpleLlmClient)
        """
        self.llm_client = llm_client
    
    def extract_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Extract video metadata using youtube-transcript-api or basic web scraping.
        
        For now, this returns placeholder data. In a production implementation,
        this could be enhanced to fetch actual metadata from YouTube.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Dictionary containing video metadata with keys:
            - title: Video title
            - channel: Channel name
            - upload_date: Upload date
            - description: Video description
        """
        # In a production implementation, this could fetch actual metadata
        # For now, we'll use the transcript API to get basic info
        # and provide placeholders for other fields
        return {
            "title": f"YouTube Video {video_id}",
            "channel": "YouTube Channel",
            "upload_date": "Date not available",
            "description": "Description not available"
        }
    
    def get_transcript(self, video_id: str) -> str:
        """
        Fetch transcript with preference for manual captions.
        Falls back to auto-generated if manual not available.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            The full transcript text as a single string
            
        Raises:
            ConversionError: If transcript cannot be fetched
        """
        try:
            # Try to get manual transcript first
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find the best transcript
            transcript = None
            
            # First, try to find a manually created transcript
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break
            
            # If no manual transcript found, use the first available one
            if transcript is None:
                # Get the first transcript (manual or auto-generated)
                for t in transcript_list:
                    transcript = t
                    break
            
            if transcript is None:
                raise NoTranscriptFound("No transcripts available for this video")
            
            # Fetch the actual transcript data
            transcript_data = transcript.fetch()
            
            # Combine all text segments
            # Handle different possible data structures
            if isinstance(transcript_data, list):
                full_text = ' '.join([item['text'] for item in transcript_data])
            else:
                # If it's not a list, try to extract text directly
                full_text = str(transcript_data)
            return full_text
            
        except TranscriptsDisabled:
            raise ConversionError(
                message="Transcripts are disabled for this video",
                input_path=f"https://youtube.com/watch?v={video_id}",
                conversion_type="youtube",
                details={"video_id": video_id, "error": "transcripts_disabled"}
            )
        except NoTranscriptFound:
            raise ConversionError(
                message="No transcripts found for this video",
                input_path=f"https://youtube.com/watch?v={video_id}",
                conversion_type="youtube",
                details={"video_id": video_id, "error": "no_transcript_found"}
            )
        except Exception as e:
            raise ConversionError(
                message=f"Failed to fetch transcript: {str(e)}",
                input_path=f"https://youtube.com/watch?v={video_id}",
                conversion_type="youtube",
                details={"video_id": video_id, "error": str(e)}
            )
    
    def convert_to_markdown(self, video_id: str, video_url: str) -> str:
        """
        Main conversion pipeline for YouTube videos.
        
        Args:
            video_id: The YouTube video ID
            video_url: The full YouTube URL
            
        Returns:
            The generated markdown content
            
        Raises:
            ConversionError: If conversion fails
        """
        try:
            # 1. Extract metadata
            metadata = self.extract_video_metadata(video_id)
            
            # 2. Get transcript
            transcript = self.get_transcript(video_id)
            
            # 3. Prepare prompt with the data
            formatted_prompt = YOUTUBE_TRANSCRIPT_PROMPT.format(
                metadata=metadata,
                url=video_url,
                transcript=transcript
            )
            
            # 4. Process with LLM
            # Note: The specification mentions "gemini-2.0-flash-preview-05-20" but that seems incorrect
            # Using "gemini-2.5-flash-preview-05-20" as mentioned in the original request
            markdown_content = self.llm_client.invoke(
                prompt=formatted_prompt,
                model="gemini/gemini-2.5-flash-preview-05-20"
            )
            
            if not markdown_content:
                raise ConversionError(
                    message="LLM failed to generate markdown content",
                    input_path=video_url,
                    conversion_type="youtube",
                    details={"video_id": video_id, "error": "llm_generation_failed"}
                )
            
            return markdown_content
            
        except ConversionError:
            # Re-raise ConversionErrors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in ConversionError
            raise ConversionError(
                message=f"Unexpected error during conversion: {str(e)}",
                input_path=video_url,
                conversion_type="youtube",
                details={"video_id": video_id, "error": str(e)}
            )
    
    def sanitize_filename(self, title: str) -> str:
        """
        Sanitize video title for use as filename.
        
        Args:
            title: The video title to sanitize
            
        Returns:
            A sanitized filename with .md extension
        """
        # Remove invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Limit length to 100 characters
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        # Prepend youtube_ prefix and add .md extension
        return f"youtube_{sanitized}.md"


def convert_youtube_to_markdown(
    video_id: str,
    video_url: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Tuple[str, str]:
    """
    Convert a YouTube video to markdown content.
    
    This function extracts the transcript from a YouTube video and converts it
    to a well-formatted markdown article using LLM processing. It includes a
    retry mechanism for handling temporary failures.
    
    Args:
        video_id: The YouTube video ID
        video_url: The full YouTube URL
        max_retries: Maximum number of conversion attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
    
    Returns:
        A tuple containing (markdown_content, video_url)
        
    Raises:
        ConversionError: If conversion fails after all retry attempts
    """
    # Create LLM client - try LiteLLM first, fall back to simple client
    try:
        llm_client = LiteLlmClient()
    except:
        llm_client = SimpleLlmClient()
    
    # Create converter instance
    converter = YouTubeConverter(llm_client)
    
    # Set up retry mechanism
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            # Attempt conversion
            markdown_content = converter.convert_to_markdown(video_id, video_url)
            
            # Validate markdown content is not empty
            if markdown_content and len(markdown_content.strip()) > 0:
                return markdown_content, video_url
            else:
                raise ConversionError(
                    message="Conversion produced empty markdown content",
                    input_path=video_url,
                    conversion_type="youtube",
                    details={"video_id": video_id}
                )
                
        except ConversionError as e:
            last_error = e
        except Exception as e:
            # Wrap unexpected errors
            last_error = ConversionError(
                message=f"Unexpected error: {str(e)}",
                input_path=video_url,
                conversion_type="youtube",
                details={"video_id": video_id, "error": str(e)}
            )
        
        # If we haven't reached max retries, wait before trying again
        retries += 1
        if retries <= max_retries:
            # Exponential backoff with jitter
            sleep_time = retry_delay * (2 ** (retries - 1))
            time.sleep(sleep_time)
        else:
            # We've exhausted our retries, raise the last error
            if last_error:
                # Add retry information to error details
                if last_error.details:
                    last_error.details.update({"retries": retries - 1})
                else:
                    last_error.details = {"retries": retries - 1}
                raise last_error
            else:
                # This should never happen, but just in case
                raise ConversionError(
                    message="Failed to convert YouTube video after multiple attempts",
                    input_path=video_url,
                    conversion_type="youtube",
                    details={"video_id": video_id, "retries": retries - 1}
                )