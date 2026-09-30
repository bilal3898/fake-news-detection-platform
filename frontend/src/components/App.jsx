import React, { useState } from 'react';
import NewsForm from './NewsForm';

function App() {
  const [isLoading, setIsLoading] = useState(false);

  // ✅ YE FUNCTION ADD KARO - BAHUT IMPORTANT HAI
  const handleNewsSubmit = async (newsData) => {
    console.log('Form data received:', newsData);
    setIsLoading(true);
    
    try {
      // Yahan par aapka analysis logic aayega
      // For now, simple simulation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Analysis completed for:', newsData.type);
      alert(`Analysis completed for ${newsData.type}! Check console for details.`);
      
    } catch (error) {
      console.error('Error in analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      {/* ✅ AB onSubmit PASS KARO */}
      <NewsForm 
        onSubmit={handleNewsSubmit}  // ← YE LINE ADD KARO
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;