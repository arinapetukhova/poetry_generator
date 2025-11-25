import time
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from core.config import RAPTORConfig
from rag_pipeline import SongRAPTOR

@dataclass
class BenchmarkResult:
    test_name: str
    query: str
    search_time: float
    results_count: int
    avg_similarity: float
    max_similarity: float
    min_similarity: float
    retrieved_hierarchy_levels: List[str]
    success: bool
    error_message: str = ""

@dataclass
class BenchmarkSummary:
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_search_time: float
    avg_similarity_score: float
    query_coverage: Dict[str, int]
    performance_metrics: Dict[str, float]

@dataclass
class DetailedTestInfo:
    query: str
    status: str
    search_time: float
    results_count: int
    min_similarity: float
    max_similarity: float
    avg_similarity: float
    level_distribution: Dict[str, int]
    expected_level: str

class RAPTORBenchmark:
    def __init__(self, raptor_system: SongRAPTOR, test_queries: List[Dict[str, Any]] = None):
        self.raptor = raptor_system
        self.config = raptor_system.config
        self.test_queries = test_queries or self._get_default_test_queries()
        
    def _get_default_test_queries(self) -> List[Dict[str, Any]]:
        return [
            {"query": "song in genre rock", "expected_level": "genre", "type": "rock"},
            {"query": "song in genre pop", "expected_level": "genre", "type": "pop"},
            {"query": "song in genre soul", "expected_level": "genre", "type": "soul"},
            {"query": "song in genre alternative", "expected_level": "genre", "type": "alternative"},
            {"query": "song in genre rap", "expected_level": "genre", "type": "rap"},
            
            {"query": "song in style of band The Beatles", "expected_level": "artist", "type": "the beatles"},
            {"query": "song in style of musician Michael Jackson", "expected_level": "artist", "type": "michael jackson"},
            {"query": "song in style of musician Bob Dylan", "expected_level": "artist", "type": "bob dylan"},
            {"query": "song in style of musician Taylor Swift", "expected_level": "artist", "type": "taylor swift"},
            {"query": "song in style of band Radiohead", "expected_level": "artist", "type": "radiohead"},
            
            {"query": "love songs with romantic lyrics", "expected_level": "song"},
            {"query": "sad breakup heartbreak lyrics", "expected_level": "song"},
            {"query": "summer fun beach party lyrics", "expected_level": "song"},
            {"query": "inspirational motivational lyrics", "expected_level": "song"},
            {"query": "storytelling narrative ballad", "expected_level": "song"},
        ]
    
    def _extract_hierarchy_level(self, result) -> str:
        """Extract hierarchy level from search result"""
        if hasattr(result, 'metadata') and result.metadata and 'hierarchy_level' in result.metadata:
            return result.metadata['hierarchy_level']
        
        if hasattr(result, 'hierarchy_path') and result.hierarchy_path:
            path_length = len(result.hierarchy_path)
            if path_length == 1:
                return "genre"
            elif path_length == 2:
                return "artist"
            elif path_length >= 3:
                return "song"
        
        return "unknown"
    
    def _check_level_match(self, expected_level: str, actual_levels: List[str], matches_type: bool) -> bool:
        """Check if the retrieved levels match the expected level"""
        if not actual_levels:
            return False
            
        if expected_level == "genre":
            if expected_level in actual_levels and matches_type:
                return True
            return False
            
        elif expected_level == "artist":
            if expected_level in actual_levels and matches_type:
                return True
            return False
            
        elif expected_level == "song":
            song_count = sum(1 for level in actual_levels if level == "song")
            return song_count / len(actual_levels) >= 1/len(actual_levels)
            
        return False
    
    def _check_similarity_quality(self, similarities: List[float]) -> bool:
        """Check if similarity scores are of good quality"""
        if not similarities:
            return False
            
        avg_similarity = statistics.mean(similarities)
        max_similarity = max(similarities)
        
        return avg_similarity > 0.3 and max_similarity > 0.4
    
    def run_single_test(self, test_query: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark test focusing on level and similarity"""
        start_time = time.time()
        
        try:
            results = self.raptor.search(
                query=test_query["query"],
                top_k=self.config.top_k
            )
            
            search_time = time.time() - start_time

            similarities = [result.similarity for result in results]
            avg_similarity = statistics.mean(similarities) if similarities else 0
            max_similarity = max(similarities) if similarities else 0
            min_similarity = min(similarities) if similarities else 0
            
            hierarchy_levels = []
            for result in results:
                level = self._extract_hierarchy_level(result)
                hierarchy_levels.append(level)
            
            matches_type = False
            if test_query["expected_level"] == 'genre':
                for result in results:
                    actual_type = result.text.split(' ')[1]
                    if actual_type.split("\n")[0].lower().strip() == test_query['type']:
                        matches_type = True
                        break
            elif test_query["expected_level"] == 'artist':
                for result in results:
                    actual_type = result.text.split('\n')[0][15:]
                    actual_type2 = result.text.split('\n')[1]

                    if actual_type.split("\n")[0].lower().strip() == test_query['type'] or actual_type2[8:].lower().strip() == test_query['type']:
                        matches_type = True
                        break
            level_match = self._check_level_match(test_query["expected_level"], hierarchy_levels, matches_type)
            similarity_quality = self._check_similarity_quality(similarities)
            success = level_match and similarity_quality and len(results) > 0
            
            return BenchmarkResult(
                test_name=test_query,
                query=test_query["query"],
                search_time=search_time,
                results_count=len(results),
                avg_similarity=avg_similarity,
                max_similarity=max_similarity,
                min_similarity=min_similarity,
                retrieved_hierarchy_levels=hierarchy_levels,
                success=success
            )
            
        except Exception as e:
            return BenchmarkResult(
                test_name=test_query,
                query=test_query["query"],
                search_time=0,
                results_count=0,
                avg_similarity=0,
                max_similarity=0,
                min_similarity=0,
                retrieved_hierarchy_levels=[],
                success=False,
                error_message=str(e)
            )
    
    def run_level_accuracy_test(self) -> Dict[str, Any]:
        """Test accuracy of hierarchy level retrieval"""
        level_results = {"genre": [], "artist": [], "song": []}
        
        level_passes = {"genre": 0, "artist": 0, "song": 0}
        level_queries = {"genre": 0, "artist": 0, "song": 0}
        level_similarities = {"genre": [], "artist": [], "song": []}
        
        for test_query in self.test_queries:
            expected_level = test_query["expected_level"]
            level_queries[expected_level] += 1
            
            result = self.run_single_test(test_query)
            
            if result.success:
                level_passes[expected_level] += 1
                level_similarities[expected_level].append(result.avg_similarity)
            
            level_counts = {}
            for level in result.retrieved_hierarchy_levels:
                level_counts[level] = level_counts.get(level, 0) + 1
            
            total_results = len(result.retrieved_hierarchy_levels)
            expected_level_count = level_counts.get(expected_level, 0)
            accuracy = expected_level_count / total_results if total_results > 0 else 0
            
            level_results[expected_level].append({
                "query": test_query["query"],
                "accuracy": accuracy,
                "level_distribution": level_counts,
                "avg_similarity": result.avg_similarity
            })
        
        accuracy_summary = {}
        for level, results in level_results.items():
            if results:
                accuracies = [r["accuracy"] for r in results]
                similarities = [r["avg_similarity"] for r in results]
                
                pass_rate = level_passes[level] / level_queries[level] if level_queries[level] > 0 else 0
                
                accuracy_summary[level] = {
                    "avg_accuracy": statistics.mean(accuracies),
                    "avg_similarity": statistics.mean(similarities),
                    "total_queries": len(results),
                    "pass_rate": pass_rate,
                    "passes": level_passes[level],
                    "total_queries_for_level": level_queries[level]
                }
        
        return accuracy_summary
    
    def run_comprehensive_benchmark(self) -> Tuple[BenchmarkSummary, List[DetailedTestInfo]]:
        """Run comprehensive benchmark suite focusing on level and similarity"""
        print("Starting RAPTOR RAG Benchmark Tests (Level & Similarity Focus)...")
        
        test_results = []
        detailed_test_info = []
        
        for test_query in self.test_queries:
            print(f"Running test: {test_query['query']}")
            result = self.run_single_test(test_query)
            test_results.append(result)
            
            status = "PASS" if result.success else "FAIL"
            level_distribution = {}
            for level in result.retrieved_hierarchy_levels:
                level_distribution[level] = level_distribution.get(level, 0) + 1
            
            test_info = DetailedTestInfo(
                query=test_query["query"],
                status=status,
                search_time=result.search_time,
                results_count=result.results_count,
                min_similarity=result.min_similarity,
                max_similarity=result.max_similarity,
                avg_similarity=result.avg_similarity,
                level_distribution=level_distribution,
                expected_level=test_query["expected_level"]
            )
            detailed_test_info.append(test_info)
            
            print(f"  {status} - Time: {result.search_time:.3f}s, Results: {result.results_count}")
            print(f"  Similarity: {result.min_similarity:.3f}-{result.max_similarity:.3f} (avg: {result.avg_similarity:.3f})")
            print(f"  Level Distribution: {level_distribution}")
            print(f"  Expected Level: {test_query['expected_level']}")
        
        print("\nRunning level accuracy analysis...")
        accuracy_summary = self.run_level_accuracy_test()
        
        print("\nLEVEL ACCURACY RESULTS:")
        print("-" * 50)
        total_passes = 0
        total_queries = 0
        all_similarities = []
        
        for level, stats in accuracy_summary.items():
            passes = stats["passes"]
            total_queries_level = stats["total_queries_for_level"]
            pass_rate = stats["pass_rate"]
            avg_similarity = stats["avg_similarity"]
            
            total_passes += passes
            total_queries += total_queries_level
            
            level_similarities = [r.avg_similarity for r in test_results 
                                if r.query in [q["query"] for q in self.test_queries 
                                             if q["expected_level"] == level]]
            all_similarities.extend(level_similarities)
            
            print(f"  {level.upper()}:")
            print(f"    Pass Rate: {passes}/{total_queries_level} ({pass_rate:.1%})")
            print(f"    Avg Accuracy: {stats['avg_accuracy']:.1%}")
            print(f"    Avg Similarity: {avg_similarity:.3f}")
        
        overall_pass_rate = total_passes / total_queries if total_queries > 0 else 0
        overall_avg_similarity = statistics.mean(all_similarities) if all_similarities else 0
        
        print(f"\nOVERALL:")
        print(f"  Total Pass Rate: {total_passes}/{total_queries} ({overall_pass_rate:.1%})")
        print(f"  Overall Avg Similarity: {overall_avg_similarity:.3f}")
        
        successful_tests = [r for r in test_results if r.success]
        failed_tests = [r for r in test_results if not r.success]
        
        query_coverage = {"genre": 0, "artist": 0, "song": 0}
        for test_query in self.test_queries:
            query_coverage[test_query["expected_level"]] += 1
        
        search_times = [r.search_time for r in successful_tests]
        similarity_scores = [r.avg_similarity for r in successful_tests]
        
        performance_metrics = {
            "min_search_time": min(search_times) if search_times else 0,
            "max_search_time": max(search_times) if search_times else 0,
            "median_search_time": statistics.median(search_times) if search_times else 0,
            "level_accuracy_genre": accuracy_summary.get("genre", {}).get("avg_accuracy", 0),
            "level_accuracy_artist": accuracy_summary.get("artist", {}).get("avg_accuracy", 0),
            "level_accuracy_song": accuracy_summary.get("song", {}).get("avg_accuracy", 0),
            "pass_rate_genre": accuracy_summary.get("genre", {}).get("pass_rate", 0),
            "pass_rate_artist": accuracy_summary.get("artist", {}).get("pass_rate", 0),
            "pass_rate_song": accuracy_summary.get("song", {}).get("pass_rate", 0),
            "overall_pass_rate": overall_pass_rate,
            "overall_avg_similarity": overall_avg_similarity
        }
        
        summary = BenchmarkSummary(
            total_tests=len(test_results),
            passed_tests=len(successful_tests),
            failed_tests=len(failed_tests),
            avg_search_time=statistics.mean(search_times) if search_times else 0,
            avg_similarity_score=statistics.mean(similarity_scores) if similarity_scores else 0,
            query_coverage=query_coverage,
            performance_metrics=performance_metrics
        )
        
        return summary, detailed_test_info
    
    def generate_report(self, summary: BenchmarkSummary, detailed_results: List[BenchmarkResult], detailed_test_info: List[DetailedTestInfo]) -> str:
        """Generate a comprehensive benchmark report focused on level and similarity"""
        report = []
        report.append("=" * 60)
        report.append("RAPTOR RAG SYSTEM BENCHMARK REPORT")
        report.append("Level & Similarity Analysis")
        report.append("=" * 60)

        report.append("\nSUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests: {summary.total_tests}")
        report.append(f"Passed: {summary.passed_tests}")
        report.append(f"Failed: {summary.failed_tests}")
        report.append(f"Success Rate: {(summary.passed_tests/summary.total_tests)*100:.1f}%")
        report.append(f"Average Search Time: {summary.avg_search_time:.3f}s")
        report.append(f"Average Similarity Score: {summary.avg_similarity_score:.3f}")
        
        report.append("\nPERFORMANCE METRICS")
        report.append("-" * 40)
        for metric, value in summary.performance_metrics.items():
            if "time" in metric:
                report.append(f"{metric}: {value:.3f}s")
            elif "accuracy" in metric or "rate" in metric:
                report.append(f"{metric}: {value:.1%}")
            else:
                report.append(f"{metric}: {value:.3f}")
        
        report.append("\nQUERY COVERAGE")
        report.append("-" * 40)
        for level, count in summary.query_coverage.items():
            report.append(f"{level.upper()} queries: {count}")

        report.append("\nDETAILED TEST RESULTS")
        report.append("-" * 50)
        for test_info in detailed_test_info:
            report.append(f"Running test: {test_info.query}")
            report.append(f"  {test_info.status} - Time: {test_info.search_time:.3f}s, Results: {test_info.results_count}")
            report.append(f"  Similarity: {test_info.min_similarity:.3f}-{test_info.max_similarity:.3f} (avg: {test_info.avg_similarity:.3f})")
            report.append(f"  Level Distribution: {test_info.level_distribution}")
            report.append(f"  Expected Level: {test_info.expected_level}")
            report.append("")
        
        report.append("\nCOMPREHENSIVE BENCHMARK RESULTS")
        report.append("-" * 40)
        
        level_stats = {"genre": {"similarities": [], "count": 0}, 
                      "artist": {"similarities": [], "count": 0}, 
                      "song": {"similarities": [], "count": 0}}
        
        for result in detailed_results:
            expected_level = None
            for test_query in self.test_queries:
                if test_query["query"] == result.query:
                    expected_level = test_query["expected_level"]
                    break
            
            if expected_level and expected_level in level_stats:
                level_stats[expected_level]["similarities"].append(result.avg_similarity)
                level_stats[expected_level]["count"] += 1
        
        report.append("\nLEVEL-WISE SIMILARITY ANALYSIS:")
        for level, stats in level_stats.items():
            if stats["similarities"]:
                mean_similarity = statistics.mean(stats["similarities"])
                report.append(f"  {level.upper()}: {mean_similarity:.3f} (from {stats['count']} queries)")
            else:
                report.append(f"  {level.upper()}: No data")
        
        all_similarities = []
        for result in detailed_results:
            if result.avg_similarity > 0:
                all_similarities.append(result.avg_similarity)
        
        if all_similarities:
            overall_mean_similarity = statistics.mean(all_similarities)
            report.append(f"  OVERALL: {overall_mean_similarity:.3f} (from {len(all_similarities)} queries)")
        
        return "\n".join(report)

def run_benchmark():
    """Main function to run the benchmark"""
    try:
        config = RAPTORConfig()
        raptor_system = SongRAPTOR(config)
        
        benchmark = RAPTORBenchmark(raptor_system)
        summary, detailed_test_info = benchmark.run_comprehensive_benchmark()
        
        detailed_results = []
        for test_query in benchmark.test_queries:
            result = benchmark.run_single_test(test_query)
            detailed_results.append(result)
        
        report = benchmark.generate_report(summary, detailed_results, detailed_test_info)
        print(report)
        
        with open('../backend/benchmark_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nBenchmark report saved to 'backend/benchmark_report.txt'")
        
        return summary.passed_tests == summary.total_tests
        
    except Exception as e:
        print(f"Benchmark failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_benchmark()