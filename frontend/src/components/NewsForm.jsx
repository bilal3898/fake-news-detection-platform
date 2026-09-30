import React, { useState } from 'react';

const NewsForm = ({ onSubmit, isLoading = false }) => {
  const [inputType, setInputType] = useState('text');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (typeof onSubmit !== 'function') {
      console.warn('⚠️ NewsForm: onSubmit prop is not provided.');
      return;
    }

    if (!isFormValid()) {
      console.warn('Form is not valid');
      return;
    }

    if (inputType === 'text' && text.trim()) {
      onSubmit({ type: 'text', content: text.trim() });
      setText('');
    } else if (inputType === 'url' && url.trim()) {
      onSubmit({ type: 'url', content: url.trim() });
      setUrl('');
    } else if (inputType === 'file' && file) {
      onSubmit({ type: 'file', content: file });
      setFile(null);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Accept text files, documents, and image files
      const allowedTypes = [
        'text/plain', 'text/html', 'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp'
      ];
      const allowedExtensions = ['.txt', '.text', '.html', '.htm', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
      const fileExtension = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf('.'));
      
      if (allowedTypes.includes(selectedFile.type) || allowedExtensions.includes(fileExtension)) {
        setFile(selectedFile);
      } else {
        alert('Please select a valid file (.txt, .html, .pdf, .doc, .docx, .png, .jpg, .jpeg, .tiff, .bmp)');
        setFile(null);
      }
    } else {
      setFile(null);
    }
  };

  const isFormValid = () => {
    if (inputType === 'text') return text.trim().length > 10;
    if (inputType === 'url') return url.trim().length > 0;
    if (inputType === 'file') return file !== null;
    return false;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Analyze News Content
      </h2>

      {/* Input Type Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Input Method
        </label>
        <div className="flex space-x-4">
          {['text', 'url', 'file'].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setInputType(type)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                inputType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Text Input */}
        {inputType === 'text' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              News Text
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste news article text here..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <p className="text-sm text-gray-500 mt-1">
              Minimum 10 characters required
            </p>
          </div>
        )}

        {/* URL Input */}
        {inputType === 'url' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              News Article URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/news-article"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
        )}

        {/* File Input */}
        {inputType === 'file' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload File (Text, Documents, or Images)
            </label>
            <input
              type="file"
              accept=".txt,.text,.html,.htm,.pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.bmp"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              disabled={isLoading}
            />
            {file && (
              <div className="mt-2">
                <p className="text-sm text-green-600">
                  Selected: {file.name}
                </p>
                {file.type.startsWith('image/') && (
                  <p className="text-xs text-blue-600 mt-1">
                    📷 Image detected - Text will be extracted using OCR
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Submit Button + Warning */}
        <div className="space-y-2">
          <button
            type="submit"
            disabled={!isFormValid() || isLoading || typeof onSubmit !== 'function'}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Analyzing...
              </div>
            ) : (
              'Analyze News'
            )}
          </button>

          {typeof onSubmit !== 'function' && (
            <div className="p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm">
                ⚠️ This form is not connected to a handler. Please provide an onSubmit function.
              </p>
            </div>
          )}
        </div>
      </form>

      {/* Tips Section */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-semibold text-blue-800 mb-2">💡 Tips for Better Analysis</h4>
        <ul className="text-sm text-blue-600 space-y-1">
          <li>• Include complete articles for best results</li>
          <li>• Avoid very short text fragments</li>
          <li>• Use reputable news sources for URL analysis</li>
          <li>• The system works best with English content</li>
          <li>• For images: Use clear, high-resolution images with readable text</li>
          <li>• Supported image formats: PNG, JPG, JPEG, TIFF, BMP</li>
        </ul>
      </div>
    </div>
  );
};

export default NewsForm;