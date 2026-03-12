from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum

# Enums for structured choices
class CampaignObjective(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    SALES = "sales"

class ToneOfVoice(str, Enum):
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    WITTY = "witty"
    URGENT = "urgent"
    CONVERSATIONAL = "conversational"
    INSPIRING = "inspiring"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"

class CallToAction(str, Enum):
    SHOP_NOW = "Shop Now"
    LEARN_MORE = "Learn More"
    SIGN_UP = "Sign Up"
    GET_STARTED = "Get Started"
    BOOK_NOW = "Book Now"
    CONTACT_US = "Contact Us"
    DOWNLOAD = "Download"
    WATCH_MORE = "Watch More"

class Platform(str, Enum):
    META = "meta"
    GOOGLE = "google"
    BOTH = "both"

class AdFormat(str, Enum):
    SINGLE_IMAGE = "single_image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    COLLECTION = "collection"
    RESPONSIVE_SEARCH = "responsive_search"
    RESPONSIVE_DISPLAY = "responsive_display"

# Demographics Models
class Demographics(BaseModel):
    age_min: Optional[int] = Field(None, ge=13, le=100)
    age_max: Optional[int] = Field(None, ge=13, le=100)
    genders: List[str] = Field(default=["All"])
    languages: List[str] = Field(default=[])
    education_levels: List[str] = Field(default=[])
    fields_of_study: List[str] = Field(default=[])
    relationship_status: List[str] = Field(default=[])
    parental_status: List[str] = Field(default=[])

class GeographicTargeting(BaseModel):
    countries: List[str] = Field(default=[])
    states_regions: List[str] = Field(default=[])
    cities: List[str] = Field(default=[])
    zip_codes: List[str] = Field(default=[])
    radius_targeting: Optional[Dict[str, Any]] = None  # {address: str, radius: int, unit: "miles"|"km"}
    location_types: List[str] = Field(default=["living_in"])  # living_in, recently_in, traveling_in

class WorkTargeting(BaseModel):
    employers: List[str] = Field(default=[])
    industries: List[str] = Field(default=[])
    job_titles: List[str] = Field(default=[])
    seniority_levels: List[str] = Field(default=[])
    company_sizes: List[str] = Field(default=[])

class FinancialTargeting(BaseModel):
    household_income_percentiles: List[str] = Field(default=[])  # "Top 10%", "10-25%", etc.

# Interest and Behavior Models
class InterestTargeting(BaseModel):
    broad_categories: List[str] = Field(default=[])
    specific_interests: List[str] = Field(default=[])
    affinity_segments: List[str] = Field(default=[])
    custom_interests: List[str] = Field(default=[])

class BehaviorTargeting(BaseModel):
    purchase_behaviors: List[str] = Field(default=[])
    digital_activities: List[str] = Field(default=[])
    travel_behaviors: List[str] = Field(default=[])
    device_usage: List[str] = Field(default=[])
    seasonal_behaviors: List[str] = Field(default=[])

class LifeEventTargeting(BaseModel):
    major_life_events: List[str] = Field(default=[])
    anniversaries: List[str] = Field(default=[])
    upcoming_events: List[str] = Field(default=[])

# First-Party Data Models
class CustomAudience(BaseModel):
    name: str
    source_type: Literal["website_visitors", "app_users", "customer_list", "engagement"]
    description: Optional[str] = None
    # For website visitors
    website_rules: Optional[List[Dict[str, Any]]] = None
    # For customer lists
    customer_data: Optional[List[str]] = None  # emails, phone numbers
    # For app users
    app_events: Optional[List[str]] = None
    # For engagement
    engagement_type: Optional[str] = None

class LookalikeAudience(BaseModel):
    name: str
    source_audience: str  # Reference to CustomAudience
    similarity_percentage: int = Field(default=1, ge=1, le=10)
    countries: List[str]

# Advanced Audience Builder
class AdvancedAudienceBuilder(BaseModel):
    name: str
    description: Optional[str] = None
    
    # Core targeting
    demographics: Demographics = Demographics()
    geographic: GeographicTargeting = GeographicTargeting()
    work: WorkTargeting = WorkTargeting()
    financial: FinancialTargeting = FinancialTargeting()
    
    # Interest and behavior
    interests: InterestTargeting = InterestTargeting()
    behaviors: BehaviorTargeting = BehaviorTargeting()
    life_events: LifeEventTargeting = LifeEventTargeting()
    
    # First-party data
    custom_audiences: List[str] = Field(default=[])  # References to CustomAudience names
    lookalike_audiences: List[str] = Field(default=[])  # References to LookalikeAudience names
    excluded_audiences: List[str] = Field(default=[])
    
    # Logical operators
    audience_logic: Literal["AND", "OR"] = "AND"
    
    # Platform-specific settings
    platform: Platform = Platform.BOTH

# Creative Asset Models
class CreativeAsset(BaseModel):
    asset_type: Literal["image", "video", "logo", "text"]
    filename: Optional[str] = None
    content: Optional[str] = None  # For text assets
    specifications: Optional[Dict[str, Any]] = None  # dimensions, format, etc.
    platform_optimized: List[Platform] = Field(default=[Platform.BOTH])

class BrandGuidelines(BaseModel):
    primary_colors: List[str] = Field(default=[])  # Hex codes
    secondary_colors: List[str] = Field(default=[])
    fonts: List[str] = Field(default=[])
    logo_variations: List[str] = Field(default=[])  # filenames
    voice_guidelines: Optional[str] = None
    visual_style_notes: Optional[str] = None

class CreativeVariations(BaseModel):
    headlines: List[str] = Field(default=[], max_items=15)
    descriptions: List[str] = Field(default=[], max_items=4)
    primary_text: List[str] = Field(default=[])  # For Meta
    call_to_actions: List[CallToAction] = Field(default=[])
    images: List[str] = Field(default=[])  # Asset filenames
    videos: List[str] = Field(default=[])  # Asset filenames

# Campaign Configuration Models
class BidStrategy(BaseModel):
    strategy_type: Literal["cpc", "cpm", "cpa", "roas", "auto"]
    target_amount: Optional[float] = None
    daily_budget: Optional[float] = None
    lifetime_budget: Optional[float] = None

class PlacementSettings(BaseModel):
    platform: Platform
    placements: List[str] = Field(default=[])  # feed, stories, reels, search, display, youtube
    device_types: List[str] = Field(default=["all"])  # mobile, desktop, tablet
    operating_systems: List[str] = Field(default=["all"])  # ios, android, windows

class AdvancedCampaignSettings(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None  # day parting
    frequency_cap: Optional[Dict[str, Any]] = None
    optimization_goal: Optional[str] = None
    attribution_window: Optional[str] = None

# A/B Testing Framework
class ABTestConfiguration(BaseModel):
    test_name: str
    variable_to_test: Literal["headline", "image", "audience", "placement", "bid_strategy"]
    variations: List[Dict[str, Any]]
    traffic_split: List[int] = Field(default=[50, 50])  # Percentage split
    duration_days: int = Field(default=7, ge=1, le=30)
    success_metric: str = "ctr"  # ctr, cpc, cpa, roas
    minimum_sample_size: Optional[int] = None
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)

# Advanced Pro Brief Model
class AdvancedProBrief(BaseModel):
    # Campaign Foundation
    campaign_name: str
    company_name: str
    website_url: str
    brand_mission: Optional[str] = None
    
    # Campaign Strategy
    objective: CampaignObjective
    product_service_name: str
    product_description: str
    unique_selling_proposition: str
    target_landing_url: str
    
    # Advanced Messaging
    target_persona_detailed: str
    core_message: str
    tone_of_voice: ToneOfVoice
    primary_cta: CallToAction
    secondary_cta: Optional[CallToAction] = None
    
    # Advanced Targeting
    audience_strategy: AdvancedAudienceBuilder
    custom_audiences: List[CustomAudience] = Field(default=[])
    lookalike_audiences: List[LookalikeAudience] = Field(default=[])
    
    # Creative Strategy
    ad_formats: List[AdFormat]
    creative_variations: CreativeVariations
    brand_guidelines: BrandGuidelines
    creative_assets: List[CreativeAsset] = Field(default=[])
    
    # Campaign Configuration
    platforms: List[Platform]
    placement_settings: List[PlacementSettings] = Field(default=[])
    bid_strategy: BidStrategy
    advanced_settings: AdvancedCampaignSettings = AdvancedCampaignSettings()
    
    # Testing Strategy
    ab_tests: List[ABTestConfiguration] = Field(default=[])
    
    # Compliance and Notes
    industry_compliance_notes: Optional[str] = None
    special_requirements: Optional[str] = None
    approval_workflow: Optional[Dict[str, Any]] = None

# Analytics and Reporting Models
class PerformanceMetrics(BaseModel):
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    conversions: Optional[int] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    reach: Optional[int] = None
    frequency: Optional[float] = None

class CampaignPerformance(BaseModel):
    campaign_id: str
    campaign_name: str
    platform: Platform
    date_range: Dict[str, str]  # start_date, end_date
    metrics: PerformanceMetrics
    top_performing_assets: List[str] = Field(default=[])
    optimization_recommendations: List[str] = Field(default=[])

# Integration Models
class CRMIntegration(BaseModel):
    platform: Literal["salesforce", "hubspot", "pipedrive", "custom"]
    api_credentials: Optional[Dict[str, str]] = None
    lead_scoring_rules: Optional[List[Dict[str, Any]]] = None
    sync_frequency: Literal["real_time", "hourly", "daily"] = "daily"

class EcommerceIntegration(BaseModel):
    platform: Literal["shopify", "woocommerce", "magento", "custom"]
    store_url: str
    api_credentials: Optional[Dict[str, str]] = None
    product_catalog_sync: bool = True
    inventory_based_automation: bool = False
