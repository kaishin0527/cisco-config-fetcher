


# Cisco Config Fetcher Operational Guide

## Getting Started

### Prerequisites
- **Python 3.12+**: Required runtime environment
- **pip**: Package installation tool
- **Network Access**: Connectivity to Cisco devices
- **Environment Variables**: For secure credential management

### Installation Steps

#### 1. Install Dependencies
```bash
# Install required Python packages
pip install flask pyyaml netmiko

# Or install from requirements (if available)
pip install -r requirements.txt
```

#### 2. Set Environment Variables
```bash
# Set device credentials (example)
export DEVICE_LOGIN_PASSWORD="your_login_password"
export DEVICE_ENABLE_PASSWORD="your_enable_password"

# Verify environment variables
echo $DEVICE_LOGIN_PASSWORD
echo $DEVICE_ENABLE_PASSWORD
```

#### 3. Configure Device Settings
Edit `devices_updated.yaml` to add your Cisco devices:
```yaml
devices:
  your_router:
    host: 192.168.1.1
    device_type: cisco_ios_ssh
    username: admin
    password: !ENV ${DEVICE_LOGIN_PASSWORD}
    secret: !ENV ${DEVICE_ENABLE_PASSWORD}
    group: core_routers
```

## Running the Application

### Option 1: Web Interface (Recommended)
```bash
# Start the web application
python web_app_complete.py

# Access the web interface
# Open browser to: http://localhost:51361
```

### Option 2: Command Line Interface
```bash
# Execute a scenario
python cisco_config_fetcher_final.py scenario_parallel.yaml

# Execute with custom configuration
python cisco_config_fetcher_parallel.py scenario_advanced.yaml
```

## Web Interface Usage

### Main Dashboard (`/`)
- **Configuration Summary**: View device, command group, and scenario counts
- **Quick Links**: Navigation to all management functions
- **System Status**: Overview of system health

### Device Management (`/devices`)
**Features:**
- List all configured devices
- Add new devices
- Edit existing device configurations
- Delete devices

**Operations:**
1. Click "Add Device" to create new device
2. Fill in device details (host, type, credentials)
3. Assign device to appropriate group
4. Save configuration

### Command Group Management (`/command_groups`)
**Features:**
- Manage command sets for different device types
- Create custom command groups
- Organize commands by function

**Example Command Groups:**
```yaml
core_routers:
  - "show version"
  - "show ip route"
  - "show ip interface brief"
  
access_switches:
  - "show vlan brief"
  - "show interface status"
  - "show spanning-tree"
```

### Scenario Management (`/scenarios`)
**Features:**
- Create execution workflows
- Define sequential or parallel tasks
- Set wait times and user interaction points

**Scenario Structure:**
```yaml
name: "network_audit"
description: "Comprehensive network audit"
steps:
  - sequence: 1
    device_group: "core_routers"
    command_group: "core_commands"
    wait_after: 30
    wait_for_user: true
```

### Command Execution (`/execute`)
**Features:**
- Execute commands on individual devices
- Run scenarios on multiple devices
- Monitor execution progress
- Download results

### Configuration Validation (`/config_validation`)
**Features:**
- Validate all configuration files
- Check for missing required fields
- Verify environment variables
- Report configuration issues

## Command Line Usage

### Basic Device Connection
```bash
# Connect to a single device
python cisco_config_fetcher_final.py

# You'll be prompted for:
# - Device configuration file path
# - Login password (if not in environment)
# - Enable password (if not in environment)
```

### Scenario Execution
```bash
# Execute predefined scenario
python cisco_config_fetcher_final.py scenario_basic.yaml

# Execute with parallel processing
python cisco_config_fetcher_parallel.py scenario_parallel.yaml
```

### Configuration Management
```bash
# Validate configuration files
python -c "from config_manager import config_manager; print(config_manager.validate_all_configs())"

# Get configuration summary
python -c "from config_manager import config_manager; print(config_manager.get_config_summary())"
```

## Configuration Files

### Device Configuration (`devices_updated.yaml`)
**Structure:**
```yaml
devices:
  device_name:
    host: device_ip_or_hostname
    device_type: cisco_ios_ssh  # or cisco_ios_telnet, cisco_asa
    username: admin
    password: !ENV ${DEVICE_LOGIN_PASSWORD}
    secret: !ENV ${DEVICE_ENABLE_PASSWORD}
    group: device_group_name
    prompt_pattern: "^[a-zA-Z0-9_\-]+#$"  # Optional custom prompt
```

