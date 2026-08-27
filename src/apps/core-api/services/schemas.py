from pydantic import BaseModel, Field
from typing import List, Optional
from typing_extensions import TypedDict
import operator

class DirectorSpec(BaseModel):
    """
    Structured output schema for the AI Director Agent.
    Dictates the script pacing, hooks, and required legal disclosures.
    """
    visual_hook: str = Field(
        description="The opening 3-second visual description to grab attention."
    )
    narration_text: str = Field(
        description="The full voiceover script text to be spoken."
    )
    pacing_notes: List[str] = Field(
        description="Timing cues for scene transitions or visual effects."
    )
    ad_disclosures: List[str] = Field(
        description="Mandatory tags like #Ad, #Sponsored, or #AffiliateLink."
    )

class AgentState(TypedDict):
    """
    State dictionary for the LangGraph AI Director workflow.
    """
    product_id: Optional[str]
    creator_id: Optional[str]
    trace_id: Optional[str]
    product_title: Optional[str]
    product_price: Optional[str]
    
    # Outputs
    generated_spec: Optional[DirectorSpec]
    claims_accuracy_score: Optional[float]
    total_tokens: Optional[int]
    status: Optional[str]
