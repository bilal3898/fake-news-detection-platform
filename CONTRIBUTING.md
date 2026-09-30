# Contributing to Fake News Detection Platform

Thank you for your interest in contributing to our Fake News Detection Platform! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git
- Basic knowledge of Python, JavaScript, and machine learning

### Setup Development Environment

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/fake-news-detection-platform.git
   cd fake-news-detection-platform
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set Up Environment**
   ```bash
   cp env.example .env
   # Edit .env with your local configuration
   ```

5. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## 📝 Development Guidelines

### Code Standards

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Maximum line length: 88 characters (Black default)

```python
from typing import Dict, Any, Optional

def predict_news(text: str, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Predict whether news text is fake or real.
    
    Args:
        text: The news article text to analyze
        title: Optional title of the news article
        
    Returns:
        Dictionary containing prediction results with confidence scores
    """
    # Implementation here
    pass
```

#### JavaScript (Frontend)
- Use ES6+ features
- Follow Airbnb style guide
- Use functional components with hooks
- Include PropTypes for components

```jsx
import React from 'react';
import PropTypes from 'prop-types';

const ResultCard = ({ prediction, confidence, onRetry }) => {
  return (
    <div className="result-card">
      {/* Component JSX */}
    </div>
  );
};

ResultCard.propTypes = {
  prediction: PropTypes.string.isRequired,
  confidence: PropTypes.number.isRequired,
  onRetry: PropTypes.func,
};

export default ResultCard;
```

### Testing

#### Backend Tests
- Write unit tests for all new functions
- Use pytest framework
- Aim for 80%+ test coverage

```python
import pytest
from backend.services.prediction_final import final_prediction_service

class TestPredictionService:
    def test_predict_fake_news(self):
        """Test prediction of fake news"""
        text = "Scientists discover miracle cure for cancer overnight"
        result = final_prediction_service.predict(text)
        
        assert result['prediction'] == 'FAKE'
        assert result['confidence'] > 0.7
    
    def test_predict_real_news(self):
        """Test prediction of real news"""
        text = "Researchers publish study on artificial intelligence in Nature journal"
        result = final_prediction_service.predict(text)
        
        assert result['prediction'] == 'REAL'
        assert result['confidence'] > 0.7
```

#### Frontend Tests
- Use React Testing Library
- Test component behavior, not implementation
- Mock API calls in tests

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import ResultCard from '../ResultCard';

describe('ResultCard', () => {
  test('displays prediction result correctly', () => {
    const mockProps = {
      prediction: 'FAKE',
      confidence: 0.85,
      onRetry: jest.fn(),
    };
    
    render(<ResultCard {...mockProps} />);
    
    expect(screen.getByText('FAKE')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });
});
```

### Git Workflow

#### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring

#### Commit Messages
Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(backend): add fallback analysis for JavaScript errors
fix(frontend): resolve prediction display issue
docs(readme): update installation instructions
test(prediction): add unit tests for fake news detection
```

#### Pull Request Process
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-new-ml-model
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "feat(ml): add new transformer model for better accuracy"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/add-new-ml-model
   # Create pull request on GitHub
   ```

4. **PR Requirements**
   - Clear title and description
   - Link to relevant issues
   - All tests passing
   - Code coverage maintained
   - Documentation updated

## 🐛 Bug Reports

### Reporting Bugs
1. **Search Existing Issues** - Check if bug already reported
2. **Create New Issue** with:
   - Clear, descriptive title
   - Detailed description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Screenshots if applicable

### Bug Report Template
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Go to...
2. Click on...
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 10, macOS 13.0]
- Browser: [e.g., Chrome 119, Firefox 120]
- Python Version: [e.g., 3.11.0]
- Node Version: [e.g., 18.17.0]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Proposing Features
1. **Discuss First** - Open issue for discussion before implementation
2. **Provide Rationale** - Explain why feature is needed
3. **Consider Alternatives** - Discuss different approaches
4. **Implementation Plan** - Outline how to implement

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How should the feature work?

## Alternatives Considered
Other approaches that were considered

## Additional Context
Any other relevant information
```

## 📚 Documentation

### Documentation Types
- **API Documentation**: Auto-generated from docstrings
- **User Documentation**: README, guides, tutorials
- **Developer Documentation**: Architecture, setup, contributing

### Writing Documentation
- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Keep documentation up to date

## 🔧 Development Tools

### Pre-commit Hooks
- Black for code formatting
- Flake8 for linting
- MyPy for type checking
- Tests for validation

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_prediction.py

# Run frontend tests
cd frontend && npm test
```

### Code Quality
```bash
# Format code
black backend/ frontend/

# Lint code
flake8 backend/
eslint frontend/src/

# Type checking
mypy backend/
```

## 🏗️ Architecture Guidelines

### Backend Architecture
- **Services**: Business logic in service classes
- **Routes**: API endpoints in route modules
- **Models**: Database models separate from business logic
- **Middleware**: Cross-cutting concerns in middleware

### Frontend Architecture
- **Components**: Reusable UI components
- **Pages**: Route-level components
- **Hooks**: Custom hooks for shared logic
- **Utils**: Utility functions

### Database Guidelines
- Use migrations for schema changes
- Include indexes for performance
- Use appropriate data types
- Document table relationships

## 🚀 Deployment

### Development Deployment
```bash
# Start backend
python -m backend.app

# Start frontend
cd frontend && npm start

# Start services
docker-compose up -d redis postgres mongodb
```

### Production Deployment
- Use Docker containers
- Environment-specific configurations
- Database migrations
- Health checks and monitoring

## 📊 Performance Guidelines

### Backend Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Optimize database queries
- Monitor response times

### Frontend Performance
- Lazy load components
- Optimize bundle size
- Use React.memo for expensive components
- Implement virtual scrolling for lists

## 🔒 Security Guidelines

### Backend Security
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Secure authentication

### Frontend Security
- Sanitize user inputs
- Use HTTPS in production
- Implement CSP headers
- Secure cookie handling

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Maintain professional behavior

### Getting Help
- Check documentation first
- Search existing issues
- Ask questions in discussions
- Join community channels

## 📈 Recognition

### Contributor Recognition
- Contributors listed in README
- Featured in release notes
- Badges for significant contributions
- Annual contributor awards

### Types of Contributions
- Code contributions
- Documentation improvements
- Bug reports and testing
- Community support
- Design and UX improvements

## 📞 Contact

### Getting in Touch
- **Issues**: For bugs and feature requests
- **Discussions**: For general questions and ideas
- **Email**: support@fakenews-detection.com
- **Discord**: Community server link

---

Thank you for contributing to the Fake News Detection Platform! Your contributions help make this project better for everyone. 🎉
