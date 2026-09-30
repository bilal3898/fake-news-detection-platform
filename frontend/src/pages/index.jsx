import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NewsForm from '../components/NewsForm';
import ResultCard from '../components/ResultCard';
import ChartView from '../components/ChartView';

const HomePage = () => {
  const { isAuthenticated, user } = useAuth();
  const [result, setResult] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(false);
  // const [stats, setStats] = React.useState(null);

  // Sample chart data (would come from API in real app)
  const sampleChartData = [
    { name: 'Real News', value: 65 },
    { name: 'Fake News', value: 35 }
  ];

  const handleAnalysisSubmit = async (analysisData) => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock result based on input type
      const mockResult = {
        prediction: Math.random() > 0.5 ? 'REAL' : 'FAKE',
        confidence: Math.random() * 0.5 + 0.5, // 0.5 to 1.0
        probabilities: {
          real: Math.random(),
          fake: Math.random()
        },
        model_version: 'v1.0',
        processing_time: new Date().toISOString(),
        text_preview: analysisData.type === 'text' 
          ? analysisData.content.substring(0, 100) + '...'
          : 'URL content analysis'
      };
      
      setResult(mockResult);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeAnother = () => {
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-6">
            Detect Fake News with AI
          </h1>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Our advanced machine learning system analyzes news content to identify 
            fake news and misinformation with high accuracy.
          </p>
          
          {!isAuthenticated ? (
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                to="/register"
                className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Get Started Free
              </Link>
              <Link
                to="/login"
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
              >
                Sign In
              </Link>
            </div>
          ) : (
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 max-w-2xl mx-auto">
              <p className="text-lg mb-4">
                Welcome back, {user?.name || user?.email}! Ready to analyze some news?
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">
            Why Choose Our Fake News Detector?
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">AI-Powered Analysis</h3>
              <p className="text-gray-600">
                Advanced machine learning models trained on thousands of news articles 
                to detect patterns of misinformation.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Real-Time Results</h3>
              <p className="text-gray-600">
                Get instant analysis with detailed confidence scores and 
                probability breakdowns.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Privacy First</h3>
              <p className="text-gray-600">
                Your data is never stored or shared. All analysis happens 
                securely in real-time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Analysis Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">
            Analyze News Content
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
            {/* Input Form */}
            <div>
              <NewsForm 
                onSubmit={handleAnalysisSubmit}
                isLoading={isLoading}
              />
            </div>
            
            {/* Results or Stats */}
            <div>
              {result ? (
                <ResultCard 
                  result={result}
                  onAnalyzeAnother={handleAnalyzeAnother}
                  isLoading={isLoading}
                />
              ) : (
                <div className="space-y-6">
                  <ChartView 
                    data={sampleChartData}
                    chartType="pie"
                    title="Global Fake News Distribution"
                  />
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">
                      How It Works
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-start">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                          <span className="text-blue-600 font-bold">1</span>
                        </div>
                        <p className="text-gray-600">
                          Paste news text, enter URL, or upload a file
                        </p>
                      </div>
                      <div className="flex items-start">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                          <span className="text-blue-600 font-bold">2</span>
                        </div>
                        <p className="text-gray-600">
                          Our AI analyzes linguistic patterns and content features
                        </p>
                      </div>
                      <div className="flex items-start">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                          <span className="text-blue-600 font-bold">3</span>
                        </div>
                        <p className="text-gray-600">
                          Get instant results with confidence scores
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">
            Trusted by Thousands
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">50K+</div>
              <div className="text-gray-600">Articles Analyzed</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">95%</div>
              <div className="text-gray-600">Accuracy Rate</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">10K+</div>
              <div className="text-gray-600">Active Users</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600 mb-2">24/7</div>
              <div className="text-gray-600">Availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">
            Ready to Fight Misinformation?
          </h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Join thousands of users who trust our AI-powered fake news detection system.
          </p>
          
          {!isAuthenticated ? (
            <Link
              to="/register"
              className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors"
            >
              Start Analyzing Now - It's Free
            </Link>
          ) : (
            <div className="space-y-4">
              <p className="text-lg">
                You're all set! Start analyzing news content above.
              </p>
              <Link
                to="/dashboard"
                className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Go to Dashboard
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Fake News Detector</h3>
              <p className="text-gray-400">
                Advanced AI-powered solution to combat misinformation and fake news.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/" className="hover:text-white">Home</Link></li>
                <li><Link to="/about" className="hover:text-white">About</Link></li>
                <li><Link to="/privacy" className="hover:text-white">Privacy</Link></li>
                <li><Link to="/terms" className="hover:text-white">Terms</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/blog" className="hover:text-white">Blog</Link></li>
                <li><Link to="/docs" className="hover:text-white">API Docs</Link></li>
                <li><Link to="/help" className="hover:text-white">Help Center</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <p className="text-gray-400 mb-2">support@fakenewsdetector.com</p>
              <p className="text-gray-400">+1 (555) 123-4567</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Fake News Detector. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;