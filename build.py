import json

# ... (truncated) ...

def run_self_test(json_output=False):
    results = []
    # ... (self-test logic) ...
    for test in tests:
        start_time = time.time()
        try:
            # Execute the test
            result = execute_test(test)
            status = 'success'
            failure_reason = None
        except Exception as e:
            status = 'failure'
            failure_reason = str(e)
        duration = time.time() - start_time
        results.append({
            'test_name': test.name,
            'status': status,
            'duration': duration,
            'failure_reason': failure_reason
        })

    if json_output:
        print(json.dumps(results, indent=4))
    else:
        # Existing text output logic
        for result in results:
            print(f"Test: {result['test_name']}, Status: {result['status']}, Duration: {result['duration']:.2f}s")
            if result['failure_reason']:
                print(f"Failure Reason: {result['failure_reason']}")

# ... (truncated) ...

def main():
    parser = argparse.ArgumentParser(description='Frailbox self-test')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    args = parser.parse_args()
    run_self_test(json_output=args.json)

if __name__ == '__main__':
    main()