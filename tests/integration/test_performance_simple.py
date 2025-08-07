#!/usr/bin/env python3
"""
Simplified Performance Test Suite
Test performance senza dipendenze esterne per 41 agenti simultanei
"""

import asyncio
import time
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
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

class SimplePerformanceTester:
    """Simplified performance testing suite"""
    
    def __init__(self):
        self.agents_directory = str(backend_path / "src" / "agents" / "definitions")
        self.loader = DynamicAgentLoader(self.agents_directory)
        self.agents = {}
        self.performance_metrics = {}
        
    async def initialize(self):
        """Initialize performance testing environment"""
        print("🚀 Initializing Simple Performance Test Suite")
        
        # Load all agents and measure time
        start_time = time.perf_counter()
        self.agents = self.loader.scan_and_load_agents()
        load_time = time.perf_counter() - start_time
        
        print(f"✅ Loaded {len(self.agents)} agents in {load_time:.3f}s")
        self.performance_metrics["agent_load_time"] = load_time
        
    async def test_agent_data_size(self) -> Dict[str, Any]:
        """Test agent data sizes and memory estimation"""
        print("\n📊 Testing Agent Data Sizes")
        
        total_size = 0
        agent_sizes = []
        
        for agent_key, agent in self.agents.items():
            # Calculate estimated size for each agent
            agent_size = (
                len(agent.name.encode('utf-8')) +
                len(agent.description.encode('utf-8')) +
                len(agent.persona.encode('utf-8')) +
                sum(len(kw.encode('utf-8')) for kw in agent.expertise_keywords) +
                len(agent.tier.encode('utf-8')) +
                len(agent.color.encode('utf-8')) +
                sum(len(tool.encode('utf-8')) for tool in agent.tools) +
                200  # Overhead for object structure
            )
            
            total_size += agent_size
            agent_sizes.append({
                "name": agent.name,
                "size_bytes": agent_size,
                "expertise_count": len(agent.expertise_keywords),
                "tools_count": len(agent.tools)
            })
        
        # Find largest and smallest agents
        largest_agent = max(agent_sizes, key=lambda x: x["size_bytes"])
        smallest_agent = min(agent_sizes, key=lambda x: x["size_bytes"])
        average_size = total_size / len(self.agents) if len(self.agents) > 0 else 0
        
        metrics = {
            "total_size_kb": total_size / 1024,
            "average_size_bytes": average_size,
            "largest_agent": largest_agent,
            "smallest_agent": smallest_agent,
            "agent_count": len(self.agents)
        }
        
        print(f"   Total Data Size: {metrics['total_size_kb']:.1f} KB")
        print(f"   Average per Agent: {average_size:.0f} bytes")
        print(f"   Largest Agent: {largest_agent['name']} ({largest_agent['size_bytes']} bytes)")
        print(f"   Smallest Agent: {smallest_agent['name']} ({smallest_agent['size_bytes']} bytes)")
        
        # Memory efficiency assessment
        if metrics['total_size_kb'] < 500:
            print("   ✅ Memory footprint: EXCELLENT")
        elif metrics['total_size_kb'] < 1000:
            print("   ✅ Memory footprint: GOOD")
        else:
            print("   ⚠️ Memory footprint: CONSIDER OPTIMIZATION")
        
        return metrics
    
    async def test_lookup_speed(self) -> Dict[str, Any]:
        """Test agent lookup and access speed"""
        print("\n⚡ Testing Agent Lookup Speed")
        
        iterations = 10000
        agent_keys = list(self.agents.keys())
        
        # Test dictionary lookups
        start_time = time.perf_counter()
        for i in range(iterations):
            key = agent_keys[i % len(agent_keys)]
            agent = self.agents.get(key)
            if agent:
                _ = agent.name  # Access property
        lookup_time = time.perf_counter() - start_time
        
        # Test search by expertise
        search_terms = ["security", "financial", "design", "strategy", "technical"]
        start_time = time.perf_counter()
        search_results = []
        
        for term in search_terms * 100:  # 500 searches
            matches = []
            for agent_key, agent in self.agents.items():
                if any(term.lower() in keyword.lower() for keyword in agent.expertise_keywords):
                    matches.append(agent_key)
            search_results.append(len(matches))
        
        search_time = time.perf_counter() - start_time
        
        metrics = {
            "lookup_iterations": iterations,
            "lookup_total_time": lookup_time,
            "lookup_time_per_operation_ms": (lookup_time / iterations) * 1000,
            "lookups_per_second": iterations / lookup_time if lookup_time > 0 else 0,
            "search_operations": 500,
            "search_total_time": search_time,
            "search_time_per_operation_ms": (search_time / 500) * 1000,
            "searches_per_second": 500 / search_time if search_time > 0 else 0
        }
        
        print(f"   {iterations} Dictionary Lookups: {lookup_time:.3f}s ({metrics['lookups_per_second']:.0f}/sec)")
        print(f"   500 Expertise Searches: {search_time:.3f}s ({metrics['searches_per_second']:.0f}/sec)")
        print(f"   Average Lookup Time: {metrics['lookup_time_per_operation_ms']:.4f}ms")
        print(f"   Average Search Time: {metrics['search_time_per_operation_ms']:.2f}ms")
        
        # Speed assessment
        if metrics['lookup_time_per_operation_ms'] < 0.01:
            print("   ✅ Lookup speed: EXCELLENT")
        elif metrics['lookup_time_per_operation_ms'] < 0.1:
            print("   ✅ Lookup speed: GOOD")
        else:
            print("   ⚠️ Lookup speed: NEEDS OPTIMIZATION")
        
        return metrics
    
    async def test_knowledge_base_generation(self) -> Dict[str, Any]:
        """Test knowledge base generation performance"""
        print("\n🧠 Testing Knowledge Base Generation")
        
        # Test multiple knowledge base generations
        generation_times = []
        kb_sizes = []
        
        for i in range(5):
            start_time = time.perf_counter()
            knowledge_base = self.loader.generate_ali_knowledge_base()
            generation_time = time.perf_counter() - start_time
            
            generation_times.append(generation_time)
            kb_sizes.append(len(knowledge_base))
        
        avg_generation_time = sum(generation_times) / len(generation_times)
        avg_kb_size = sum(kb_sizes) / len(kb_sizes)
        min_time = min(generation_times)
        max_time = max(generation_times)
        
        metrics = {
            "generation_iterations": 5,
            "average_generation_time": avg_generation_time,
            "min_generation_time": min_time,
            "max_generation_time": max_time,
            "average_kb_size_chars": avg_kb_size,
            "kb_generation_rate_chars_per_sec": avg_kb_size / avg_generation_time if avg_generation_time > 0 else 0
        }
        
        print(f"   5 Knowledge Base Generations:")
        print(f"     Average Time: {avg_generation_time:.3f}s")
        print(f"     Min Time: {min_time:.3f}s")
        print(f"     Max Time: {max_time:.3f}s")
        print(f"     Average Size: {avg_kb_size:.0f} characters")
        print(f"     Generation Rate: {metrics['kb_generation_rate_chars_per_sec']:.0f} chars/sec")
        
        # Generation speed assessment
        if avg_generation_time < 0.1:
            print("   ✅ Knowledge generation: EXCELLENT")
        elif avg_generation_time < 0.5:
            print("   ✅ Knowledge generation: GOOD")
        else:
            print("   ⚠️ Knowledge generation: CONSIDER CACHING")
        
        return metrics
    
    async def test_concurrent_operations(self) -> Dict[str, Any]:
        """Test concurrent agent operations"""
        print("\n🔄 Testing Concurrent Operations")
        
        async def agent_operation_batch(batch_id: int, operations: int):
            """Perform a batch of agent operations"""
            agent_keys = list(self.agents.keys())
            results = []
            
            start_time = time.perf_counter()
            for i in range(operations):
                key = agent_keys[(batch_id + i) % len(agent_keys)]
                agent = self.agents.get(key)
                
                if agent:
                    # Simulate agent data access
                    data = {
                        "name": agent.name,
                        "description_length": len(agent.description),
                        "expertise_count": len(agent.expertise_keywords),
                        "tools_count": len(agent.tools)
                    }
                    results.append(data)
                
                # Small delay to simulate processing
                await asyncio.sleep(0.001)
            
            end_time = time.perf_counter()
            return {
                "batch_id": batch_id,
                "operations": len(results),
                "time": end_time - start_time
            }
        
        # Run concurrent batches
        concurrent_batches = 20
        operations_per_batch = 25
        
        start_time = time.perf_counter()
        tasks = [agent_operation_batch(i, operations_per_batch) for i in range(concurrent_batches)]
        batch_results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        total_operations = sum(r["operations"] for r in batch_results)
        average_batch_time = sum(r["time"] for r in batch_results) / len(batch_results)
        operations_per_second = total_operations / total_time if total_time > 0 else 0
        
        metrics = {
            "concurrent_batches": concurrent_batches,
            "operations_per_batch": operations_per_batch,
            "total_operations": total_operations,
            "total_time": total_time,
            "average_batch_time": average_batch_time,
            "operations_per_second": operations_per_second,
            "concurrency_efficiency": (concurrent_batches * average_batch_time) / total_time if total_time > 0 else 0
        }
        
        print(f"   {concurrent_batches} concurrent batches × {operations_per_batch} operations")
        print(f"   Total Operations: {total_operations}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Operations/Second: {operations_per_second:.0f}")
        print(f"   Concurrency Efficiency: {metrics['concurrency_efficiency']:.2f}x")
        
        # Concurrency assessment
        if operations_per_second > 5000:
            print("   ✅ Concurrent performance: EXCELLENT")
        elif operations_per_second > 2000:
            print("   ✅ Concurrent performance: GOOD")
        else:
            print("   ⚠️ Concurrent performance: CONSIDER OPTIMIZATION")
        
        return metrics
    
    async def test_scaling_behavior(self) -> Dict[str, Any]:
        """Test how performance scales with different numbers of agents"""
        print("\n📈 Testing Scaling Behavior")
        
        scaling_tests = [
            {"agent_count": 10, "name": "Small team"},
            {"agent_count": 20, "name": "Medium team"},
            {"agent_count": 30, "name": "Large team"},
            {"agent_count": 41, "name": "Full ecosystem"}
        ]
        
        scaling_results = []
        
        for test in scaling_tests:
            agent_count = min(test["agent_count"], len(self.agents))
            selected_agents = dict(list(self.agents.items())[:agent_count])
            
            # Test search performance with this subset
            search_terms = ["security", "financial", "design", "strategy"]
            start_time = time.perf_counter()
            
            search_results = []
            for term in search_terms * 50:  # 200 searches
                matches = []
                for agent_key, agent in selected_agents.items():
                    if any(term.lower() in keyword.lower() for keyword in agent.expertise_keywords):
                        matches.append(agent_key)
                search_results.append(len(matches))
            
            search_time = time.perf_counter() - start_time
            
            scaling_results.append({
                "name": test["name"],
                "agent_count": agent_count,
                "search_time": search_time,
                "searches_per_second": 200 / search_time if search_time > 0 else 0,
                "time_per_agent": search_time / agent_count if agent_count > 0 else 0
            })
            
            print(f"   {test['name']} ({agent_count} agents): {search_time:.3f}s ({200/search_time:.0f} searches/sec)")
        
        # Calculate scaling efficiency
        if len(scaling_results) > 1:
            base_time = scaling_results[0]["search_time"]
            full_time = scaling_results[-1]["search_time"]
            base_agents = scaling_results[0]["agent_count"]
            full_agents = scaling_results[-1]["agent_count"]
            
            linear_expected_time = base_time * (full_agents / base_agents)
            scaling_efficiency = linear_expected_time / full_time if full_time > 0 else 1
        else:
            scaling_efficiency = 1.0
        
        metrics = {
            "scaling_tests": scaling_results,
            "scaling_efficiency": scaling_efficiency,
            "performance_degradation": (1 - scaling_efficiency) * 100 if scaling_efficiency < 1 else 0
        }
        
        print(f"   Scaling Efficiency: {scaling_efficiency:.2f}x")
        print(f"   Performance Degradation: {metrics['performance_degradation']:.1f}%")
        
        # Scaling assessment
        if scaling_efficiency > 0.8:
            print("   ✅ Scaling behavior: EXCELLENT")
        elif scaling_efficiency > 0.6:
            print("   ✅ Scaling behavior: GOOD")
        else:
            print("   ⚠️ Scaling behavior: OPTIMIZATION RECOMMENDED")
        
        return metrics
    
    def calculate_overall_score(self, all_metrics: Dict[str, Any]) -> int:
        """Calculate overall performance score"""
        
        scores = []
        
        # Data size score (lower is better)
        data_size = all_metrics.get("data_size", {}).get("total_size_kb", 1000)
        if data_size < 500:
            scores.append(100)
        elif data_size < 1000:
            scores.append(80)
        else:
            scores.append(60)
        
        # Lookup speed score
        lookup_time = all_metrics.get("lookup_speed", {}).get("lookup_time_per_operation_ms", 1)
        if lookup_time < 0.01:
            scores.append(100)
        elif lookup_time < 0.1:
            scores.append(80)
        else:
            scores.append(60)
        
        # Knowledge generation score
        kb_time = all_metrics.get("knowledge_generation", {}).get("average_generation_time", 1)
        if kb_time < 0.1:
            scores.append(100)
        elif kb_time < 0.5:
            scores.append(80)
        else:
            scores.append(60)
        
        # Concurrent operations score
        concurrent_ops = all_metrics.get("concurrent_operations", {}).get("operations_per_second", 0)
        if concurrent_ops > 5000:
            scores.append(100)
        elif concurrent_ops > 2000:
            scores.append(80)
        else:
            scores.append(60)
        
        # Scaling score
        scaling_eff = all_metrics.get("scaling_behavior", {}).get("scaling_efficiency", 1)
        if scaling_eff > 0.8:
            scores.append(100)
        elif scaling_eff > 0.6:
            scores.append(80)
        else:
            scores.append(60)
        
        return int(sum(scores) / len(scores)) if scores else 0
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete performance test suite"""
        
        print("🎯 RUNNING COMPLETE PERFORMANCE TEST SUITE")
        print("=" * 60)
        
        all_metrics = {}
        
        try:
            # Run all tests
            all_metrics["data_size"] = await self.test_agent_data_size()
            all_metrics["lookup_speed"] = await self.test_lookup_speed()
            all_metrics["knowledge_generation"] = await self.test_knowledge_base_generation()
            all_metrics["concurrent_operations"] = await self.test_concurrent_operations()
            all_metrics["scaling_behavior"] = await self.test_scaling_behavior()
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(all_metrics)
            all_metrics["overall_performance_score"] = overall_score
            
            return all_metrics
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

async def main():
    """Main function"""
    
    try:
        # Initialize and run tests
        tester = SimplePerformanceTester()
        await tester.initialize()
        
        results = await tester.run_complete_test_suite()
        
        if "error" in results:
            return False
        
        # Print final summary
        print("\n🏆 PERFORMANCE TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Overall Performance Score: {results['overall_performance_score']}/100")
        
        if results['overall_performance_score'] >= 85:
            print("✅ PERFORMANCE: EXCELLENT - Optimized for 41+ agents!")
        elif results['overall_performance_score'] >= 75:
            print("✅ PERFORMANCE: GOOD - Ready for production")
        elif results['overall_performance_score'] >= 65:
            print("⚠️ PERFORMANCE: ACCEPTABLE - Minor optimizations recommended")
        else:
            print("⚠️ PERFORMANCE: NEEDS IMPROVEMENT - Apply optimizations")
        
        print(f"\nKey Metrics:")
        print(f"  Agent Data Size: {results['data_size']['total_size_kb']:.1f} KB")
        print(f"  Lookup Speed: {results['lookup_speed']['lookups_per_second']:.0f} lookups/sec")
        print(f"  Concurrent Operations: {results['concurrent_operations']['operations_per_second']:.0f} ops/sec")
        print(f"  Scaling Efficiency: {results['scaling_behavior']['scaling_efficiency']:.2f}x")
        
        # Save results to project root logs directory
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        results_file = logs_dir / "performance_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Detailed results saved to {results_file}")
        
        return results['overall_performance_score'] >= 70
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)