import React from 'react';
import PropTypes from 'prop-types';

const ProgressIndicator = ({ currentStep = 1, totalSteps = 5, steps, className = '' }) => {
  const defaultSteps = [
    { id: 1, name: 'Input', description: 'Enter website details' },
    { id: 2, name: 'Crawling', description: 'Analyzing website content' },
    { id: 3, name: 'Analysis', description: 'AI chatbot testing' },
    { id: 4, name: 'Scoring', description: 'Generating scores' },
    { id: 5, name: 'Results', description: 'Optimization report' }
  ];

  const progressSteps = steps || defaultSteps;

  return (
    <div className={`w-full ${className}`}>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {progressSteps.map((step, index) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;
            const isUpcoming = step.id > currentStep;

            return (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center">
                  {/* Step circle */}
                  <div
                    className={`
                      flex items-center justify-center w-8 h-8 md:w-10 md:h-10 rounded-full text-sm md:text-base font-medium
                      ${isCompleted 
                        ? 'bg-primary-600 text-white' 
                        : isCurrent 
                          ? 'bg-primary-100 text-primary-600 ring-2 ring-primary-600' 
                          : 'bg-gray-200 text-gray-500'
                      }
                    `}
                    aria-current={isCurrent ? 'step' : undefined}
                  >
                    {isCompleted ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      step.id
                    )}
                  </div>
                  
                  {/* Step label */}
                  <div className="mt-2 text-center">
                    <p className={`text-xs md:text-sm font-medium ${
                      isCurrent ? 'text-primary-600' : isCompleted ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {step.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 hidden sm:block">
                      {step.description}
                    </p>
                  </div>
                </div>
                
                {/* Connector line */}
                {index < progressSteps.length - 1 && (
                  <div className="flex-1 mx-2 md:mx-4">
                    <div 
                      className={`h-0.5 ${
                        step.id < currentStep ? 'bg-primary-600' : 'bg-gray-200'
                      }`}
                      aria-hidden="true"
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-primary-600 h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${((currentStep - 1) / (progressSteps.length - 1)) * 100}%` }}
          role="progressbar"
          aria-valuenow={currentStep}
          aria-valuemin={1}
          aria-valuemax={progressSteps.length}
          aria-label={`Step ${currentStep} of ${progressSteps.length}`}
        />
      </div>
    </div>
  );
};

ProgressIndicator.propTypes = {
  currentStep: PropTypes.number,
  totalSteps: PropTypes.number,
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
    })
  ),
  className: PropTypes.string,
};

export default ProgressIndicator;