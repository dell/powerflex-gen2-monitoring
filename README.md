# PowerFlex Gen2 Monitoring

A comprehensive monitoring solution for Dell PowerFlex storage systems, using Telegraf, InfluxDB, and Grafana on Enterprise Linux 9 (RHEL9 and compatible distributions). This is an open source solution and is not an officially supported solution by Dell Technologies. Limited support is provided by the community. To open a ticket please email PowerFlex.Monitoring@Dell.com. 

## Overview

This project provides a complete monitoring stack for PowerFlex Gen2 (erasure-coding-based) storage clusters, version 5.x and higher. It is not compatible with Gen1 (mirroring-based) PowerFlex systems. It collectss metrics via custom Python scripts using Telegraf, Sformats and stores these in InfluxDB, and visualizes them through pre-built Grafana dashboards.

A pre-packaged all-in-one virtual machine is provided and is the easiest way to use the tools. However, if you wish to run these tools on your own EL9 distribution, this document will guide you through the process. While it is possible to run these tools on other distributions, it will require some additional configuration and testing on your part.

## System Requirements

### Operating System
- Enterprise Linux 9 (RHEL 9, Rocky Linux 9, AlmaLinux 9, or compatible EL9 distributions)
- Begin with the minimal install image and select the "Standard" software package group.

### Required Software Versions

**Tested and validated with the following versions:**
- **InfluxDB**: 1.12.2
- **Telegraf**: 1.37.2
- **Grafana**: 9.5.21
- **Python**: 3.9 (included with EL9)

*Note: Other versions may work, but users are responsible for testing and verifying compatibility.*

**Minimum versions that might work:**
- **InfluxDB**: 1.8.x or later
- **Telegraf**: 1.20.x or later  
- **Grafana**: 9.0.x or later
- **Python**: 3.9 or later


### Hardware Requirements
- Minimum 2 CPU cores (4 recommended)
- Minimum 4GB RAM (8 recommended)
- Minimum 64GB disk space for metrics storage (128GB recommended for longer retention)

**Important**: If /var/ is mounted on a separate partition, ensure that it has enough space for the InfluxDB database. The default InfluxDB database location is `/var/lib/influxdb`.

## Installation

### 1. Project Placement

Clone or extract this project to `/var/local/telegraf-powerflex/`:

```bash
# If cloning from git repository
git clone <repository-url> /var/local/telegraf-powerflex/

# Ensure proper permissions
chmod 755 /var/local/telegraf-powerflex
chmod +x /var/local/telegraf-powerflex/*.py
chmod +x /var/local/telegraf-powerflex/sio_sdk/*.py
```

### 2. Install Required Packages

**Recommended**: Install the 3rd party packages from their official release links to ensure compatibility:

```bash
# Install required packages from OS provider
dnf install python3 python3-pip 

# Download influxdb, telegraf, and grafana from the provider's direct links:
curl -O https://dl.influxdata.com/influxdb/releases/influxdb-1.12.2-4.x86_64.rpm
curl -O https://dl.influxdata.com/telegraf/releases/telegraf-1.37.2-1.x86_64.rpm
curl -O https://dl.grafana.com/oss/release/grafana-9.5.21-1.x86_64.rpm

# Install the downloaded packages
dnf localinstall influxdb-1.12.2-4.x86_64.rpm telegraf-1.37.2-1.x86_64.rpm grafana-9.5.21-1.x86_64.rpm
```

**Suggested**: To prevent automatic OS updates from upgrading these packages to potentially incompatible versions, you may want to edit `/etc/dnf/dnf.conf` and add package exclusions:

```bash
# Add to /etc/dnf/dnf.conf:
exclude=influxdb* telegraf* grafana*
```

### 3. Python Dependencies

Install required Python packages:

```bash
cd /var/local/telegraf-powerflex
pip3 install pyyaml requests
```

## Configuration

### 1. PowerFlex Cluster Info Configuration

Copy the example cluster configuration and update with your cluster details:

```bash
cp /var/local/telegraf-powerflex/clusters_example.yaml /var/local/telegraf-powerflex/clusters.yaml
```

Then edit `clusters.yaml` with your PowerFlex Gen1 cluster information:

