import React from 'react';

const Header = () => {
  return (
    <header className="bg-white shadow-sm">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="flex items-center justify-between py-6">
          {/* Brand */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900">
                AEO Booster
              </h1>
            </div>
          </div>
          
          {/* Navigation - prepared for future navigation items */}
          <nav className="hidden sm:flex space-x-8" aria-label="Main navigation">
            {/* Future navigation items will go here */}
          </nav>
          
          {/* Mobile menu button - prepared for future use */}
          <div className="sm:hidden">
            {/* Future mobile menu button will go here */}
          </div>
        </div>
        
        {/* Subtitle */}
        <div className="pb-6">
          <p className="text-base md:text-lg text-gray-600 max-w-3xl">
            Optimize your website for AI chatbot recommendations
          </p>
        </div>
      </div>
    </header>
  );
};

export default Header;