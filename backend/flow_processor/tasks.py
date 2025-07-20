"""
Celery tasks for processing network flows.
"""
import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Max, Min
from django.db.models.functions import TruncMinute, TruncHour, TruncDay
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from flows.models import NetworkFlow, FlowStatistics, FlowAlert, NetworkInterface

logger = logging.getLogger(__name__)


@shared_task
def process_network_flows():
    """Process incoming network flows from pmacct."""
    try:
        # Get unprocessed flows
        unprocessed_flows = NetworkFlow.objects.filter(processed=False)
        
        if not unprocessed_flows.exists():
            logger.info("No unprocessed flows found")
            return
        
        logger.info(f"Processing {unprocessed_flows.count()} flows")
        
        # Process flows in batches
        batch_size = 100
        for i in range(0, unprocessed_flows.count(), batch_size):
            batch = unprocessed_flows[i:i + batch_size]
            
            for flow in batch:
                # Add geolocation data if enabled
                if flow.src_country == '':
                    flow.src_country, flow.src_city = get_geolocation(flow.src_ip)
                if flow.dst_country == '':
                    flow.dst_country, flow.dst_city = get_geolocation(flow.dst_ip)
                
                # Add ASN information if available
                if not flow.src_asn:
                    flow.src_asn = get_asn(flow.src_ip)
                if not flow.dst_asn:
                    flow.dst_asn = get_asn(flow.dst_ip)
                
                flow.processed = True
                flow.save()
            
            logger.info(f"Processed batch {i//batch_size + 1}")
        
        # Send real-time updates
        send_flow_updates()
        
        logger.info("Flow processing completed")
        
    except Exception as e:
        logger.error(f"Error processing flows: {e}")
        raise


@shared_task
def aggregate_flow_statistics():
    """Aggregate flow statistics for different time periods."""
    try:
        logger.info("Starting flow statistics aggregation")
        
        # Aggregate for different periods
        periods = [
            ('1m', TruncMinute, timedelta(minutes=1)),
            ('5m', TruncMinute, timedelta(minutes=5)),
            ('15m', TruncMinute, timedelta(minutes=15)),
            ('1h', TruncHour, timedelta(hours=1)),
            ('1d', TruncDay, timedelta(days=1)),
        ]
        
        for period_name, trunc_func, time_delta in periods:
            # Get the time bucket for this period
            now = timezone.now()
            bucket_start = trunc_func(now)
            
            # Check if statistics already exist for this bucket
            if FlowStatistics.objects.filter(period=period_name, timestamp=bucket_start).exists():
                continue
            
            # Get flows for this time period
            flows = NetworkFlow.objects.filter(
                timestamp__gte=bucket_start - time_delta,
                timestamp__lt=bucket_start
            )
            
            if not flows.exists():
                continue
            
            # Calculate statistics
            stats = calculate_flow_statistics(flows, period_name, bucket_start)
            
            # Save statistics
            FlowStatistics.objects.create(**stats)
            
            logger.info(f"Created {period_name} statistics for {bucket_start}")
        
        # Send statistics updates
        send_statistics_updates()
        
        logger.info("Flow statistics aggregation completed")
        
    except Exception as e:
        logger.error(f"Error aggregating statistics: {e}")
        raise


@shared_task
def cleanup_old_flows():
    """Clean up old flow data based on retention policy."""
    try:
        from django.conf import settings
        
        retention_days = settings.NETWORK_FLOW_SETTINGS.get('FLOW_RETENTION_DAYS', 30)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Delete old flows
        old_flows = NetworkFlow.objects.filter(timestamp__lt=cutoff_date)
        count = old_flows.count()
        
        if count > 0:
            old_flows.delete()
            logger.info(f"Deleted {count} old flows (older than {retention_days} days)")
        
        # Clean up old statistics
        old_stats = FlowStatistics.objects.filter(timestamp__lt=cutoff_date)
        stats_count = old_stats.count()
        
        if stats_count > 0:
            old_stats.delete()
            logger.info(f"Deleted {stats_count} old statistics")
        
        # Clean up old alerts (keep for 90 days)
        alert_cutoff = timezone.now() - timedelta(days=90)
        old_alerts = FlowAlert.objects.filter(timestamp__lt=alert_cutoff)
        alert_count = old_alerts.count()
        
        if alert_count > 0:
            old_alerts.delete()
            logger.info(f"Deleted {alert_count} old alerts")
        
    except Exception as e:
        logger.error(f"Error cleaning up old flows: {e}")
        raise