```yaml
flex-cluster1:
  gateway: your-powerflex-manager-ingress-ip
  username: your-monitor-user
  password: your-password
```

**Note**: Create a unique PowerFlex user with only monitor-level permissions and use that here for security.

### 2. Telegraf Configuration

Copy the provided Telegraf configuration:

```bash
cp /var/local/telegraf-powerflex/example-telegraf-powerflex-config/powerflex-telegraf-influxdb.conf /etc/telegraf/telegraf.d/
```

For monitoring multiple clusters, update the commands section in `/etc/telegraf/telegraf.d/powerflex-telegraf-influxdb.conf`:

```toml
[[inputs.exec]]
  commands = [
    '/usr/bin/python3 /var/local/telegraf-powerflex/siocli.py flex-cluster1',
    '/usr/bin/python3 /var/local/telegraf-powerflex/siocli.py flex-cluster2'
  ]
  data_format = "influx"
  interval = "10s"
  timeout = "5s"
  tagexclude = ["host"]
```

### 3. InfluxDB Configuration

Highly suggested for best performance: Copy the example InfluxDB configuration into place
This configuration is optimized for these PowerFlex monitoring tools and provides a good balance between performance and resource usage.

```bash
cp /var/local/telegraf-powerflex/example-influxdbv1-config/influxdb.conf /etc/influxdb/
```

### 4. Grafana Configuration

Highly suggested: Copy the provided Grafana configuration and SSL certificates:
This configuration enables a number of security measures not provided by the default configuration.

```bash
# Copy configuration
cp /var/local/telegraf-powerflex/example-grafana-config/grafana.ini /etc/grafana/

# Copy SSL certificates (or provide your own)
cp /var/local/telegraf-powerflex/example-grafana-config/powerflex.crt /etc/grafana/
cp /var/local/telegraf-powerflex/example-grafana-config/powerflex.key /etc/grafana/

# Set proper permissions
chmod 600 /etc/grafana/powerflex.key
chmod 644 /etc/grafana/powerflex.crt
```

The provided `grafana.ini` assumes HTTPS will be used with the included SSL certificates. If you prefer to use your own certificates, update the paths in the `[server]` section:

If you keep the default configuration, you can access Grafana at `http://<your-server-ip>` (default port 3000).

```ini
[server]
protocol = https
cert_file = /path/to/your/certificate.crt
cert_key = /path/to/your/private.key
```

**Note 1**: In order to allow Grafana to run on port 443, you must create an override for the default systemd service to allow it to bind to port 443. This is not required if you use the default port 3000. 

```bash
# Create override file
systemctl edit grafana-server

# Add the following to the override file
[Service]
# Give the CAP_NET_BIND_SERVICE capability
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=false
```

**Note 2**: If you installed the suggested build of Grafana from the link provided above, then this configuration will work as described. If you install Grafana from the OS provider repo, it will probably also install associated selinux packages. You will need to create selinux policies to allow Grafana to run on port 443.

Add the firewall rule to allow users to access Grafana on 443/https

```bash
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 5. Enable all services and start

Enable and start all services to apply configurations:

```bash
# Enable and start services
systemctl enable --now influxdb telegraf grafana-server
```

## Grafana Setup

### Add InfluxDB Data Source

1. Access Grafana at `https://<your-server-ip>` (or `http://<your-server-ip>:3000` if using default port)
2. Login with default credentials (admin/admin) and set a new password
3. Navigate to **Administration → Data Sources** (gear icon → Data Sources)
4. Click **Add new data source** and select **InfluxDB**
5. Configure the data source with these settings:
   - **Name**: `PowerFlex-InfluxDB` (or your preferred name)
   - **Query Language**: InfluxQL
   - **URL**: `http://localhost:8086`
   - **Database**: `telegraf` (default Telegraf database)
   - **User**: Leave blank (default InfluxDB setup)
   - **Password**: Leave blank (default InfluxDB setup)
6. Click **Save & Test** to verify the connection

### Pre-built Dashboards
Pre-built dashboards are available in the `example-grafana-dashboards/` directory:

