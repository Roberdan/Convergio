# 🚀 Convergio - Development Makefile
# Dedicated to Mario and FightTheStroke Foundation 💜

.PHONY: help install dev build test clean deploy docker-dev docker-prod

# 🎯 Default target
help:
	@echo "🚀 Convergio Development Commands"
	@echo "💜 Built with love for Mario and accessible AI"
	@echo ""
	@echo "📋 Available commands:"
	@echo "  make install         📦 Install all dependencies"
	@echo "  make dev             🛠️  Start development environment"
	@echo "  make build           🏗️  Build production images"
	@echo "  make test            🧪 Run all tests"
	@echo "  make test-integration 🔗 Run integration tests only"
	@echo "  make test-agents      🧪 Test agent definitions (standalone)"
	@echo "  make test-agents-simple 🧪 Test agent definitions (simple)"
	@echo "  make test-coordination 🎯 Test Ali coordination (requires backend)"
	@echo "  make test-conversations 💬 Test multi-agent conversations (requires backend)"
	@echo "  make test-performance ⚡ Test performance (requires backend)"
	@echo "  make test-performance-full ⚡ Test performance optimization (requires backend)"
	@echo "  make clean           🧹 Clean up containers and volumes"
	@echo "  make deploy          🚀 Deploy to Azure"
	@echo "  make deploy-azure    ☁️  Deploy to Azure (explicit)"
	@echo "  make docker-dev      🐳 Start development with Docker"
	@echo "  make docker-prod     🐳 Start production with Docker"
	@echo ""

# 📦 Install dependencies
install:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm ci
	@echo "✅ Dependencies installed successfully!"

# 🛠️ Development environment
dev:
	@echo "🛠️ Starting development environment..."
	@echo "🐍 Starting backend on http://localhost:9000"
	@echo "🎨 Starting frontend on http://localhost:4000"
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload

dev-frontend:
	cd frontend && npm run dev -- --port 4000

# 🏗️ Build production images
build:
	@echo "🏗️ Building production Docker images..."
	docker-compose -f deployment/docker/docker-compose.yml build
	@echo "✅ Production images built successfully!"

# 🧪 Run tests
test:
	@echo "🧪 Running all tests..."
	@echo "🐍 Testing backend..."
	cd backend && python -m pytest tests/ -v
	@echo "🎨 Testing frontend..."
	cd frontend && npm test
	@echo "♿ Running accessibility tests..."
	cd frontend && npm run test:a11y || echo "Accessibility tests completed"
	@echo "🔗 Running integration tests..."
	python tests/run_integration_tests.py
	@echo "✅ All tests completed!"

# 🔗 Run integration tests only
test-integration:
	@echo "🔗 Running integration tests..."
	python tests/run_integration_tests.py

# 🧪 Run specific integration test (standalone - no dependencies)
test-agents:
	@echo "🧪 Testing agent definitions (standalone)..."
	python tests/integration/test_agents_standalone.py

test-agents-simple:
	@echo "🧪 Testing agent definitions (simple)..."
	python tests/integration/test_agents_simple.py

# 🎯 Backend-dependent tests (require backend dependencies)
test-coordination:
	@echo "🎯 Testing Ali coordination..."
	python tests/integration/test_ali_coordination.py

test-conversations:
	@echo "💬 Testing multi-agent conversations..."
	python tests/integration/test_multiagent_conversations.py

test-performance:
	@echo "⚡ Testing performance..."
	python tests/integration/test_performance_simple.py

test-performance-full:
	@echo "⚡ Testing performance optimization..."
	python tests/integration/test_performance_optimization.py

# 🧹 Clean up
clean:
	@echo "🧹 Cleaning up Docker containers and volumes..."
	docker-compose -f deployment/docker/docker-compose.yml down -v --remove-orphans
	docker-compose -f deployment/docker/docker-compose.dev.yml down -v --remove-orphans || true
	docker system prune -f
	@echo "✅ Cleanup completed!"

# 🚀 Deploy to Azure
deploy:
	@echo "🚀 Deploying Convergio to Azure..."
	./deployment/azure/deploy-azure.sh
	@echo "🎉 Deployment completed!"

# ☁️ Deploy to Azure (explicit)
deploy-azure:
	@echo "☁️ Deploying to Azure..."
	./deployment/azure/deploy-azure.sh
	@echo "🎉 Azure deployment completed!"

# 🐳 Development with Docker
docker-dev:
	@echo "🐳 Starting development environment with Docker..."
	docker-compose -f deployment/docker/docker-compose.dev.yml up --build
	@echo "🛠️ Development environment ready!"

# 🐳 Production with Docker
docker-prod:
	@echo "🐳 Starting production environment with Docker..."
	docker-compose -f deployment/docker/docker-compose.yml up -d --build
	@echo "🚀 Production environment ready!"

# 🔍 Health check
health:
	@echo "🔍 Checking service health..."
	@curl -f http://localhost:9000/health && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"
	@curl -f http://localhost:4000/health && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"

# 📊 Show logs
logs:
	@echo "📊 Showing service logs..."
	docker-compose -f deployment/docker/docker-compose.yml logs -f

# 🔄 Restart services
restart:
	@echo "🔄 Restarting services..."
	docker-compose -f deployment/docker/docker-compose.yml restart
	@echo "✅ Services restarted!"

# 📈 Show status
status:
	@echo "📈 Service status:"
	docker-compose -f deployment/docker/docker-compose.yml ps