@shared_task
def check_flow_alerts():
    """Check for anomalous flows and create alerts."""
    try:
        logger.info("Checking for flow alerts")
        
        # Check for bandwidth spikes
        check_bandwidth_spikes()
        
        # Check for unusual protocols
        check_unusual_protocols()
        
        # Check for port scans
        check_port_scans()
        
        # Check for DDoS patterns
        check_ddos_patterns()
        
        logger.info("Flow alert checking completed")
        
    except Exception as e:
        logger.error(f"Error checking flow alerts: {e}")
        raise


def calculate_flow_statistics(flows, period, timestamp):
    """Calculate flow statistics for a given time period."""
    # Basic aggregations
    total_flows = flows.count()
    total_packets = flows.aggregate(Sum('packets'))['packets__sum'] or 0
    total_bytes = flows.aggregate(Sum('bytes'))['bytes__sum'] or 0
    avg_flow_duration = flows.aggregate(Avg('duration'))['duration__avg'] or 0
    max_bandwidth = flows.aggregate(Max('bandwidth_mbps'))['bandwidth_mbps__max'] or 0
    avg_bandwidth = flows.aggregate(Avg('bandwidth_mbps'))['bandwidth_mbps__avg'] or 0
    
    # Top source IPs
    top_src_ips = list(flows.values('src_ip').annotate(
        count=Count('id'),
        packets=Sum('packets'),
        bytes=Sum('bytes')
    ).order_by('-bytes')[:10])
    
    # Top destination IPs
    top_dst_ips = list(flows.values('dst_ip').annotate(
        count=Count('id'),
        packets=Sum('packets'),
        bytes=Sum('bytes')
    ).order_by('-bytes')[:10])
    
    # Protocol distribution
    protocol_distribution = dict(flows.values('protocol_name').annotate(
        count=Count('id'),
        packets=Sum('packets'),
        bytes=Sum('bytes')
    ).values_list('protocol_name', 'count'))
    
    # Top ports
    top_ports = list(flows.values('dst_port').annotate(
        count=Count('id'),
        packets=Sum('packets'),
        bytes=Sum('bytes')
    ).order_by('-bytes')[:10])
    
    # Country distribution
    country_distribution = dict(flows.exclude(
        src_country=''
    ).values('src_country').annotate(
        count=Count('id')
    ).values_list('src_country', 'count'))
    
    # ASN distribution
    asn_distribution = dict(flows.exclude(
        src_asn__isnull=True
    ).values('src_asn').annotate(
        count=Count('id')
    ).values_list('src_asn', 'count'))
    
    return {
        'period': period,
        'timestamp': timestamp,
        'total_flows': total_flows,
        'total_packets': total_packets,
        'total_bytes': total_bytes,
        'avg_flow_duration': avg_flow_duration,
        'max_bandwidth': max_bandwidth,
        'avg_bandwidth': avg_bandwidth,
        'top_src_ips': top_src_ips,
        'top_dst_ips': top_dst_ips,
        'protocol_distribution': protocol_distribution,
        'top_ports': top_ports,
        'country_distribution': country_distribution,
        'asn_distribution': asn_distribution,
    }


def get_geolocation(ip_address):
    """Get geolocation information for an IP address."""
    try:
        # This is a placeholder - in a real implementation, you would use
        # a geolocation service like MaxMind GeoIP2, IP2Location, etc.
        # For now, return empty values
        return '', ''
    except Exception as e:
        logger.error(f"Error getting geolocation for {ip_address}: {e}")
        return '', ''


def get_asn(ip_address):
    """Get ASN information for an IP address."""
    try:
        # This is a placeholder - in a real implementation, you would use
        # an ASN lookup service
        return None
    except Exception as e:
        logger.error(f"Error getting ASN for {ip_address}: {e}")
        return None


