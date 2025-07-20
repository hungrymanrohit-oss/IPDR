"""
Models for network flow data storage and analysis.
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.conf import settings
import json


class NetworkFlow(models.Model):
    """
    Model for storing network flow data with TimescaleDB hypertable support.
    """
    # Flow identification
    flow_id = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Timestamps
    timestamp = models.DateTimeField(db_index=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    
    # Source and destination
    src_ip = models.GenericIPAddressField(db_index=True)
    dst_ip = models.GenericIPAddressField(db_index=True)
    src_port = models.IntegerField()
    dst_port = models.IntegerField()
    
    # Protocol information
    protocol = models.IntegerField()  # IP protocol number
    protocol_name = models.CharField(max_length=20, blank=True)
    
    # Flow statistics
    packets = models.BigIntegerField(default=0)
    bytes = models.BigIntegerField(default=0)
    duration = models.FloatField(default=0.0)  # in seconds
    
    # Network interface
    input_interface = models.IntegerField(null=True, blank=True)
    output_interface = models.IntegerField(null=True, blank=True)
    
    # Additional metadata
    tos = models.IntegerField(default=0)  # Type of Service
    tcp_flags = models.IntegerField(default=0)
    
    # Geolocation data (if available)
    src_country = models.CharField(max_length=2, blank=True)
    src_city = models.CharField(max_length=100, blank=True)
    dst_country = models.CharField(max_length=2, blank=True)
    dst_city = models.CharField(max_length=100, blank=True)
    
    # ASN information
    src_asn = models.IntegerField(null=True, blank=True)
    dst_asn = models.IntegerField(null=True, blank=True)
    
    # Additional flow data
    flow_data = JSONField(default=dict, blank=True)
    
    # Processing metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'network_flows'
        indexes = [
            models.Index(fields=['timestamp', 'src_ip']),
            models.Index(fields=['timestamp', 'dst_ip']),
            models.Index(fields=['timestamp', 'protocol']),
            models.Index(fields=['src_ip', 'dst_ip']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.src_ip}:{self.src_port} -> {self.dst_ip}:{self.dst_port} ({self.protocol_name})"
    
    def save(self, *args, **kwargs):
        # Generate flow_id if not provided
        if not self.flow_id:
            self.flow_id = self._generate_flow_id()
        
        # Set protocol name if not provided
        if not self.protocol_name:
            self.protocol_name = self._get_protocol_name()
        
        super().save(*args, **kwargs)
    
    def _generate_flow_id(self):
        """Generate a unique flow ID based on flow characteristics."""
        import hashlib
        flow_string = f"{self.src_ip}:{self.src_port}:{self.dst_ip}:{self.dst_port}:{self.protocol}:{self.first_seen.isoformat()}"
        return hashlib.sha256(flow_string.encode()).hexdigest()[:16]
    
    def _get_protocol_name(self):
        """Get protocol name from protocol number."""
        protocol_names = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
            47: 'GRE',
            50: 'ESP',
            51: 'AH',
            89: 'OSPF',
        }
        return protocol_names.get(self.protocol, f'PROTO_{self.protocol}')
    
    @property
    def bandwidth_mbps(self):
        """Calculate bandwidth in Mbps."""
        if self.duration > 0:
            return (self.bytes * 8) / (self.duration * 1000000)
        return 0
    
    @property
    def packets_per_second(self):
        """Calculate packets per second."""
        if self.duration > 0:
            return self.packets / self.duration
        return 0


class FlowStatistics(models.Model):
    """
    Aggregated flow statistics for different time periods.
    """
    PERIOD_CHOICES = [
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('1h', '1 Hour'),
        ('1d', '1 Day'),
    ]
    
    period = models.CharField(max_length=3, choices=PERIOD_CHOICES)
    timestamp = models.DateTimeField(db_index=True)
    
    # Aggregated statistics
    total_flows = models.BigIntegerField(default=0)
    total_packets = models.BigIntegerField(default=0)
    total_bytes = models.BigIntegerField(default=0)
    
    # Top talkers
    top_src_ips = JSONField(default=list)
    top_dst_ips = JSONField(default=list)
    
    # Protocol distribution
    protocol_distribution = JSONField(default=dict)
    
    # Port distribution
    top_ports = JSONField(default=list)
    
    # Geographic distribution
    country_distribution = JSONField(default=dict)
    
    # ASN distribution
    asn_distribution = JSONField(default=dict)
    
    # Additional metrics
    avg_flow_duration = models.FloatField(default=0.0)
    max_bandwidth = models.FloatField(default=0.0)
    avg_bandwidth = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'flow_statistics'
        unique_together = ['period', 'timestamp']
        indexes = [
            models.Index(fields=['period', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_period_display()} - {self.timestamp}"


class FlowAlert(models.Model):
    """
    Alerts for anomalous network flows.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('bandwidth_spike', 'Bandwidth Spike'),
        ('unusual_protocol', 'Unusual Protocol'),
        ('port_scan', 'Port Scan'),
        ('ddos_attack', 'DDoS Attack'),
        ('data_exfiltration', 'Data Exfiltration'),
        ('custom', 'Custom'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Related flow data
    flow = models.ForeignKey(NetworkFlow, on_delete=models.CASCADE, null=True, blank=True)
    flow_data = JSONField(default=dict)
    
    # Alert metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Alert configuration
    threshold_value = models.FloatField(null=True, blank=True)
    current_value = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'flow_alerts'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.alert_type} - {self.title} ({self.severity})"


class NetworkInterface(models.Model):
    """
    Network interfaces for flow monitoring.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    interface_id = models.IntegerField(unique=True)
    
    # Interface statistics
    total_flows = models.BigIntegerField(default=0)
    total_packets = models.BigIntegerField(default=0)
    total_bytes = models.BigIntegerField(default=0)
    
    # Status
    active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'network_interfaces'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (ID: {self.interface_id})"