- **PowerFlex - 0. Cluster (Overview)**: High-level cluster overview
- **PowerFlex - 1. Clusters (Stacked)**: Multi-cluster comparison view
- **PowerFlex - 2. Devices**: Storage device metrics
- **PowerFlex - 3. Pools**: Storage pool performance and capacity
- **PowerFlex - 4. SDC**: Storage Data Client metrics
- **PowerFlex - 5. SDS**: Storage Data Server metrics  
- **PowerFlex - 6. Volumes**: Volume performance and usage
- **PowerFlex - 7. Cluster Capacity**: Cluster-wide capacity planning

### Importing Dashboards

1. Access Grafana at `https://<your-server-ip>` (default port 443)
2. Login with default credentials (admin/admin)
3. Navigate to **+ → Import**
4. Upload the JSON files from `example-grafana-dashboards/`
5. Configure the InfluxDB data source when prompted

## Project Structure

```
/var/local/telegraf-powerflex/
├── README.md                           # This file
├── LICENSE                             # Apache 2.0 License
├── OS_PACKAGE_SBOM.txt                 # Software Bill of Materials
├── THIRD_PARTY_LICENSES                # Third-party license information
├── clusters.yaml                       # Your cluster configuration (you must create this; example provided in clusters_example.yaml)
├── clusters_example.yaml               # Example cluster configuration
├── siocli.py                          # PowerFlex metrics collection script
├── siometrics.py                      # Metrics formatting utilities
├── sio_sdk/                           # PowerFlex SDK module
│   ├── __init__.py                    # SDK initialization and collection functions
│   └── SioSdk.py                      # REST API client and authentication
├── tests/                             # Unit tests
│   ├── test_sio_sdk.py               # SDK tests
│   ├── test_siocli.py                # CLI tests
│   └── test_siometrics_tags.py       # Metrics tagging tests
├── example-telegraf-powerflex-config/ # Telegraf configuration examples
│   └── powerflex-telegraf-influxdb.conf
├── example-influxdbv1-config/         # InfluxDB configuration examples
│   └── influxdb.conf
├── example-grafana-config/            # Grafana configuration examples
│   ├── grafana.ini
│   ├── powerflex.crt
│   └── powerflex.key
└── example-grafana-dashboards/        # Pre-built Grafana dashboards
    ├── PowerFlex - 0. Cluster (Overview).json
    ├── PowerFlex - 1. Clusters (Stacked).json
    ├── PowerFlex - 2. Devices.json
    ├── PowerFlex - 3. Pools.json
    ├── PowerFlex - 4. SDC.json
    ├── PowerFlex - 5. SDS.json
    ├── PowerFlex - 6. Volumes.json
    └── PowerFlex - 7. Cluster Capacity.json
```

## Optional Tools

The pre-packed Monitoring VM has a number of scripts in `/root/tools/`. These are not required for basic operation but may provide additional utilities for advanced users. These will be available in a separate repository if needed.

## Troubleshooting

### Common Issues

1. **Telegraf not collecting metrics**: Check that `clusters.yaml` is properly configured and the Python scripts have execute permissions.

   You can test the Python scripts manually to ensure they are working:

   ```bash
   python3 /var/local/telegraf-powerflex/siocli.py flex-cluster1
   ```

   Any errors will be displayed in the terminal.

2. **Grafana not accessible**: Verify SSL certificate paths in `grafana.ini` and check firewall settings for port 443.

3. **InfluxDB connection issues**: Ensure InfluxDB is running and the telegraf configuration points to the correct database and port on localhost.

4. **For all services**: Check service status with:

   ```bash
   journalctl -u <service-name>
   ```

### Log Locations

- Most of the logging is sent to `/var/log/messages`.
- Some additional Grafana logs are available in `/var/log/grafana/grafana.log`.

### Service Status

Check service status with:

```bash
systemctl status influxdb telegraf grafana-server
```

## Security Considerations

- Use only dedicated PowerFlex monitoring-type user accounts with minimal required permissions
- Consider rotating the credentials periodically for production deployments
- Enable firewall rules to restrict access to Grafana and InfluxDB

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Support

For issues related to:
- **PowerFlex connectivity**: Check cluster credentials and network connectivity
- **Metric collection**: Review `/var/log/messages` and manually run the Python script to verify output
- **Dashboard issues**: Verify InfluxDB data source configuration in Grafana

