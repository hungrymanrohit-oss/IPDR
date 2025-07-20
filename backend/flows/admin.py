"""
Admin configuration for flows app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import NetworkFlow, FlowStatistics, FlowAlert, NetworkInterface


@admin.register(NetworkFlow)
class NetworkFlowAdmin(admin.ModelAdmin):
    list_display = [
        'flow_id', 'src_ip', 'dst_ip', 'protocol_name', 
        'packets', 'bytes', 'bandwidth_mbps', 'timestamp'
    ]
    list_filter = [
        'protocol_name', 'src_country', 'dst_country', 
        'processed', 'timestamp'
    ]
    search_fields = ['src_ip', 'dst_ip', 'flow_id']
    readonly_fields = ['flow_id', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Flow Information', {
            'fields': ('flow_id', 'timestamp', 'first_seen', 'last_seen')
        }),
        ('Source & Destination', {
            'fields': ('src_ip', 'src_port', 'dst_ip', 'dst_port')
        }),
        ('Protocol & Statistics', {
            'fields': ('protocol', 'protocol_name', 'packets', 'bytes', 'duration')
        }),
        ('Network Details', {
            'fields': ('input_interface', 'output_interface', 'tos', 'tcp_flags')
        }),
        ('Geolocation', {
            'fields': ('src_country', 'src_city', 'dst_country', 'dst_city')
        }),
        ('ASN Information', {
            'fields': ('src_asn', 'dst_asn')
        }),
        ('Metadata', {
            'fields': ('flow_data', 'processed', 'created_at', 'updated_at')
        }),
    )
    
    def bandwidth_mbps(self, obj):
        return f"{obj.bandwidth_mbps:.2f} Mbps"
    bandwidth_mbps.short_description = 'Bandwidth (Mbps)'


@admin.register(FlowStatistics)
class FlowStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'period', 'timestamp', 'total_flows', 'total_packets', 
        'total_bytes', 'avg_bandwidth'
    ]
    list_filter = ['period', 'timestamp']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('period', 'timestamp')
        }),
        ('Aggregated Statistics', {
            'fields': ('total_flows', 'total_packets', 'total_bytes')
        }),
        ('Top Talkers', {
            'fields': ('top_src_ips', 'top_dst_ips')
        }),
        ('Distributions', {
            'fields': ('protocol_distribution', 'top_ports', 'country_distribution', 'asn_distribution')
        }),
        ('Metrics', {
            'fields': ('avg_flow_duration', 'max_bandwidth', 'avg_bandwidth')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(FlowAlert)
class FlowAlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_type', 'severity', 'title', 'timestamp', 
        'acknowledged', 'current_value'
    ]
    list_filter = [
        'alert_type', 'severity', 'acknowledged', 'timestamp'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'severity', 'title', 'description')
        }),
        ('Flow Data', {
            'fields': ('flow', 'flow_data')
        }),
        ('Thresholds', {
            'fields': ('threshold_value', 'current_value')
        }),
        ('Status', {
            'fields': ('acknowledged', 'acknowledged_by', 'acknowledged_at')
        }),
        ('Metadata', {
            'fields': ('timestamp',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('flow', 'acknowledged_by')


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'interface_id', 'active', 'total_flows', 
        'total_packets', 'total_bytes', 'last_updated'
    ]
    list_filter = ['active', 'last_updated']
    search_fields = ['name', 'description']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Interface Information', {
            'fields': ('name', 'description', 'interface_id')
        }),
        ('Statistics', {
            'fields': ('total_flows', 'total_packets', 'total_bytes')
        }),
        ('Status', {
            'fields': ('active', 'last_updated')
        }),
    )