import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProgressIndicator from '../../UI/ProgressIndicator';

describe('ProgressIndicator', () => {
  test('renders with default steps', () => {
    render(<ProgressIndicator currentStep={2} />);
    
    expect(screen.getByText('Input')).toBeInTheDocument();
    expect(screen.getByText('Crawling')).toBeInTheDocument();
    expect(screen.getByText('Analysis')).toBeInTheDocument();
    expect(screen.getByText('Scoring')).toBeInTheDocument();
    expect(screen.getByText('Results')).toBeInTheDocument();
  });

  test('renders with custom steps', () => {
    const customSteps = [
      { id: 1, name: 'Start', description: 'Begin process' },
      { id: 2, name: 'Process', description: 'Processing data' },
      { id: 3, name: 'Finish', description: 'Complete process' }
    ];
    
    render(<ProgressIndicator steps={customSteps} currentStep={2} />);
    
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('Process')).toBeInTheDocument();
    expect(screen.getByText('Finish')).toBeInTheDocument();
  });

  test('shows correct current step styling', () => {
    render(<ProgressIndicator currentStep={3} />);
    
    const currentStepElement = screen.getByText('Analysis').closest('div').querySelector('div');
    expect(currentStepElement).toHaveClass('bg-primary-100', 'text-primary-600', 'ring-2', 'ring-primary-600');
  });

  test('shows completed steps with checkmark', () => {
    render(<ProgressIndicator currentStep={3} />);
    
    // First step should be completed (has checkmark)
    const completedSteps = screen.getAllByRole('img', { hidden: true });
    expect(completedSteps.length).toBeGreaterThan(0);
  });

  test('has proper accessibility attributes', () => {
    render(<ProgressIndicator currentStep={2} totalSteps={5} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '2');
    expect(progressBar).toHaveAttribute('aria-valuemin', '1');
    expect(progressBar).toHaveAttribute('aria-valuemax', '5');
    expect(progressBar).toHaveAttribute('aria-label', 'Step 2 of 5');
    
    const currentStep = screen.getByText('Crawling').closest('div').querySelector('div');
    expect(currentStep).toHaveAttribute('aria-current', 'step');
  });

  test('calculates progress bar width correctly', () => {
    const { rerender } = render(<ProgressIndicator currentStep={1} totalSteps={5} />);
    let progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveStyle('width: 0%');

    rerender(<ProgressIndicator currentStep={3} totalSteps={5} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveStyle('width: 50%');

    rerender(<ProgressIndicator currentStep={5} totalSteps={5} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveStyle('width: 100%');
  });

  test('applies custom className', () => {
    const { container } = render(<ProgressIndicator className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('shows step descriptions on larger screens', () => {
    render(<ProgressIndicator currentStep={1} />);
    
    const description = screen.getByText('Enter website details');
    expect(description).toHaveClass('hidden', 'sm:block');
  });
});