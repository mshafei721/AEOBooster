"""
Business categories for AEO analysis.

This module defines the valid business categories that users can select
to tailor their AEO analysis. These categories are used for:
- API validation in Pydantic models
- Frontend dropdown options
- Future prompt generation customization

Maintains consistency with frontend constants in src/constants/businessCategories.js
"""

from typing import List, Literal

# Type definition for better type safety
BusinessCategoryType = Literal[
    'e-commerce',
    'saas', 
    'local-services',
    'healthcare',
    'finance',
    'education',
    'real-estate',
    'travel-hospitality',
    'professional-services',
    'manufacturing',
    'other'
]

# Business categories for AEO analysis
BUSINESS_CATEGORIES: List[str] = [
    'e-commerce',
    'saas',
    'local-services',
    'healthcare',
    'finance',
    'education',
    'real-estate',
    'travel-hospitality',
    'professional-services',
    'manufacturing',
    'other'
]

def is_valid_business_category(category: str) -> bool:
    """
    Check if a given category is valid.
    
    Args:
        category: The category string to validate
        
    Returns:
        True if the category is valid, False otherwise
    """
    return category in BUSINESS_CATEGORIES