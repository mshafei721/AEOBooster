import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import InputForm from '../InputForm';
import { BUSINESS_CATEGORIES } from '../../constants/businessCategories';

// Mock the UI components
jest.mock('../UI/LoadingSpinner', () => {
  return function MockLoadingSpinner({ text }) {
    return <div data-testid="loading-spinner">{text}</div>;
  };
});

jest.mock('../UI/ErrorMessage', () => {
  return function MockErrorMessage({ title, message, onRetry }) {
    return (
      <div data-testid="error-message">
        <h3>{title}</h3>
        <p>{message}</p>
        {onRetry && <button onClick={onRetry}>Retry</button>}
      </div>
    );
  };
});

jest.mock('../UI/ProgressIndicator', () => {
  return function MockProgressIndicator({ currentStep }) {
    return <div data-testid="progress-indicator">Step {currentStep}</div>;
  };
});

// Mock fetch
global.fetch = jest.fn();

describe('InputForm', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders form with initial URL input', () => {
    render(<InputForm />);
    
    expect(screen.getByText('Enter Your Website URLs')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('https://example.com')).toBeInTheDocument();
    expect(screen.getByText('Start AEO Analysis')).toBeInTheDocument();
  });

  test('validates required URL field', async () => {
    const user = userEvent.setup();
    render(<InputForm />);
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    expect(screen.getByText('URL is required')).toBeInTheDocument();
  });

  test('validates URL format', async () => {
    const user = userEvent.setup();
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'invalid-url');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    expect(screen.getByText('Please enter a valid website URL')).toBeInTheDocument();
  });

  test('accepts valid URLs', async () => {
    const user = userEvent.setup();
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    
    // Test various valid URL formats
    const validUrls = [
      'https://example.com',
      'http://example.com',
      'example.com',
      'www.example.com',
      'subdomain.example.com'
    ];
    
    for (const url of validUrls) {
      await user.clear(urlInput);
      await user.type(urlInput, url);
      
      const submitButton = screen.getByText('Start AEO Analysis');
      await user.click(submitButton);
      
      // Should not show validation error
      expect(screen.queryByText('Please enter a valid website URL')).not.toBeInTheDocument();
      expect(screen.queryByText('URL is required')).not.toBeInTheDocument();
    }
  });

  test('can add and remove additional URL fields', async () => {
    const user = userEvent.setup();
    render(<InputForm />);
    
    // Initially should have one URL input
    expect(screen.getAllByPlaceholderText('https://example.com')).toHaveLength(1);
    
    // Add another URL field
    const addButton = screen.getByText('Add another URL');
    await user.click(addButton);
    
    expect(screen.getAllByPlaceholderText('https://example.com')).toHaveLength(2);
    
    // Remove URL field (X button should appear)
    const removeButtons = screen.getAllByLabelText(/Remove URL field/);
    expect(removeButtons).toHaveLength(1); // Only one remove button for the second field
    
    await user.click(removeButtons[0]);
    expect(screen.getAllByPlaceholderText('https://example.com')).toHaveLength(1);
  });

  test('handles form submission successfully', async () => {
    const user = userEvent.setup();
    
    // Mock successful API response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ project_id: 'test-project-id', status: 'created' })
    });
    
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'example.com');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    // Should show loading state
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Analyzing Website...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          site_url: 'https://example.com',
          business_category: undefined
        }),
      });
    });
    
    // Should show success screen
    await waitFor(() => {
      expect(screen.getByText('Analysis Started!')).toBeInTheDocument();
      expect(screen.getByText('test-project-id')).toBeInTheDocument();
      expect(screen.getByTestId('progress-indicator')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    });
    
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'example.com');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByText('Submission Failed')).toBeInTheDocument();
    });
  });

  test('includes business category in submission', async () => {
    const user = userEvent.setup();
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ project_id: 'test-project-id', status: 'created' })
    });
    
    window.alert = jest.fn();
    
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'example.com');
    
    // Select from dropdown instead of typing
    const categorySelect = screen.getByLabelText(/Business Category/);
    await user.selectOptions(categorySelect, 'e-commerce');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          site_url: 'https://example.com',
          business_category: 'e-commerce'
        }),
      });
    });
  });

  test('can skip business category selection', async () => {
    const user = userEvent.setup();
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ project_id: 'test-project-id', status: 'created' })
    });
    
    window.alert = jest.fn();
    
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'example.com');
    
    // Don't select any category (default is empty)
    const categorySelect = screen.getByLabelText(/Business Category/);
    expect(categorySelect.value).toBe('');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          site_url: 'https://example.com',
          business_category: undefined
        }),
      });
    });
  });

  test('shows all business categories in dropdown', () => {
    render(<InputForm />);
    
    const categorySelect = screen.getByLabelText(/Business Category/);
    
    // Check that skip option exists
    expect(screen.getByText('Skip this step')).toBeInTheDocument();
    
    // Check that all business categories are present
    BUSINESS_CATEGORIES.forEach(category => {
      expect(screen.getByText(category.label)).toBeInTheDocument();
    });
  });

  test('is responsive - contains proper CSS classes', () => {
    render(<InputForm />);
    
    // Check for responsive container classes
    const form = screen.getByRole('form');
    expect(form.parentElement).toHaveClass('bg-white', 'rounded-lg', 'shadow-lg', 'p-6');
    
    // Check for responsive input classes
    const urlInput = screen.getByPlaceholderText('https://example.com');
    expect(urlInput).toHaveClass('w-full');
    
    // Check for responsive button classes
    const submitButton = screen.getByText('Start AEO Analysis');
    expect(submitButton).toHaveClass('w-full');
  });
});