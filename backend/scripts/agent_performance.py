#!/usr/bin/env python3

import time
import statistics
from typing import List, Dict, Any
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.agent import _invoke_agent_with_trace, set_current_user_id, reset_current_user_id
from app.services.conversation_service import create_thread_for_user, get_user_id_for_thread

# Test configuration
NUM_REQUESTS = 10  # Number of requests per query
TEST_QUERIES = [
    "Find me a 2-bedroom apartment in Gainesville under $1500",
    "Show me apartments with pools in Orlando",
    "I need a studio apartment near downtown Tampa",
    "Find pet-friendly apartments in Jacksonville",
    "Looking for apartments with washer/dryer in unit in Miami",
]

# Dummy user ID for testing
TEST_USER_ID = "performance_test_user"

def run_performance_test() -> Dict[str, Any]:
    """
    Run performance tests on the agent and collect statistics.

    Returns:
        Dictionary containing test results and statistics
    """
    print("Starting agent performance test...")
    print(f"Number of requests per query: {NUM_REQUESTS}")
    print(f"Number of test queries: {len(TEST_QUERIES)}")
    print(f"Total requests: {NUM_REQUESTS * len(TEST_QUERIES)}")
    print("-" * 50)

    all_response_times: List[float] = []
    query_results: List[Dict[str, Any]] = []

    for query_idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\nTesting query {query_idx}: {query[:50]}...")
        query_times: List[float] = []

        for req_num in range(1, NUM_REQUESTS + 1):
            # Create a new thread for each request to avoid conversation history effects
            thread = create_thread_for_user(TEST_USER_ID)
            thread_id = thread['thread_id']

            # Measure response time
            start_time = time.time()
            try:
                # Set user context
                tkn = set_current_user_id(TEST_USER_ID)
                config = {"configurable": {"thread_id": thread_id}}
                msgs, final_response, reasoning_steps, tool_calls = _invoke_agent_with_trace(query, config)
                end_time = time.time()
                response_time = end_time - start_time

                # Check if successful (has response)
                if final_response:
                    query_times.append(response_time)
                    all_response_times.append(response_time)
                    print(".3f")
                else:
                    print(f"  Request {req_num}: FAILED - No response generated")

            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                print(f"  Request {req_num}: ERROR - {str(e)} ({response_time:.3f}s)")
            finally:
                reset_current_user_id(tkn)

        # Calculate statistics for this query
        if query_times:
            query_stats = {
                'query': query,
                'num_successful': len(query_times),
                'mean_time': statistics.mean(query_times),
                'median_time': statistics.median(query_times),
                'min_time': min(query_times),
                'max_time': max(query_times),
                'std_dev': statistics.stdev(query_times) if len(query_times) > 1 else 0,
                'times': query_times
            }
            query_results.append(query_stats)
            print(f"  Query stats: Mean={query_stats['mean_time']:.3f}s, "
                  f"Median={query_stats['median_time']:.3f}s, "
                  f"Min={query_stats['min_time']:.3f}s, "
                  f"Max={query_stats['max_time']:.3f}s")

    # Calculate overall statistics
    if all_response_times:
        overall_stats = {
            'total_requests': len(all_response_times),
            'successful_requests': len(all_response_times),
            'mean_time': statistics.mean(all_response_times),
            'median_time': statistics.median(all_response_times),
            'min_time': min(all_response_times),
            'max_time': max(all_response_times),
            'std_dev': statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0,
            'percentiles': {
                '25th': statistics.quantiles(all_response_times, n=4)[0],
                '50th': statistics.quantiles(all_response_times, n=4)[1],
                '75th': statistics.quantiles(all_response_times, n=4)[2],
                '90th': statistics.quantiles(all_response_times, n=4)[3] if len(all_response_times) >= 4 else max(all_response_times),
                '95th': statistics.quantiles(all_response_times, n=4)[3] if len(all_response_times) >= 4 else max(all_response_times),
                '99th': statistics.quantiles(all_response_times, n=4)[3] if len(all_response_times) >= 4 else max(all_response_times),
            }
        }
    else:
        overall_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'error': 'No successful requests'
        }

    results = {
        'test_config': {
            'num_requests_per_query': NUM_REQUESTS,
            'num_queries': len(TEST_QUERIES),
            'total_expected_requests': NUM_REQUESTS * len(TEST_QUERIES)
        },
        'overall_stats': overall_stats,
        'query_results': query_results,
        'all_response_times': all_response_times
    }

    return results

def print_results(results: Dict[str, Any]):
    """Print the test results in a formatted way."""
    print("\n" + "="*60)
    print("AGENT PERFORMANCE TEST RESULTS")
    print("="*60)

    config = results['test_config']
    overall = results['overall_stats']

    print(f"\nTest Configuration:")
    print(f"  Requests per query: {config['num_requests_per_query']}")
    print(f"  Number of queries: {config['num_queries']}")
    print(f"  Total expected requests: {config['total_expected_requests']}")

    print(f"\nOverall Statistics:")
    if 'error' not in overall:
        print(f"  Successful requests: {overall['successful_requests']}/{config['total_expected_requests']}")
        print(f"  Mean response time: {overall['mean_time']:.3f} seconds")
        print(f"  Median response time: {overall['median_time']:.3f} seconds")
        print(f"  Min response time: {overall['min_time']:.3f} seconds")
        print(f"  Max response time: {overall['max_time']:.3f} seconds")
        print(f"  Standard deviation: {overall['std_dev']:.3f} seconds")

        print(f"\nPercentiles:")
        percentiles = overall['percentiles']
        print(f"  25th percentile: {percentiles['25th']:.3f} seconds")
        print(f"  50th percentile: {percentiles['50th']:.3f} seconds")
        print(f"  75th percentile: {percentiles['75th']:.3f} seconds")
        print(f"  90th percentile: {percentiles['90th']:.3f} seconds")
        print(f"  95th percentile: {percentiles['95th']:.3f} seconds")
        print(f"  99th percentile: {percentiles['99th']:.3f} seconds")
    else:
        print(f"  Error: {overall['error']}")

    print(f"\nPer-Query Results:")
    for i, query_result in enumerate(results['query_results'], 1):
        print(f"\n  Query {i}: {query_result['query'][:50]}...")
        print(f"    Successful: {query_result['num_successful']}/{NUM_REQUESTS}")
        if query_result['num_successful'] > 0:
            print(f"    Mean: {query_result['mean_time']:.3f}s, Median: {query_result['median_time']:.3f}s")
            print(f"    Range: {query_result['min_time']:.3f}s - {query_result['max_time']:.3f}s")

def main():
    """Main entry point."""
    try:
        results = run_performance_test()
        print_results(results)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()