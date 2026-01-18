# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🆕 **Process Search Tool** (`search_processes`): Search for processes by keyword (name or command line)
  - Case-sensitive and case-insensitive search support
  - Returns matching process IDs, names, and resource usage
  - Useful for finding target processes before profiling

- 🆕 **Process Profiling Tool** (`profile_process`): Profile specific processes using perf
  - Collect performance data using Linux `perf` tool
  - Configurable sampling duration, frequency, and events
  - Generate flame graph-ready data
  - Extract top CPU-consuming functions
  - Support for various perf events: cpu-clock, cycles, instructions, cache-misses

- 📝 New documentation file `FEATURES.md` with detailed usage examples
- 📝 Change log file `CHANGELOG.md`

### Changed
- Enhanced `ProcessCollector` with search functionality
- Updated README files (both Chinese and English) with new feature descriptions

### Technical Details
- New collector: `PerfCollector` in `collectors/perf.py`
- Enhanced `ProcessCollector.search_processes()` method
- Added input validation for process profiling parameters
- Automatic cleanup of temporary perf data files

## [1.0.0] - 2026-01-17

### Added
- Initial release with basic performance monitoring features
- CPU metrics collection
- Memory metrics collection
- Disk I/O metrics collection
- Network metrics collection
- Process metrics collection
- Performance summary generation
- MCP protocol support (STDIO and HTTP modes)
- Support for Streamable HTTP and SSE transports
- Health check endpoints
- Apache 2.0 license
- Comprehensive documentation in English and Chinese

### Features
- Real-time system performance monitoring
- Top N CPU/memory consumers tracking
- Automated health checks and alerts
- Cross-platform support (Linux primary, macOS for development)
- Remote monitoring via HTTP
- CORS support for web clients

---

## Upgrade Notes

### From 1.0.0 to Current

**New Dependencies**: None (uses existing psutil and subprocess)

**Breaking Changes**: None - All existing APIs remain compatible

**New Requirements**:
- For `profile_process` tool: `perf` must be installed on target systems
  ```bash
  # Ubuntu/Debian
  sudo apt-get install linux-tools-generic linux-tools-$(uname -r)
  
  # RHEL/CentOS
  sudo yum install perf
  ```

**Configuration Changes**: None required

**Permissions**:
- Process profiling may require elevated permissions or kernel parameter adjustments:
  ```bash
  # Enable perf for non-root users (optional)
  sudo sysctl -w kernel.perf_event_paranoid=-1
  ```

---

## Future Roadmap

### Planned Features
- [ ] Real-time streaming profiling
- [ ] Automatic flame graph generation and rendering
- [ ] Historical data storage and trending
- [ ] Alerting and notification system
- [ ] Process trace and system call analysis
- [ ] GPU performance monitoring
- [ ] Container-aware monitoring
- [ ] Kubernetes integration
- [ ] Prometheus metrics export
- [ ] Web dashboard UI

### Under Consideration
- [ ] Support for Windows performance monitoring
- [ ] Machine learning-based anomaly detection
- [ ] Distributed tracing integration
- [ ] Custom metric plugins
- [ ] Time-series database integration

---

## Contributing

We welcome contributions! To contribute to this project:

1. **Report Issues**: Open an issue on GitHub to report bugs or suggest features
2. **Submit Pull Requests**: Fork the repository, make your changes, and submit a PR
3. **Follow Code Style**: Ensure your code follows the existing style and passes linting
4. **Add Tests**: Include tests for new features when applicable
5. **Update Documentation**: Update README and CHANGELOG for significant changes

For more details, please review the [README.md](README.md) and check the [LICENSE](LICENSE).

For bugs and feature requests, please open an issue on GitHub.

---

[Unreleased]: https://github.com/yuezhongtao/linux-profiler-tool/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yuezhongtao/linux-profiler-tool/releases/tag/v1.1.0
[1.0.0]: https://github.com/yuezhongtao/linux-profiler-tool/releases/tag/v1.0.0
