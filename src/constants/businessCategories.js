// Business categories for AEO analysis
// Maintains consistency with backend constants in src/constants/business_categories.py

/**
 * Business category configuration for the AEO analysis system.
 * Each category has a value (used in API calls) and a label (displayed in UI).
 * 
 * @typedef {Object} BusinessCategory
 * @property {string} value - The internal value used in API calls and storage
 * @property {string} label - The human-readable label displayed in the UI
 */
export const BUSINESS_CATEGORIES = [
  { value: 'e-commerce', label: 'E-commerce' },
  { value: 'saas', label: 'SaaS' },
  { value: 'local-services', label: 'Local Services' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'finance', label: 'Finance' },
  { value: 'education', label: 'Education' },
  { value: 'real-estate', label: 'Real Estate' },
  { value: 'travel-hospitality', label: 'Travel & Hospitality' },
  { value: 'professional-services', label: 'Professional Services' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'other', label: 'Other' }
];

// Export as array of values for backend validation and consistency checks
export const BUSINESS_CATEGORY_VALUES = BUSINESS_CATEGORIES.map(cat => cat.value);

// Helper function to get label by value
export const getBusinessCategoryLabel = (value) => {
  const category = BUSINESS_CATEGORIES.find(cat => cat.value === value);
  return category ? category.label : value;
};