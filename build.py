# ... (truncated) ...

# New regression tests for frailbox logger newline boundary handling

def test_logger_newline_boundaries():
    logger = FrailboxLogger()

    # Test case: No newline
    logger.log('Test message without newline')
    assert logger.get_last_log() == 'Test message without newline'

    # Test case: One newline
    logger.log('Test message with newline\n')
    assert logger.get_last_log() == 'Test message with newline'

    # Test case: Multiple trailing newlines
    logger.log('Test message with multiple newlines\n\n\n')
    assert logger.get_last_log() == 'Test message with multiple newlines'

    # Test case: Partial write crossing buffer limit
    logger.write_partial('Partial log message that crosses the buffer limit')
    assert logger.get_last_log() == 'Partial log message that crosses the buffer limit'

# ... (truncated) ...

if __name__ == '__main__':
    # Run tests
    test_logger_newline_boundaries()

    # Existing build process
    results = run_build_process()
    print_summary(results)

# ... (truncated) ...