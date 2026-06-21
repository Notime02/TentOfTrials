# Operations Documentation

# Log Watchdog

## Fixture Command

To test the log watchdog, you can use the following command:

```bash
perl v2/scripts/log_watchdog.pl < log_input.json
```

## JSON Behavior

The log watchdog processes JSON records from standard input. It counts malformed records and reports them without crashing. The exit code will be 1 if there are any malformed records, otherwise, it will exit with 0.
