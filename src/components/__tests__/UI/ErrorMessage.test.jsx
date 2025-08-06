import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorMessage from '../../UI/ErrorMessage';

describe('ErrorMessage', () => {
  test('renders with default props', () => {
    render(<ErrorMessage message="Something went wrong" />);
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  test('renders with custom title', () => {
    render(<ErrorMessage title="Custom Error" message="Test message" />);
    
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
  });

  test('renders different types correctly', () => {
    const { rerender, container } = render(
      <ErrorMessage type="error" message="Error message" />
    );
    expect(container.firstChild).toHaveClass('bg-red-50', 'border-red-200');

    rerender(<ErrorMessage type="warning" message="Warning message" />);
    expect(container.firstChild).toHaveClass('bg-yellow-50', 'border-yellow-200');

    rerender(<ErrorMessage type="info" message="Info message" />);
    expect(container.firstChild).toHaveClass('bg-blue-50', 'border-blue-200');
  });

  test('renders without message', () => {
    render(<ErrorMessage title="Just a title" />);
    
    expect(screen.getByText('Just a title')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  test('calls onRetry when retry button is clicked', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage message="Failed" onRetry={mockRetry} />);
    
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);
    
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  test('calls onDismiss when dismiss button is clicked', () => {
    const mockDismiss = jest.fn();
    render(<ErrorMessage message="Failed" onDismiss={mockDismiss} />);
    
    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);
    
    expect(mockDismiss).toHaveBeenCalledTimes(1);
  });

  test('calls onDismiss when close X button is clicked', () => {
    const mockDismiss = jest.fn();
    render(<ErrorMessage message="Failed" onDismiss={mockDismiss} />);
    
    const closeButton = screen.getByLabelText('Dismiss');
    fireEvent.click(closeButton);
    
    expect(mockDismiss).toHaveBeenCalledTimes(1);
  });

  test('renders both retry and dismiss buttons', () => {
    const mockRetry = jest.fn();
    const mockDismiss = jest.fn();
    render(<ErrorMessage message="Failed" onRetry={mockRetry} onDismiss={mockDismiss} />);
    
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
    expect(screen.getByLabelText('Dismiss')).toBeInTheDocument(); // X button
  });

  test('applies custom className', () => {
    const { container } = render(<ErrorMessage message="Test" className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('has proper accessibility attributes', () => {
    render(<ErrorMessage message="Error occurred" />);
    
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
  });

  test('renders appropriate icons for different types', () => {
    const { rerender } = render(<ErrorMessage type="error" message="Error" />);
    expect(document.querySelector('svg')).toBeInTheDocument();

    rerender(<ErrorMessage type="warning" message="Warning" />);
    expect(document.querySelector('svg')).toBeInTheDocument();

    rerender(<ErrorMessage type="info" message="Info" />);
    expect(document.querySelector('svg')).toBeInTheDocument();
  });
});