def send_flow_updates():
    """Send real-time flow updates via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        
        # Get recent flows
        recent_flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-timestamp')[:10]
        
        flow_data = []
        for flow in recent_flows:
            flow_data.append({
                'flow_id': flow.flow_id,
                'src_ip': flow.src_ip,
                'dst_ip': flow.dst_ip,
                'protocol': flow.protocol_name,
                'packets': flow.packets,
                'bytes': flow.bytes,
                'bandwidth_mbps': flow.bandwidth_mbps,
                'timestamp': flow.timestamp.isoformat(),
            })
        
        # Send to flows group
        async_to_sync(channel_layer.group_send)(
            "flows",
            {
                "type": "flow_update",
                "data": flow_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending flow updates: {e}")


def send_statistics_updates():
    """Send statistics updates via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        
        # Get latest statistics
        stats = FlowStatistics.objects.filter(
            period='1m',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-timestamp').first()
        
        if stats:
            stats_data = {
                'total_flows': stats.total_flows,
                'total_packets': stats.total_packets,
                'total_bytes': stats.total_bytes,
                'avg_bandwidth': stats.avg_bandwidth,
                'protocol_distribution': stats.protocol_distribution,
                'top_src_ips': stats.top_src_ips[:5],
                'top_dst_ips': stats.top_dst_ips[:5],
                'timestamp': stats.timestamp.isoformat(),
            }
            
            # Send to flows group
            async_to_sync(channel_layer.group_send)(
                "flows",
                {
                    "type": "statistics_update",
                    "data": stats_data
                }
            )
        
    except Exception as e:
        logger.error(f"Error sending statistics updates: {e}")


def check_bandwidth_spikes():
    """Check for bandwidth spikes and create alerts."""
    try:
        # Get recent flows and check for bandwidth spikes
        recent_flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        )
        
        if recent_flows.exists():
            avg_bandwidth = recent_flows.aggregate(Avg('bandwidth_mbps'))['bandwidth_mbps__avg'] or 0
            max_bandwidth = recent_flows.aggregate(Max('bandwidth_mbps'))['bandwidth_mbps__max'] or 0
            
            # Alert if max bandwidth is 5x higher than average
            if max_bandwidth > avg_bandwidth * 5 and max_bandwidth > 100:  # 100 Mbps threshold
                FlowAlert.objects.create(
                    alert_type='bandwidth_spike',
                    severity='medium',
                    title=f'Bandwidth spike detected: {max_bandwidth:.2f} Mbps',
                    description=f'Maximum bandwidth {max_bandwidth:.2f} Mbps is significantly higher than average {avg_bandwidth:.2f} Mbps',
                    threshold_value=avg_bandwidth * 5,
                    current_value=max_bandwidth
                )
    
    except Exception as e:
        logger.error(f"Error checking bandwidth spikes: {e}")


def check_unusual_protocols():
    """Check for unusual protocols and create alerts."""
    try:
        # Get recent flows and check for unusual protocols
        recent_flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        )
        
        # Check for non-standard protocols
        unusual_protocols = recent_flows.exclude(
            protocol__in=[1, 6, 17]  # ICMP, TCP, UDP
        )
        
        if unusual_protocols.exists():
            for flow in unusual_protocols:
                FlowAlert.objects.create(
                    alert_type='unusual_protocol',
                    severity='low',
                    title=f'Unusual protocol detected: {flow.protocol_name}',
                    description=f'Protocol {flow.protocol_name} (ID: {flow.protocol}) detected from {flow.src_ip} to {flow.dst_ip}',
                    flow=flow,
                    current_value=flow.protocol
                )
    
    except Exception as e:
        logger.error(f"Error checking unusual protocols: {e}")


def check_port_scans():
    """Check for port scan patterns and create alerts."""
    try:
        # Get recent flows and check for port scan patterns
        recent_flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        )
        
        # Check for multiple connections from same source to different ports
        port_scan_sources = recent_flows.values('src_ip').annotate(
            unique_ports=Count('dst_port', distinct=True)
        ).filter(unique_ports__gte=10)  # Alert if 10+ different ports
        
        for source in port_scan_sources:
            FlowAlert.objects.create(
                alert_type='port_scan',
                severity='medium',
                title=f'Potential port scan from {source["src_ip"]}',
                description=f'Source {source["src_ip"]} connected to {source["unique_ports"]} different ports',
                threshold_value=10,
                current_value=source['unique_ports']
            )
    
    except Exception as e:
        logger.error(f"Error checking port scans: {e}")


def check_ddos_patterns():
    """Check for DDoS attack patterns and create alerts."""
    try:
        # Get recent flows and check for DDoS patterns
        recent_flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        )
        
        # Check for multiple sources targeting same destination
        ddos_targets = recent_flows.values('dst_ip').annotate(
            unique_sources=Count('src_ip', distinct=True)
        ).filter(unique_sources__gte=50)  # Alert if 50+ different sources
        
        for target in ddos_targets:
            FlowAlert.objects.create(
                alert_type='ddos_attack',
                severity='high',
                title=f'Potential DDoS attack on {target["dst_ip"]}',
                description=f'Destination {target["dst_ip"]} received traffic from {target["unique_sources"]} different sources',
                threshold_value=50,
                current_value=target['unique_sources']
            )
    
    except Exception as e:
        logger.error(f"Error checking DDoS patterns: {e}")