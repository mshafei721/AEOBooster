import React, { useState } from 'react';
import { BUSINESS_CATEGORIES } from '../constants/businessCategories';
import LoadingSpinner from './UI/LoadingSpinner';
import ErrorMessage from './UI/ErrorMessage';
import ProgressIndicator from './UI/ProgressIndicator';

const InputForm = () => {
  const [urls, setUrls] = useState(['']);
  const [businessCategory, setBusinessCategory] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [projectData, setProjectData] = useState(null);

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
      
      // Set success state
      setProjectData(data);
      setIsSuccess(true);
      setErrors({}); // Clear any previous errors
      
    } catch (error) {
      console.error('Error creating project:', error);
      setErrors({ submit: error.message || 'Failed to create project. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  // Reset form to initial state
  const resetForm = () => {
    setUrls(['']);
    setBusinessCategory('');
    setErrors({});
    setIsLoading(false);
    setIsSuccess(false);
    setProjectData(null);
  };

  // If form was successfully submitted, show success screen
  if (isSuccess && projectData) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Analysis Started!</h2>
          <p className="text-gray-600 mb-6">
            Your AEO analysis has been initiated. We're now crawling and analyzing your website.
          </p>
          
          <div className="bg-gray-50 rounded-md p-4 mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Project Details:</h3>
            <p className="text-sm text-gray-600">Project ID: <span className="font-mono text-gray-900">{projectData.project_id}</span></p>
            <p className="text-sm text-gray-600">Website: <span className="text-gray-900">{projectData.site_url}</span></p>
            {projectData.business_category && (
              <p className="text-sm text-gray-600">Category: <span className="text-gray-900">{projectData.business_category}</span></p>
            )}
          </div>
          
          <ProgressIndicator currentStep={2} className="mb-6" />
          
          <div className="space-y-3">
            <button
              onClick={() => window.location.reload()} // Temporary - will be replaced with proper navigation
              className="w-full bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              View Analysis Progress
            </button>
            <button
              onClick={resetForm}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Start New Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 animate-fade-in">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Enter Your Website URLs</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* URL Input Fields */}
        <fieldset className="space-y-4">
          <legend className="block text-sm font-medium text-gray-700">
            Website URLs *
          </legend>
          
          {urls.map((url, index) => (
            <div key={index} className="flex gap-2">
              <div className="flex-1">
                <input
                  type="url"
                  id={`url-${index}`}
                  name={`url-${index}`}
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  placeholder="https://example.com"
                  className={`w-full px-3 py-2 border rounded-md shadow-sm transition-all-smooth focus-ring ${
                    errors[`url_${index}`] ? 'border-red-500' : 'border-gray-300'
                  }`}
                  aria-describedby={errors[`url_${index}`] ? `url-${index}-error` : undefined}
                  aria-invalid={errors[`url_${index}`] ? 'true' : 'false'}
                  aria-label={`Website URL ${index + 1}`}
                  required={index === 0}
                />
                {errors[`url_${index}`] && (
                  <p id={`url-${index}-error`} className="mt-1 text-sm text-red-600" role="alert">
                    {errors[`url_${index}`]}
                  </p>
                )}
              </div>
              
              {/* Remove button - only show if more than one URL */}
              {urls.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeUrlField(index)}
                  className="px-3 py-2 text-red-600 hover:text-red-800 focus-ring transition-all-smooth"
                  aria-label={`Remove website URL ${index + 1}`}
                  title={`Remove website URL ${index + 1}`}
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
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-500 focus-ring transition-all-smooth"
            aria-label="Add another website URL field"
            >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add another URL
          </button>
        </fieldset>

        {/* Business Category - Optional */}
        <div>
          <label htmlFor="businessCategory" className="block text-sm font-medium text-gray-700 mb-2">
            Business Category <span className="text-gray-500 font-normal">(Optional)</span>
          </label>
          <div className="relative">
            <select
              id="businessCategory"
              name="businessCategory"
              value={businessCategory}
              onChange={(e) => setBusinessCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus-ring appearance-none bg-white transition-all-smooth"
              aria-describedby="businessCategory-help"
            >
              <option value="">Skip this step</option>
              {BUSINESS_CATEGORIES.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
              <svg 
                className="fill-current h-4 w-4" 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
              </svg>
            </div>
          </div>
          <p id="businessCategory-help" className="mt-1 text-sm text-gray-500">
            Help us tailor the analysis to your industry for better results
          </p>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <ErrorMessage 
            title="Submission Failed"
            message={errors.submit}
            onRetry={() => {
              const newErrors = { ...errors };
              delete newErrors.submit;
              setErrors(newErrors);
            }}
            className="mb-4"
          />
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-md font-medium focus-ring transition-all-smooth ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed text-white'
              : 'bg-primary-600 hover:bg-primary-700 text-white'
          }`}
        >
          {isLoading ? (
            <LoadingSpinner size="sm" text="Analyzing Website..." />
          ) : (
            'Start AEO Analysis'
          )}
        </button>
      </form>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 rounded-md animate-slide-up">
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