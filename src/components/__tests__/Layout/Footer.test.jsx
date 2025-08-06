import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Footer from '../../Layout/Footer';

describe('Footer', () => {
  test('renders copyright with current year', () => {
    render(<Footer />);
    
    const currentYear = new Date().getFullYear();
    expect(screen.getByText(`© ${currentYear} AEO Booster. All rights reserved.`)).toBeInTheDocument();
  });

  test('renders about section', () => {
    render(<Footer />);
    
    expect(screen.getByText('About AEO Booster')).toBeInTheDocument();
    expect(screen.getByText(/Helping businesses optimize their online presence/)).toBeInTheDocument();
  });

  test('renders resources section with links', () => {
    render(<Footer />);
    
    expect(screen.getByText('Resources')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'How It Works' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Best Practices' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'FAQ' })).toBeInTheDocument();
  });

  test('renders support section with links', () => {
    render(<Footer />);
    
    expect(screen.getByText('Support')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Documentation' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact Us' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeInTheDocument();
  });

  test('has proper semantic structure', () => {
    render(<Footer />);
    
    const footer = screen.getByRole('contentinfo');
    expect(footer).toBeInTheDocument();
    expect(footer).toHaveClass('bg-white', 'border-t', 'border-gray-200');
  });

  test('has responsive grid layout', () => {
    const { container } = render(<Footer />);
    
    const gridContainer = container.querySelector('.grid');
    expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-3', 'gap-8');
  });

  test('renders tagline', () => {
    render(<Footer />);
    
    expect(screen.getByText('Built for the AI-first web')).toBeInTheDocument();
  });
});