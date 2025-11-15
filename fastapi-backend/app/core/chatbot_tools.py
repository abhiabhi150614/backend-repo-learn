import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.google_services import get_day_notes, update_day_notes
from app.core.youtube_services import search_youtube_videos, create_playlist, add_video_to_playlist, get_user_playlists
from app.core.call_bot import call_bot
from app.models.user import User
from app.models.learning_plan import LearningPlan
import logging

logger = logging.getLogger(__name__)

class ChatbotTools:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        
    def get_tools_schema(self) -> List[Dict]:
        """Return function schemas for Gemini AI function calling"""
        return [
            {
                "name": "get_drive_notes",
                "description": "Fetch learning notes from Google Drive for a specific day",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month_index": {"type": "integer", "description": "Month number (1-12)"},
                        "day": {"type": "integer", "description": "Day number within the month"}
                    },
                    "required": ["month_index", "day"]
                }
            },
            {
                "name": "update_drive_notes",
                "description": "Add or update content in Google Drive notes for a specific day",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month_index": {"type": "integer", "description": "Month number (1-12)"},
                        "day": {"type": "integer", "description": "Day number within the month"},
                        "content": {"type": "string", "description": "Content to add to the notes"}
                    },
                    "required": ["month_index", "day", "content"]
                }
            },
            {
                "name": "search_youtube_videos",
                "description": "Search for YouTube videos on a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for videos"},
                        "max_results": {"type": "integer", "description": "Maximum number of results (default 5)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_youtube_playlist",
                "description": "Create a new YouTube playlist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Playlist title"},
                        "description": {"type": "string", "description": "Playlist description (optional)"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "add_video_to_playlist",
                "description": "Add a video to an existing YouTube playlist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "playlist_name": {"type": "string", "description": "Name of the playlist"},
                        "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                    },
                    "required": ["playlist_name", "video_id"]
                }
            },
            {
                "name": "initiate_call",
                "description": "Make a phone call with learning context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string", "description": "Phone number to call (optional, uses default if not provided)"}
                    },
                    "required": []
                }
            },
            {
                "name": "create_linkedin_post",
                "description": "Create and publish a LinkedIn post with AI-generated content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content for the LinkedIn post"}
                    },
                    "required": ["content"]
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict[str, Any]:
        """Execute a tool function and return results"""
        try:
            if tool_name == "get_drive_notes":
                return self._get_drive_notes(parameters)
            elif tool_name == "update_drive_notes":
                return self._update_drive_notes(parameters)
            elif tool_name == "search_youtube_videos":
                return self._search_youtube_videos(parameters)
            elif tool_name == "create_youtube_playlist":
                return self._create_youtube_playlist(parameters)
            elif tool_name == "add_video_to_playlist":
                return self._add_video_to_playlist(parameters)
            elif tool_name == "initiate_call":
                return self._initiate_call(parameters)
            elif tool_name == "create_linkedin_post":
                return self._create_linkedin_post(parameters)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return {"error": str(e)}
    
    def _get_drive_notes(self, params: Dict) -> Dict[str, Any]:
        """Get notes from Google Drive"""
        month_index = params.get("month_index")
        day = params.get("day")
        
        notes_data = get_day_notes(self.user_id, month_index, day)
        if notes_data:
            return {
                "success": True,
                "content": notes_data.get("content", ""),
                "link": notes_data.get("link", ""),
                "message": f"Here are your notes for Month {month_index}, Day {day}:\n\n{notes_data.get('content', 'No content yet')}\n\n[View in Google Drive]({notes_data.get('link', '')})"
            }
        else:
            return {
                "success": False,
                "message": f"No notes found for Month {month_index}, Day {day}"
            }
    
    def _update_drive_notes(self, params: Dict) -> Dict[str, Any]:
        """Update notes in Google Drive"""
        month_index = params.get("month_index")
        day = params.get("day")
        content = params.get("content")
        
        # Get existing notes first
        existing_notes = get_day_notes(self.user_id, month_index, day)
        existing_content = existing_notes.get("content", "") if existing_notes else ""
        
        # Append new content
        updated_content = f"{existing_content}\n\n{content}" if existing_content else content
        
        success = update_day_notes(self.user_id, month_index, day, updated_content)
        if success:
            updated_notes = get_day_notes(self.user_id, month_index, day)
            return {
                "success": True,
                "link": updated_notes.get("link", "") if updated_notes else "",
                "message": f"Perfect! Your notes for Month {month_index}, Day {day} have been updated.\n\n[View updated notes]({updated_notes.get('link', '') if updated_notes else ''})\n\nKeep up the great work!"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update notes"
            }
    
    def _search_youtube_videos(self, params: Dict) -> Dict[str, Any]:
        """Search YouTube videos"""
        query = params.get("query")
        max_results = params.get("max_results", 5)
        
        videos = search_youtube_videos(self.user_id, query, max_results)
        return {
            "success": True,
            "videos": videos,
            "count": len(videos),
            "message": f"Found {len(videos)} videos for '{query}'"
        }
    
    def _create_youtube_playlist(self, params: Dict) -> Dict[str, Any]:
        """Create YouTube playlist"""
        title = params.get("title")
        description = params.get("description", f"Learning playlist created by EduAI")
        
        # Check user authentication
        user = self.db.query(User).filter(User.id == self.user_id).first()
        if not user or not user.google_id or not user.google_access_token:
            return {
                "success": False,
                "message": "Google account not connected. Please link your Google account first."
            }
        print(self.user_id)
        result = create_playlist(self.user_id, title, description)
        if result and result.get('id') and 'error' not in result:
            return {
                "success": True,
                "playlist_id": result.get('id'),
                "url": result.get('url'),
                "message": f"Great! Your playlist '{title}' has been created.\n\n[Access your playlist]({result.get('url')})\n\nLet me know if you'd like to add videos to it!"
            }
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            return {
                "success": False,
                "message": f"Failed to create playlist: {error_msg}"
            }
    
    def _add_video_to_playlist(self, params: Dict) -> Dict[str, Any]:
        """Add video to playlist"""
        playlist_name = params.get("playlist_name")
        video_id = params.get("video_id")
        
        # Get user playlists
        playlists = get_user_playlists(self.user_id)
        
        # Find playlist by name
        playlist_id = None
        for playlist in playlists:
            if playlist.get('title', '').lower().strip() == playlist_name.lower().strip():
                playlist_id = playlist.get('id')
                break
        
        if not playlist_id:
            # Create playlist if it doesn't exist
            create_result = self._create_youtube_playlist({"title": playlist_name})
            if create_result.get("success"):
                playlist_id = create_result.get("playlist_id")
            else:
                return {
                    "success": False,
                    "message": f"Playlist '{playlist_name}' not found and could not be created"
                }
        
        # Add video to playlist
        result = add_video_to_playlist(self.user_id, playlist_id, video_id)
        if result is True:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return {
                "success": True,
                "message": f"Perfect! Video added to '{playlist_name}' playlist.\n\n[Watch the video]({video_url})\n\nAnything else you'd like to add?"
            }
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            return {
                "success": False,
                "message": f"Failed to add video: {error_msg}"
            }
    
    def _initiate_call(self, params: Dict) -> Dict[str, Any]:
        """Initiate phone call"""
        phone_number = params.get("phone_number", "+919030633137")
        
        result = call_bot.make_call(self.db, self.user_id, phone_number)
        if result.get("success"):
            return {
                "success": True,
                "call_sid": result.get("call_sid"),
                "message": f"Call initiated to {phone_number}"
            }
        else:
            return {
                "success": False,
                "message": f"Call failed: {result.get('error', 'Unknown error')}"
            }
    
    def _create_linkedin_post(self, params: Dict) -> Dict[str, Any]:
        """Create LinkedIn post"""
        content = params.get("content")
        print(content)
        # Get user information
        user = self.db.query(User).filter(User.id == self.user_id).first()
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Create LinkedIn post using Composio
        try:
            from app.core.composio_service import composio_auth
            result = composio_auth.create_linkedin_post(user.email, content)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": f"🎉 Great! Your LinkedIn post has been published successfully!\n\n**Posted Content:**\n{content}\n\nYour professional network can now see your learning progress!"
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "message": f"LinkedIn posting failed: {error_msg}. Please check your LinkedIn connection in social settings."
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Technical error creating LinkedIn post: {str(e)}"
            }