### Command Groups (`command_groups.yaml`)
**Structure:**
```yaml
command_groups:
  group_name:
    - "show command 1"
    - "show command 2"
    - "show command 3"
```

### Scenarios (`scenario_*.yaml`)
**Structure:**
```yaml
name: "scenario_name"
description: "Scenario description"
steps:
  - sequence: 1
    device_group: "group_name"
    command_group: "command_group_name"
    wait_after: 30          # Optional: seconds to wait
    wait_for_user: true     # Optional: pause for user input
```

## Troubleshooting

### Common Issues

#### 1. Connection Failures
**Symptoms:** "Connection timeout" or "Authentication failed"
**Solutions:**
- Verify device IP address and connectivity
- Check SSH/Telnet services are running
- Confirm credentials are correct
- Check network firewall rules

#### 2. Configuration Errors
**Symptoms:** "Configuration validation failed"
**Solutions:**
- Check YAML syntax and indentation
- Verify required fields are present
- Ensure environment variables are set
- Validate device types are supported

#### 3. Web Interface Issues
**Symptoms:** "Page not found" or "Server error"
**Solutions:**
- Check Flask application is running
- Verify port 51361 is available
- Check template files exist
- Review Flask logs for errors

#### 4. Permission Issues
**Symptoms:** "Permission denied" or "File not found"
**Solutions:**
- Check file permissions on configuration files
- Ensure Python has read/write access
- Verify upload directory exists

### Debug Mode

#### Enable Debug Logging
```bash
# For CLI applications
python cisco_config_fetcher_final.py --debug

# For web application
export FLASK_DEBUG=1
python web_app_complete.py
```

#### Check Logs
```bash
# View application logs
tail -f cisco_config_fetcher.log
tail -f server.log
tail -f web_app.log
```

### Network Testing
```bash
# Test device connectivity
ping device_ip
telnet device_ip 23      # For Telnet
ssh username@device_ip   # For SSH

# Test port availability
nc -zv device_ip 22      # SSH port
nc -zv device_ip 23      # Telnet port
```

## Best Practices

### Security
1. **Environment Variables**: Always use environment variables for passwords
2. **Least Privilege**: Use minimal necessary credentials
3. **Network Security**: Use SSH instead of Telnet when possible
4. **Access Control**: Restrict web interface access

### Performance
1. **Connection Pooling**: Reuse connections for multiple commands
2. **Parallel Execution**: Use parallel processing for multiple devices
3. **Caching**: Leverage configuration caching
4. **Batch Operations**: Group related commands together

### Maintenance
1. **Regular Updates**: Keep dependencies updated
2. **Log Rotation**: Implement log rotation policies
3. **Configuration Backups**: Backup configuration files regularly
4. **Monitoring**: Monitor system performance and errors

### Backup and Recovery
```bash
# Backup configuration files
cp devices_updated.yaml devices_backup_$(date +%Y%m%d).yaml
cp command_groups.yaml command_groups_backup_$(date +%Y%m%d).yaml

# Restore configuration
cp devices_backup_20250819.yaml devices_updated.yaml
```

## Advanced Usage

### Custom Command Groups
Create specialized command groups for specific tasks:
```yaml
security_audit:
  - "show access-lists"
  - "show crypto ipsec sa"
  - "show crypto isakmp sa"
  
performance_monitoring:
  - "show processes cpu sorted"
  - "show memory statistics"
  - "show interfaces status"
```

### Complex Scenarios
Build multi-step workflows with conditional logic:
```yaml
name: "complex_network_audit"
description: "Comprehensive audit with user interaction"
steps:
  - sequence: 1
    device_group: "core_routers"
    command_group: "basic_info"
    wait_after: 10
    
  - sequence: 2
    device_group: "core_routers"
    command_group: "security_audit"
    wait_for_user: true
    
  - sequence: 3
    device_group: "access_switches"
    command_group: "configuration_check"
```

### Integration with External Tools
```bash
# Export results to external tools
python cisco_config_fetcher_final.py scenario.yaml | grep "ERROR" > error_report.txt

# Integrate with monitoring systems
python cisco_config_fetcher_parallel.py scenario.yaml 2>&1 | logger -t cisco-config
```

This operational guide provides comprehensive instructions for deploying, managing, and troubleshooting the Cisco Config Fetcher application in various environments.


