import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Header from '../../Layout/Header';

describe('Header', () => {
  test('renders AEO Booster brand name', () => {
    render(<Header />);
    
    expect(screen.getByRole('heading', { name: /aeo booster/i })).toBeInTheDocument();
  });

  test('renders subtitle', () => {
    render(<Header />);
    
    expect(screen.getByText('Optimize your website for AI chatbot recommendations')).toBeInTheDocument();
  });

  test('has proper semantic structure', () => {
    render(<Header />);
    
    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();
    
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
    expect(nav).toHaveAttribute('aria-label', 'Main navigation');
  });

  test('has responsive design classes', () => {
    const { container } = render(<Header />);
    
    const header = screen.getByRole('banner');
    expect(header).toHaveClass('bg-white', 'shadow-sm');
    
    const heading = screen.getByRole('heading');
    expect(heading).toHaveClass('text-2xl', 'md:text-3xl', 'lg:text-4xl');
  });

  test('brand name is properly structured', () => {
    render(<Header />);
    
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveClass('font-bold', 'text-gray-900');
  });
});