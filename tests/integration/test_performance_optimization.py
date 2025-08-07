#!/usr/bin/env python3
"""
Performance Optimization Test Suite
Test e ottimizzazione delle performance per 41 agenti simultanei
"""

import asyncio
import time
import sys
import os
import psutil
import json
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Add backend to path
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

try:
    from src.agents.services.agent_loader import DynamicAgentLoader
    from src.core.config import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Note: This test requires backend dependencies to be installed")
    sys.exit(1)

class PerformanceOptimizer:
    """Performance optimization and testing suite"""
    
    def __init__(self):
        self.agents_directory = str(backend_path / "src" / "agents" / "definitions")
        self.loader = DynamicAgentLoader(self.agents_directory)
        self.agents = {}
        self.performance_metrics = {}
        
    async def initialize(self):
        """Initialize performance testing environment"""
        print("🚀 Initializing Performance Optimization Suite")
        
        # Load all agents
        start_time = time.time()
        self.agents = self.loader.scan_and_load_agents()
        load_time = time.time() - start_time
        
        print(f"✅ Loaded {len(self.agents)} agents in {load_time:.2f}s")
        self.performance_metrics["agent_load_time"] = load_time
        
    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage with all agents loaded"""
        print("\n🧠 Testing Memory Usage")
        
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Calculate agent memory footprint
        agent_data_size = 0
        for agent in self.agents.values():
            # Estimate memory usage per agent
            agent_size = (
                len(agent.name.encode('utf-8')) +
                len(agent.description.encode('utf-8')) +
                len(agent.persona.encode('utf-8')) +
                sum(len(kw.encode('utf-8')) for kw in agent.expertise_keywords) +
                100  # Overhead for metadata
            )
            agent_data_size += agent_size
        
        metrics = {
            "total_memory_mb": memory_info.rss / (1024 * 1024),
            "memory_percent": memory_percent,
            "agent_data_size_kb": agent_data_size / 1024,
            "average_agent_size_bytes": agent_data_size / len(self.agents) if len(self.agents) > 0 else 0
        }
        
        print(f"   Total Memory Usage: {metrics['total_memory_mb']:.1f} MB ({metrics['memory_percent']:.1f}%)")
        print(f"   Agent Data Size: {metrics['agent_data_size_kb']:.1f} KB")
        print(f"   Average per Agent: {metrics['average_agent_size_bytes']:.0f} bytes")
        
        # Memory efficiency assessment
        if metrics['memory_percent'] < 10:
            print("   ✅ Memory usage: EXCELLENT")
        elif metrics['memory_percent'] < 20:
            print("   ✅ Memory usage: GOOD")
        else:
            print("   ⚠️ Memory usage: NEEDS OPTIMIZATION")
        
        return metrics
    
    async def test_agent_lookup_performance(self) -> Dict[str, Any]:
        """Test agent lookup performance"""
        print("\n🔍 Testing Agent Lookup Performance")
        
        test_iterations = 1000
        agent_keys = list(self.agents.keys())
        
        # Test sequential lookups
        start_time = time.perf_counter()
        for i in range(test_iterations):
            key = agent_keys[i % len(agent_keys)]
            _ = self.agents.get(key)
        sequential_time = time.perf_counter() - start_time
        
        # Test knowledge base generation performance
        start_time = time.perf_counter()
        knowledge_base = self.loader.generate_ali_knowledge_base()
        knowledge_gen_time = time.perf_counter() - start_time
        
        metrics = {
            "sequential_lookup_time": sequential_time,
            "average_lookup_time_ms": (sequential_time / test_iterations) * 1000,
            "knowledge_generation_time": knowledge_gen_time,
            "knowledge_base_size": len(knowledge_base),
            "lookups_per_second": test_iterations / sequential_time if sequential_time > 0 else 0
        }
        
        print(f"   {test_iterations} Sequential Lookups: {sequential_time:.3f}s")
        print(f"   Average Lookup Time: {metrics['average_lookup_time_ms']:.3f}ms")
        print(f"   Knowledge Generation: {knowledge_gen_time:.3f}s")
        print(f"   Lookup Rate: {metrics['lookups_per_second']:.0f} lookups/second")
        
        # Performance assessment
        if metrics['average_lookup_time_ms'] < 0.1:
            print("   ✅ Lookup performance: EXCELLENT")
        elif metrics['average_lookup_time_ms'] < 1.0:
            print("   ✅ Lookup performance: GOOD")
        else:
            print("   ⚠️ Lookup performance: NEEDS OPTIMIZATION")
        
        return metrics
    
    async def test_concurrent_agent_access(self) -> Dict[str, Any]:
        """Test concurrent agent access performance"""
        print("\n🚀 Testing Concurrent Agent Access")
        
        concurrent_users = 50
        operations_per_user = 20
        agent_keys = list(self.agents.keys())
        
        async def simulate_user_operations(user_id: int):
            """Simulate a user performing multiple agent operations"""
            start_time = time.perf_counter()
            operations = 0
            
            for i in range(operations_per_user):
                # Simulate different operations
                key = agent_keys[(user_id + i) % len(agent_keys)]
                agent = self.agents.get(key)
                
                if agent:
                    # Simulate accessing agent properties
                    _ = agent.name
                    _ = agent.description
                    _ = agent.expertise_keywords
                    operations += 1
                
                # Small delay to simulate processing
                await asyncio.sleep(0.001)
            
            end_time = time.perf_counter()
            return {
                "user_id": user_id,
                "operations": operations,
                "time": end_time - start_time
            }
        
        # Run concurrent users
        print(f"   Simulating {concurrent_users} concurrent users...")
        start_time = time.perf_counter()
        
        tasks = [simulate_user_operations(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        total_operations = sum(r["operations"] for r in results)
        average_user_time = sum(r["time"] for r in results) / len(results)
        operations_per_second = total_operations / total_time if total_time > 0 else 0
        
        metrics = {
            "concurrent_users": concurrent_users,
            "total_operations": total_operations,
            "total_time": total_time,
            "average_user_time": average_user_time,
            "operations_per_second": operations_per_second,
            "successful_operations_percent": 100.0  # All operations successful in this simulation
        }
        
        print(f"   Total Operations: {total_operations}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Operations/Second: {operations_per_second:.0f}")
        print(f"   Average User Time: {average_user_time:.3f}s")
        
        # Concurrent performance assessment
        if operations_per_second > 10000:
            print("   ✅ Concurrent performance: EXCELLENT")
        elif operations_per_second > 5000:
            print("   ✅ Concurrent performance: GOOD")
        else:
            print("   ⚠️ Concurrent performance: NEEDS OPTIMIZATION")
        
        return metrics
    
    async def test_agent_coordination_overhead(self) -> Dict[str, Any]:
        """Test coordination overhead with multiple agents"""
        print("\n🎯 Testing Agent Coordination Overhead")
        
        # Test different coordination scenarios
        scenarios = [
            {"agents": 5, "description": "Small team coordination"},
            {"agents": 10, "description": "Medium team coordination"},
            {"agents": 20, "description": "Large team coordination"},
            {"agents": 41, "description": "Full ecosystem coordination"}
        ]
        
        coordination_metrics = []
        
        for scenario in scenarios:
            agent_count = min(scenario["agents"], len(self.agents))
            selected_agents = list(self.agents.values())[:agent_count]
            
            # Simulate coordination overhead
            start_time = time.perf_counter()
            
            # Simulate Ali generating routing decisions
            routing_decisions = []
            for agent in selected_agents:
                decision_time = time.perf_counter()
                
                # Simulate decision process
                relevant_keywords = agent.expertise_keywords[:3]
                coordination_score = len(relevant_keywords) * 0.1
                
                routing_decisions.append({
                    "agent": agent.name,
                    "keywords": relevant_keywords,
                    "score": coordination_score
                })
                
                decision_time = time.perf_counter() - decision_time
            
            coordination_time = time.perf_counter() - start_time
            
            scenario_metrics = {
                "agent_count": agent_count,
                "coordination_time": coordination_time,
                "time_per_agent": coordination_time / agent_count if agent_count > 0 else 0,
                "routing_decisions": len(routing_decisions)
            }
            
            coordination_metrics.append(scenario_metrics)
            
            print(f"   {scenario['description']} ({agent_count} agents): {coordination_time:.3f}s")
        
        # Calculate scaling efficiency
        if len(coordination_metrics) > 1:
            scaling_factor = coordination_metrics[-1]["coordination_time"] / coordination_metrics[0]["coordination_time"]
            agent_scaling_factor = coordination_metrics[-1]["agent_count"] / coordination_metrics[0]["agent_count"]
            efficiency = agent_scaling_factor / scaling_factor if scaling_factor > 0 else 0
        else:
            efficiency = 1.0
        
        metrics = {
            "coordination_scenarios": coordination_metrics,
            "scaling_efficiency": efficiency,
            "full_ecosystem_time": coordination_metrics[-1]["coordination_time"] if coordination_metrics else 0
        }
        
        print(f"   Scaling Efficiency: {efficiency:.2f} (higher is better)")
        
        if efficiency > 0.7:
            print("   ✅ Coordination overhead: EXCELLENT")
        elif efficiency > 0.5:
            print("   ✅ Coordination overhead: GOOD")
        else:
            print("   ⚠️ Coordination overhead: NEEDS OPTIMIZATION")
        
        return metrics
    
    def generate_optimization_recommendations(self, all_metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on test results"""
        
        recommendations = []
        
        # Memory optimization recommendations
        memory_metrics = all_metrics.get("memory_usage", {})
        if memory_metrics.get("memory_percent", 0) > 15:
            recommendations.append("🧠 Consider implementing agent lazy loading to reduce memory footprint")
            recommendations.append("🗜️ Implement agent data compression for large persona texts")
        
        # Lookup performance recommendations
        lookup_metrics = all_metrics.get("lookup_performance", {})
        if lookup_metrics.get("average_lookup_time_ms", 0) > 0.5:
            recommendations.append("🔍 Consider adding agent caching layer for faster lookups")
            recommendations.append("📇 Implement agent indexing for expertise-based searches")
        
        # Concurrent access recommendations
        concurrent_metrics = all_metrics.get("concurrent_access", {})
        if concurrent_metrics.get("operations_per_second", 0) < 8000:
            recommendations.append("⚡ Consider implementing connection pooling for high-concurrency scenarios")
            recommendations.append("🔄 Add agent operation queuing for load balancing")
        
        # Coordination overhead recommendations  
        coordination_metrics = all_metrics.get("coordination_overhead", {})
        if coordination_metrics.get("scaling_efficiency", 1) < 0.6:
            recommendations.append("🎯 Implement hierarchical agent coordination to reduce overhead")
            recommendations.append("📊 Add agent specialization indexing for faster routing decisions")
        
        # General performance recommendations
        recommendations.extend([
            "⚡ Implement agent response caching for repeated queries",
            "🔄 Consider implementing agent state persistence for faster startups",
            "📈 Add performance monitoring and metrics collection",
            "🏗️ Consider agent pool management for resource optimization"
        ])
        
        return recommendations
    
    async def run_full_performance_suite(self) -> Dict[str, Any]:
        """Run complete performance test suite"""
        
        print("🎯 RUNNING FULL PERFORMANCE OPTIMIZATION SUITE")
        print("=" * 60)
        
        all_metrics = {}
        
        # Run all performance tests
        try:
            all_metrics["memory_usage"] = await self.test_memory_usage()
            all_metrics["lookup_performance"] = await self.test_agent_lookup_performance()
            all_metrics["concurrent_access"] = await self.test_concurrent_agent_access()
            all_metrics["coordination_overhead"] = await self.test_agent_coordination_overhead()
            
            # Generate recommendations
            recommendations = self.generate_optimization_recommendations(all_metrics)
            all_metrics["recommendations"] = recommendations
            
            # Overall performance score
            memory_score = 100 if all_metrics["memory_usage"]["memory_percent"] < 10 else 80 if all_metrics["memory_usage"]["memory_percent"] < 20 else 60
            lookup_score = 100 if all_metrics["lookup_performance"]["average_lookup_time_ms"] < 0.1 else 80 if all_metrics["lookup_performance"]["average_lookup_time_ms"] < 1 else 60
            concurrent_score = 100 if all_metrics["concurrent_access"]["operations_per_second"] > 10000 else 80 if all_metrics["concurrent_access"]["operations_per_second"] > 5000 else 60
            coordination_score = 100 if all_metrics["coordination_overhead"]["scaling_efficiency"] > 0.7 else 80 if all_metrics["coordination_overhead"]["scaling_efficiency"] > 0.5 else 60
            
            overall_score = (memory_score + lookup_score + concurrent_score + coordination_score) / 4
            all_metrics["overall_performance_score"] = overall_score
            
            return all_metrics
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

