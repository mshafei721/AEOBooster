import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoadingSpinner from '../../UI/LoadingSpinner';

describe('LoadingSpinner', () => {
  test('renders with default props', () => {
    render(<LoadingSpinner />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders with custom text', () => {
    render(<LoadingSpinner text="Processing..." />);
    
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(screen.getByLabelText('Processing...')).toBeInTheDocument();
  });

  test('renders without text when text is empty', () => {
    render(<LoadingSpinner text="" />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  test('applies different sizes correctly', () => {
    const { rerender, container } = render(<LoadingSpinner size="sm" />);
    expect(container.querySelector('.h-4')).toBeInTheDocument();

    rerender(<LoadingSpinner size="lg" />);
    expect(container.querySelector('.h-12')).toBeInTheDocument();

    rerender(<LoadingSpinner size="xl" />);
    expect(container.querySelector('.h-16')).toBeInTheDocument();
  });

  test('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('has proper accessibility attributes', () => {
    render(<LoadingSpinner text="Loading data..." />);
    
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-label', 'Loading data...');
    
    const srText = screen.getByText('Loading data...', { selector: '.sr-only' });
    expect(srText).toBeInTheDocument();
  });

  test('has animation classes', () => {
    const { container } = render(<LoadingSpinner />);
    
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('rounded-full', 'border-2', 'border-gray-300', 'border-t-primary-600');
  });
});