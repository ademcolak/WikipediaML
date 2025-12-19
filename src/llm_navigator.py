"""
llm_navigator.py
----------------
LLM-based link selection for Wikipedia navigation.

Uses Claude API to intelligently select the best link from available options.
"""

import os
from typing import List, Optional, Any
from anthropic import Anthropic
from anthropic.types import TextBlock


class LLMNavigator:
    """
    LLM-based navigator using Claude API.
    
    Uses Claude Haiku (cheapest model) to select the best link
    from a list of candidates when KG doesn't have the path.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM Navigator.
        
        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        try:
            import anthropic
            self.anthropic = anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var or pass api_key parameter."
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"  # Cheapest model
        self.call_count = 0
        self.total_cost = 0.0
    
    def select_link(
        self,
        current_page: str,
        target_page: str,
        available_links: List[str],
        max_links: int = 10
    ) -> str:
        """
        Select the best link using LLM.
        
        Args:
            current_page: Current Wikipedia page
            target_page: Target Wikipedia page
            available_links: List of available links from current page
            max_links: Maximum number of links to send to LLM (to reduce cost)
        
        Returns:
            Selected link name
        """
        # Limit links to reduce token cost
        links_to_consider = available_links[:max_links]
        
        # Create prompt
        prompt = self._create_prompt(current_page, target_page, links_to_consider)
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            # Handle different content block types
            content_block = response.content[0]
            if isinstance(content_block, TextBlock):
                selected_link = content_block.text.strip()
            else:
                # Fallback to string representation
                selected_link = str(content_block).strip()
            
            # Update stats
            self.call_count += 1
            # Haiku pricing: ~$0.00025 per 1K input tokens, ~$0.00125 per 1K output tokens
            # Rough estimate: ~$0.02 per call
            self.total_cost += 0.02
            
            # Validate response
            if selected_link in available_links:
                return selected_link
            else:
                # LLM returned invalid link, fallback to first link
                print(f"⚠️ LLM returned invalid link: {selected_link}, using first link")
                return available_links[0]
        
        except Exception as e:
            print(f"❌ LLM API error: {e}")
            # Fallback to first link
            return available_links[0]
    
    def _create_prompt(
        self,
        current_page: str,
        target_page: str,
        links: List[str]
    ) -> str:
        """Create prompt for LLM."""
        links_str = ", ".join(links)
        
        prompt = f"""You are helping navigate Wikipedia from "{current_page}" to "{target_page}".

Current page: {current_page}
Target page: {target_page}
Available links: {links_str}

Which link should I click to get closer to the target? Reply with ONLY the exact link name, nothing else."""
        
        return prompt
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            'call_count': self.call_count,
            'total_cost': self.total_cost,
            'avg_cost_per_call': self.total_cost / max(1, self.call_count)
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.call_count = 0
        self.total_cost = 0.0