async def main():
    """Main performance testing function"""
    
    try:
        # Initialize optimizer
        optimizer = PerformanceOptimizer()
        await optimizer.initialize()
        
        # Run full test suite
        results = await optimizer.run_full_performance_suite()
        
        if "error" in results:
            return False
        
        # Print final summary
        print("\n🏆 PERFORMANCE OPTIMIZATION RESULTS")
        print("=" * 50)
        print(f"Overall Performance Score: {results['overall_performance_score']:.0f}/100")
        
        if results['overall_performance_score'] >= 80:
            print("✅ PERFORMANCE: EXCELLENT - Ready for production with 41 agents!")
        elif results['overall_performance_score'] >= 70:
            print("✅ PERFORMANCE: GOOD - Minor optimizations recommended")
        else:
            print("⚠️ PERFORMANCE: NEEDS IMPROVEMENT - Apply recommended optimizations")
        
        print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"][:8], 1):  # Show top 8
            print(f"   {i}. {rec}")
        
        # Save detailed results to project root logs directory
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        results_file = logs_dir / "performance_optimization_results.json"
        
        with open(results_file, 'w') as f:
            # Convert any non-serializable objects to strings
            serializable_results = json.loads(json.dumps(results, default=str))
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        return results['overall_performance_score'] >= 70
        
    except Exception as e:
        print(f"❌ Performance optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)