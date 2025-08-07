# 🤝 Contributing to Convergio

> **Welcome to the future of AI-powered business orchestration!** We're excited to have you contribute to Convergio.

---

## 🌟 **Our Mission**

Convergio democratizes access to enterprise-level AI expertise through 40+ specialized agents. Every contribution helps make advanced business intelligence accessible to startups, solopreneurs, and growing companies worldwide.

### 💜 **Inspired by Mario**
This project is dedicated to Mario and the FightTheStroke Foundation. We build with accessibility, inclusivity, and human dignity at the core of every decision.

---

## 🚀 **Quick Start for Contributors**

### 📋 **Prerequisites**
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Git

### ⚡ **Development Setup**
```bash
# 1. Fork and clone
git clone https://github.com/Roberdan/Convergio.git
cd Convergio

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend setup
cd ../frontend
npm install

# 4. Environment setup
cp .env.example .env
# Edit .env with your API keys and database credentials

# 5. Start services
# Terminal 1: Backend
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 9000

# Terminal 2: Frontend
cd frontend && npm run dev -- --port 4000
```

---

## 🎯 **How to Contribute**

### 🐛 **Bug Reports**
Found a bug? Help us fix it!

1. **Search existing issues** first
2. **Use our bug report template**
3. **Include reproduction steps**
4. **Add screenshots/logs** if relevant
5. **Test with latest version**

### ✨ **Feature Requests**
Have an idea for a new agent or feature?

1. **Check our roadmap** in README.md
2. **Use our feature request template**
3. **Explain the business value**
4. **Consider accessibility impact**
5. **Propose implementation approach**

### 🔧 **Code Contributions**

#### **Development Workflow**
```bash
# 1. Create feature branch
git checkout -b feature/amazing-new-agent

# 2. Make your changes
# Follow our coding standards below

# 3. Test thoroughly
cd backend && python -m pytest
cd frontend && npm test

# 4. Commit with conventional commits
git commit -m "feat(agents): add marketing automation agent

- Implements email campaign optimization
- Adds social media scheduling
- Includes ROI tracking and analytics
- Follows accessibility guidelines"

# 5. Push and create PR
git push origin feature/amazing-new-agent
```

#### **Pull Request Guidelines**
- **One feature per PR**
- **Clear, descriptive title**
- **Detailed description** with context
- **Link related issues**
- **Include tests** for new functionality
- **Update documentation** if needed
- **Ensure accessibility compliance**

---

## 📝 **Coding Standards**

### 🐍 **Python (Backend)**
```python
# Follow PEP 8 with these specifics:
# - Line length: 88 characters (Black formatter)
# - Use type hints
# - Docstrings for all public functions
# - Async/await for I/O operations

async def create_agent_response(
    agent_id: str, 
    message: str, 
    context: Optional[Dict[str, Any]] = None
) -> AgentResponse:
    """
    Generate response from specified agent.
    
    Args:
        agent_id: Unique identifier for the agent
        message: User input message
        context: Optional conversation context
        
    Returns:
        AgentResponse with generated content and metadata
    """
    # Implementation here
```

### 🌐 **TypeScript (Frontend)**
```typescript
// Use strict TypeScript
// - Explicit types for all parameters
// - Interface definitions for complex objects
// - JSDoc comments for public functions

interface AgentMessage {
  id: string;
  agentId: string;
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

/**
 * Sends message to specified agent and handles streaming response
 */
export async function sendAgentMessage(
  agentId: string, 
  message: string
): Promise<AgentMessage> {
  // Implementation here
}
```

### 🎨 **UI/UX Guidelines**
- **Accessibility First**: WCAG 2.1 AA compliance mandatory
- **High Contrast**: Ensure readability for all users
- **Keyboard Navigation**: All features accessible via keyboard
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Mobile Responsive**: Works on all device sizes
- **Loading States**: Clear feedback for all async operations

---

## 🤖 **Agent Development Guidelines**

### 🧠 **Creating New Agents**
```python
# Agent template structure
class NewAgent(BaseAgent):
    """
    Brief description of agent purpose and capabilities.
    
    Specialization: [Domain area]
    Tools: [List of available tools]
    Use Cases: [Primary use cases]
    """
    
    def __init__(self):
        super().__init__(
            name="Agent Name",
            role="Specific Role",
            specialization="Domain Area",
            tools=["tool1", "tool2"],
            personality="Professional, helpful, domain-expert"
        )
    
    async def process_request(self, request: str) -> AgentResponse:
        """Process user request and return structured response."""
        # Implementation with proper error handling
        # Include reasoning and source attribution
        # Ensure accessibility in responses
```

### 🛡️ **Security Requirements for Agents**
- **Input Validation**: All user inputs must be sanitized
- **Prompt Injection Protection**: Use Guardian Agent validation
- **Rate Limiting**: Implement per-agent rate limits
- **Audit Logging**: Log all agent interactions
- **Error Handling**: Never expose internal system details

