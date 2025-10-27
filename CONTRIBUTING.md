# Contributing to ZCS to ZCS Migration

Thank you for your interest in contributing to the ZCS to ZCS Migration project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Issues

If you encounter a bug or have a feature request:

1. Check if the issue already exists in the [issue tracker](https://github.com/ScaleNix/zcs-to-zcs-migration/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - ZCS version information
   - Relevant log excerpts (sanitize sensitive data)

### Submitting Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/ScaleNix/zcs-to-zcs-migration.git
   cd zcs-to-zcs-migration
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Test in a non-production environment
   - Verify all scripts execute without errors
   - Check for syntax errors with shellcheck

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

6. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Use consistent indentation (4 spaces)
- Add comments for complex sections
- Use meaningful variable names
- Follow bash best practices:
  - Use `set -e` for error handling
  - Quote variables to prevent word splitting
  - Use `[[ ]]` instead of `[ ]` for conditionals

### Script Structure

- Keep functions focused on single tasks
- Use clear function names that describe their purpose
- Add function documentation for complex functions
- Handle errors gracefully with appropriate messages

### Testing

Before submitting:

1. **Syntax check**
   ```bash
   bash -n migrate.sh
   shellcheck migrate.sh
   ```

2. **Test in safe environment**
   - Use test ZCS installations
   - Verify with small datasets first
   - Test all command-line options

3. **Verify documentation**
   - Ensure README is updated
   - Check that examples work
   - Verify configuration file comments

### Documentation

When adding features:

- Update README.md with new functionality
- Add examples for new options
- Update configuration file documentation
- Include any limitations or caveats

### Commit Messages

Follow these conventions:

- Use present tense ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Blank line between summary and details
- Detailed explanation if needed

Example:
```
Add mailbox quota verification

- Add function to check mailbox quotas
- Compare source and destination quotas
- Report any discrepancies in verification
```

## Areas for Contribution

We welcome contributions in these areas:

### High Priority

- **Error handling improvements**: Better error messages and recovery
- **Progress indicators**: Real-time progress for long operations
- **Parallel processing**: Speed up account/mailbox migrations
- **Resume capability**: Resume interrupted migrations

### Features

- **Selective migration**: Migrate specific domains or accounts
- **Incremental sync**: Better support for pre-sync operations
- **Backup integration**: Automatic backup before migration
- **Email notifications**: Status updates via email

### Testing

- **Test suite**: Automated testing framework
- **Mock environment**: Simulated ZCS for testing
- **Performance tests**: Benchmark migration speeds

### Documentation

- **Video tutorials**: Screen recordings of migration process
- **Troubleshooting guide**: Common issues and solutions
- **Best practices**: Real-world migration experiences
- **Language translations**: README in other languages

## Code Review Process

1. All submissions require review
2. Maintainers will provide feedback
3. Address review comments
4. Once approved, changes will be merged

## Community Guidelines

- Be respectful and constructive
- Help others learn and improve
- Share your migration experiences
- Report issues you encounter

## Getting Help

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For private or security-related concerns

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be acknowledged in:
- README.md contributor section
- Release notes for significant contributions
- Project documentation

Thank you for making ZCS migrations easier for everyone!
