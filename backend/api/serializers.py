"""
Serializers for API endpoints.
"""
from rest_framework import serializers
from flows.models import NetworkFlow, FlowStatistics, FlowAlert, NetworkInterface


class NetworkFlowSerializer(serializers.ModelSerializer):
    """Serializer for NetworkFlow model."""
    
    class Meta:
        model = NetworkFlow
        fields = [
            'flow_id', 'timestamp', 'first_seen', 'last_seen',
            'src_ip', 'dst_ip', 'src_port', 'dst_port',
            'protocol', 'protocol_name', 'packets', 'bytes',
            'duration', 'input_interface', 'output_interface',
            'tos', 'tcp_flags', 'src_country', 'src_city',
            'dst_country', 'dst_city', 'src_asn', 'dst_asn',
            'flow_data', 'processed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['flow_id', 'created_at', 'updated_at']


class FlowStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for FlowStatistics model."""
    
    class Meta:
        model = FlowStatistics
        fields = [
            'period', 'timestamp', 'total_flows', 'total_packets',
            'total_bytes', 'top_src_ips', 'top_dst_ips',
            'protocol_distribution', 'top_ports', 'country_distribution',
            'asn_distribution', 'avg_flow_duration', 'max_bandwidth',
            'avg_bandwidth', 'created_at'
        ]
        read_only_fields = ['created_at']


class FlowAlertSerializer(serializers.ModelSerializer):
    """Serializer for FlowAlert model."""
    
    class Meta:
        model = FlowAlert
        fields = [
            'alert_type', 'severity', 'title', 'description',
            'flow', 'flow_data', 'timestamp', 'acknowledged',
            'acknowledged_by', 'acknowledged_at', 'threshold_value',
            'current_value'
        ]
        read_only_fields = ['timestamp']


class NetworkInterfaceSerializer(serializers.ModelSerializer):
    """Serializer for NetworkInterface model."""
    
    class Meta:
        model = NetworkInterface
        fields = [
            'name', 'description', 'interface_id', 'total_flows',
            'total_packets', 'total_bytes', 'active', 'last_updated'
        ]
        read_only_fields = ['last_updated']


class TopTalkersSerializer(serializers.Serializer):
    """Serializer for top talkers data."""
    ip_address = serializers.CharField()
    flows_count = serializers.IntegerField()
    packets_count = serializers.BigIntegerField()
    bytes_count = serializers.BigIntegerField()
    bandwidth_mbps = serializers.FloatField()
    country = serializers.CharField(allow_blank=True)
    city = serializers.CharField(allow_blank=True)


class ProtocolDistributionSerializer(serializers.Serializer):
    """Serializer for protocol distribution data."""
    protocol = serializers.CharField()
    protocol_name = serializers.CharField()
    flows_count = serializers.IntegerField()
    packets_count = serializers.BigIntegerField()
    bytes_count = serializers.BigIntegerField()
    percentage = serializers.FloatField()


class BandwidthDataSerializer(serializers.Serializer):
    """Serializer for bandwidth data."""
    timestamp = serializers.DateTimeField()
    bandwidth_mbps = serializers.FloatField()
    packets_per_second = serializers.FloatField()


class GeographicDistributionSerializer(serializers.Serializer):
    """Serializer for geographic distribution data."""
    country = serializers.CharField()
    city = serializers.CharField(allow_blank=True)
    flows_count = serializers.IntegerField()
    packets_count = serializers.BigIntegerField()
    bytes_count = serializers.BigIntegerField()
    percentage = serializers.FloatField()