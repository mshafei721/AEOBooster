import React from 'react';
import InputForm from './components/InputForm';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AEO Booster</h1>
          <p className="text-lg text-gray-600">Optimize your website for AI chatbot recommendations</p>
        </header>
        
        <main className="max-w-2xl mx-auto">
          <InputForm />
        </main>
      </div>
    </div>
  );
}

export default App;