### 🎯 **Agent Quality Standards**
- **CEO-Ready Responses**: Clear, actionable, business-focused
- **Source Attribution**: Always cite information sources
- **Follow-up Suggestions**: Proactive next steps
- **Error Recovery**: Graceful handling of failures
- **Context Awareness**: Maintain conversation context

---

## 🧪 **Testing Guidelines**

### 🔬 **Test Categories**
```bash
# Unit tests (required for all new code)
cd backend && python -m pytest tests/unit/

# Integration tests (required for API changes)
cd backend && python -m pytest tests/integration/

# End-to-end tests (required for UI changes)
cd frontend && npm run test:e2e

# Accessibility tests (required for all UI changes)
cd frontend && npm run test:a11y
```

### 📊 **Coverage Requirements**
- **Backend**: Minimum 90% test coverage
- **Frontend**: Minimum 85% component coverage
- **Critical Paths**: 100% coverage for security and agent interactions
- **Accessibility**: All UI components must pass a11y tests

### 🎭 **Test Writing Guidelines**
```python
# Backend test example
async def test_agent_response_accessibility():
    """Test that agent responses include accessibility metadata."""
    agent = MarketingAgent()
    response = await agent.process_request("Create campaign strategy")
    
    assert response.accessibility_score >= 0.9
    assert response.screen_reader_friendly is True
    assert len(response.alt_text_suggestions) > 0
```

---

## 📚 **Documentation Standards**

### 📖 **Documentation Requirements**
- **API Changes**: Update OpenAPI specs
- **New Agents**: Add to agent directory in README
- **Configuration**: Update environment variables documentation
- **Accessibility**: Document accessibility features and testing

### 🎨 **Documentation Style**
- **Clear Headings**: Use emoji + descriptive titles
- **Code Examples**: Include working code snippets
- **Screenshots**: Add visual examples where helpful
- **Accessibility Notes**: Mention accessibility considerations

---

## 🌍 **Accessibility & Inclusivity**

### ♿ **Accessibility Requirements**
Every contribution must consider:
- **Visual Impairments**: Screen reader compatibility, high contrast
- **Motor Impairments**: Keyboard navigation, large click targets
- **Cognitive Impairments**: Clear language, consistent navigation
- **Hearing Impairments**: Visual alternatives to audio cues

### 🌐 **Internationalization**
- **Text Externalization**: All user-facing text in i18n files
- **RTL Support**: Right-to-left language compatibility
- **Cultural Sensitivity**: Avoid cultural assumptions in examples
- **Timezone Awareness**: Handle multiple timezones correctly

---

## 🏆 **Recognition**

### 🌟 **Contributor Levels**
- **First-time Contributors**: Welcome package and mentorship
- **Regular Contributors**: Recognition in release notes
- **Core Contributors**: Direct collaboration on roadmap
- **Maintainers**: Full repository access and decision-making

### 🎉 **Recognition Programs**
- **Monthly Contributor Spotlight**: Featured in community updates
- **Annual Contributors**: Special recognition and swag
- **Accessibility Champions**: Extra recognition for inclusive contributions
- **Agent Creators**: Credit in agent documentation and UI

---

## 📞 **Getting Help**

### 💬 **Communication Channels**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat with maintainers (coming soon)
- **Email**: security@convergio.io for security issues

### 🆘 **Stuck? We're Here to Help!**
- **New to Open Source?** Check our "First Contribution" guide
- **Technical Questions?** Tag @maintainers in your issue
- **Accessibility Questions?** We have dedicated accessibility mentors
- **Agent Development?** Our AI team provides guidance

---

## 📜 **Code of Conduct**

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

### 🤝 **Our Values**
- **Respect**: Treat everyone with dignity and kindness
- **Inclusivity**: Welcome contributors from all backgrounds
- **Collaboration**: Work together towards common goals
- **Learning**: Support each other's growth and development
- **Accessibility**: Champion inclusive design in everything we do

### 📧 **Reporting Issues**
If you experience or witness unacceptable behavior, please report it to roberdan@fightthestroke.org. All reports will be handled with discretion and confidentiality.

---

## 🎯 **Current Priorities**

### 🔥 **High Priority**
- Agent Management System (CRUD editor with Ali assistance)
- Enhanced Agent Coordination (auto-coordination patterns)
- CEO Dashboard Supreme (executive analytics)

### 🌟 **Medium Priority**
- Multi-language support and internationalization
- Advanced GraphFlow workflow templates
- Custom agent creation tools

### 🔮 **Future Vision**
- Swarm intelligence and autonomous collaboration
- ML model integration and custom training
- AI talent marketplace and on-demand agents

---

## 💜 **A Message from the Team**

*"Every line of code you contribute helps democratize access to AI-powered business intelligence. You're not just building software - you're creating tools that empower entrepreneurs, support accessibility, and honor Mario's inspiring journey. Thank you for being part of this mission!"*

---

**Ready to contribute? Start with a good first issue labeled `good-first-issue` or `accessibility`!**

*Built with ❤️ for Mario and the global community*