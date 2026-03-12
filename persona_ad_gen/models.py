from typing import Optional, List
from pydantic import BaseModel

class PersonaDrivenAdBrief(BaseModel):
    """Data model for the persona-driven ad creative brief."""
    # The Ideal Customer (The Persona)
    ideal_customer: str  # Description of the person and their problem/need/desire
    
    # The 'Aha!' Moment (The Core Message)
    core_message: str  # One powerful sentence solution/takeaway
    
    # The Conversation (Tone of Voice)
    tone_of_voice: str  # Professional, Empathetic, Witty, Urgent, etc.
    
    # The Creative Toolbox (Assets & Copy)
    headlines: List[str]  # 5-10 different headlines
    # Note: Images are handled separately as artifacts
    
    # The Targeting Signals (Audience Foundation)
    location: str  # Where customers are located
    demographics: str  # Age range and gender
    interests: str  # 3-5 interests or behaviors
    
    # Optional paths for additional assets
    creative_brief_gcs_path: Optional[str] = None
    brand_logo_gcs_path: Optional[str] = None

# Keep the old model for backward compatibility
class VideoAdBrief(BaseModel):
    """Legacy data model for the video ad creative brief."""
    brand: str
    product: str
    target_location: str
    target_age: str
    target_gender: str
    target_interests: str
    creative_brief_gcs_path: Optional[str] = None
    brand_logo_gcs_path: Optional[str] = None
