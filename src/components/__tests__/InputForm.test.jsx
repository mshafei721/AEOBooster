import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import InputForm from '../InputForm';

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
    
    // Mock alert
    window.alert = jest.fn();
    
    render(<InputForm />);
    
    const urlInput = screen.getByPlaceholderText('https://example.com');
    await user.type(urlInput, 'example.com');
    
    const submitButton = screen.getByText('Start AEO Analysis');
    await user.click(submitButton);
    
    // Should show loading state
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
    
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Project created successfully! Project ID: test-project-id');
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
      expect(screen.getByText('Failed to create project. Please try again.')).toBeInTheDocument();
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
    
    const categoryInput = screen.getByPlaceholderText('e.g., E-commerce, SaaS, Consulting');
    await user.type(categoryInput, 'E-commerce');
    
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
          business_category: 'E-commerce'
        }),
      });
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