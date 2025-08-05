import React, { useState } from 'react';

const InputForm = () => {
  const [urls, setUrls] = useState(['']);
  const [businessCategory, setBusinessCategory] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  // URL validation function
  const validateUrl = (url) => {
    if (!url.trim()) return 'URL is required';
    
    try {
      // Add protocol if missing
      const urlToValidate = url.startsWith('http://') || url.startsWith('https://') 
        ? url 
        : `https://${url}`;
      
      new URL(urlToValidate);
      
      // Basic domain validation
      const urlPattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
      if (!urlPattern.test(urlToValidate)) {
        return 'Please enter a valid website URL';
      }
      
      return null;
    } catch {
      return 'Please enter a valid website URL';
    }
  };

  // Handle URL input change
  const handleUrlChange = (index, value) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);

    // Clear error for this field
    if (errors[`url_${index}`]) {
      const newErrors = { ...errors };
      delete newErrors[`url_${index}`];
      setErrors(newErrors);
    }
  };

  // Add new URL input field
  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  // Remove URL input field
  const removeUrlField = (index) => {
    if (urls.length > 1) {
      setUrls(urls.filter((_, i) => i !== index));
      // Remove error for this field
      const newErrors = { ...errors };
      delete newErrors[`url_${index}`];
      setErrors(newErrors);
    }
  };

  // Validate all URLs
  const validateAllUrls = () => {
    const newErrors = {};
    let hasErrors = false;

    urls.forEach((url, index) => {
      const error = validateUrl(url);
      if (error) {
        newErrors[`url_${index}`] = error;
        hasErrors = true;
      }
    });

    setErrors(newErrors);
    return !hasErrors;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateAllUrls()) {
      return;
    }

    setIsLoading(true);

    try {
      // Filter out empty URLs
      const validUrls = urls.filter(url => url.trim());
      
      // For now, we'll submit the first URL as required by the API spec
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          site_url: validUrls[0].startsWith('http') ? validUrls[0] : `https://${validUrls[0]}`,
          business_category: businessCategory || undefined
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to create project');
      }

      const data = await response.json();
      
      // TODO: Navigate to next step using project_id
      console.log('Project created:', data);
      alert(`Project created successfully! Project ID: ${data.project_id}`);
      
    } catch (error) {
      console.error('Error creating project:', error);
      setErrors({ submit: error.message || 'Failed to create project. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Enter Your Website URLs</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* URL Input Fields */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Website URLs *
          </label>
          
          {urls.map((url, index) => (
            <div key={index} className="flex gap-2">
              <div className="flex-1">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  placeholder="https://example.com"
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors[`url_${index}`] ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors[`url_${index}`] && (
                  <p className="mt-1 text-sm text-red-600">{errors[`url_${index}`]}</p>
                )}
              </div>
              
              {/* Remove button - only show if more than one URL */}
              {urls.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeUrlField(index)}
                  className="px-3 py-2 text-red-600 hover:text-red-800 focus:outline-none"
                  aria-label={`Remove URL field ${index + 1}`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
          
          {/* Add URL button */}
          <button
            type="button"
            onClick={addUrlField}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-500 focus:outline-none"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add another URL
          </button>
        </div>

        {/* Business Category - Optional */}
        <div>
          <label htmlFor="businessCategory" className="block text-sm font-medium text-gray-700 mb-2">
            Business Category (Optional)
          </label>
          <input
            type="text"
            id="businessCategory"
            value={businessCategory}
            onChange={(e) => setBusinessCategory(e.target.value)}
            placeholder="e.g., E-commerce, SaaS, Consulting"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <p className="text-sm text-red-600">{errors.submit}</p>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed text-white'
              : 'bg-primary-600 hover:bg-primary-700 text-white'
          }`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Website...
            </span>
          ) : (
            'Start AEO Analysis'
          )}
        </button>
      </form>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 rounded-md">
        <h3 className="text-sm font-medium text-blue-900 mb-2">How it works:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Enter your website URL(s) to analyze</li>
          <li>• We'll test how well your site appears in AI chatbot responses</li>
          <li>• Get personalized recommendations to improve your AEO performance</li>
        </ul>
      </div>
    </div>
  );
};

export default InputForm;