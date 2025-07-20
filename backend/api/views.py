"""
API views for network flow dashboard.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg, Max
from django.utils import timezone
from django.db.models.functions import TruncMinute, TruncHour
from datetime import timedelta
import json

from flows.models import NetworkFlow, FlowStatistics, FlowAlert, NetworkInterface
from .serializers import (
    NetworkFlowSerializer, FlowStatisticsSerializer, FlowAlertSerializer,
    NetworkInterfaceSerializer, TopTalkersSerializer, ProtocolDistributionSerializer,
    BandwidthDataSerializer, GeographicDistributionSerializer
)


class NetworkFlowViewSet(viewsets.ModelViewSet):
    """ViewSet for NetworkFlow model."""
    queryset = NetworkFlow.objects.all()
    serializer_class = NetworkFlowSerializer
    
    def get_queryset(self):
        queryset = NetworkFlow.objects.all()
        
        # Filtering
        src_ip = self.request.query_params.get('src_ip')
        dst_ip = self.request.query_params.get('dst_ip')
        protocol = self.request.query_params.get('protocol')
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        
        if src_ip:
            queryset = queryset.filter(src_ip__icontains=src_ip)
        if dst_ip:
            queryset = queryset.filter(dst_ip__icontains=dst_ip)
        if protocol:
            queryset = queryset.filter(protocol_name__icontains=protocol)
        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent network flows."""
        hours = int(request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        
        flows = self.get_queryset().filter(timestamp__gte=since)[:100]
        serializer = self.get_serializer(flows, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get flow summary statistics."""
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        flows = self.get_queryset().filter(timestamp__gte=since)
        
        summary = {
            'total_flows': flows.count(),
            'total_packets': flows.aggregate(Sum('packets'))['packets__sum'] or 0,
            'total_bytes': flows.aggregate(Sum('bytes'))['bytes__sum'] or 0,
            'avg_bandwidth': flows.aggregate(Avg('bandwidth_mbps'))['bandwidth_mbps__avg'] or 0,
            'max_bandwidth': flows.aggregate(Max('bandwidth_mbps'))['bandwidth_mbps__max'] or 0,
            'unique_src_ips': flows.values('src_ip').distinct().count(),
            'unique_dst_ips': flows.values('dst_ip').distinct().count(),
        }
        
        return Response(summary)


class FlowStatisticsViewSet(viewsets.ModelViewSet):
    """ViewSet for FlowStatistics model."""
    queryset = FlowStatistics.objects.all()
    serializer_class = FlowStatisticsSerializer
    
    def get_queryset(self):
        queryset = FlowStatistics.objects.all()
        
        period = self.request.query_params.get('period')
        if period:
            queryset = queryset.filter(period=period)
        
        return queryset.order_by('-timestamp')


class FlowAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for FlowAlert model."""
    queryset = FlowAlert.objects.all()
    serializer_class = FlowAlertSerializer
    
    def get_queryset(self):
        queryset = FlowAlert.objects.all()
        
        severity = self.request.query_params.get('severity')
        acknowledged = self.request.query_params.get('acknowledged')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged == 'true')
        
        return queryset.order_by('-timestamp')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class NetworkInterfaceViewSet(viewsets.ModelViewSet):
    """ViewSet for NetworkInterface model."""
    queryset = NetworkInterface.objects.all()
    serializer_class = NetworkInterfaceSerializer


class TopTalkersView(APIView):
    """Get top talkers (IP addresses with most traffic)."""
    
    def get(self, request):
        hours = int(request.query_params.get('hours', 1))
        limit = int(request.query_params.get('limit', 10))
        since = timezone.now() - timedelta(hours=hours)
        
        # Get top source IPs
        top_src = NetworkFlow.objects.filter(
            timestamp__gte=since
        ).values('src_ip', 'src_country', 'src_city').annotate(
            flows_count=Count('id'),
            packets_count=Sum('packets'),
            bytes_count=Sum('bytes'),
            bandwidth_mbps=Sum('bandwidth_mbps')
        ).order_by('-bytes_count')[:limit]
        
        # Get top destination IPs
        top_dst = NetworkFlow.objects.filter(
            timestamp__gte=since
        ).values('dst_ip', 'dst_country', 'dst_city').annotate(
            flows_count=Count('id'),
            packets_count=Sum('packets'),
            bytes_count=Sum('bytes'),
            bandwidth_mbps=Sum('bandwidth_mbps')
        ).order_by('-bytes_count')[:limit]
        
        # Format data
        src_data = []
        for item in top_src:
            src_data.append({
                'ip_address': item['src_ip'],
                'flows_count': item['flows_count'],
                'packets_count': item['packets_count'],
                'bytes_count': item['bytes_count'],
                'bandwidth_mbps': item['bandwidth_mbps'] or 0,
                'country': item['src_country'] or '',
                'city': item['src_city'] or '',
                'type': 'source'
            })
        
        dst_data = []
        for item in top_dst:
            dst_data.append({
                'ip_address': item['dst_ip'],
                'flows_count': item['flows_count'],
                'packets_count': item['packets_count'],
                'bytes_count': item['bytes_count'],
                'bandwidth_mbps': item['bandwidth_mbps'] or 0,
                'country': item['dst_country'] or '',
                'city': item['dst_city'] or '',
                'type': 'destination'
            })
        
        return Response({
            'top_sources': src_data,
            'top_destinations': dst_data
        })


class ProtocolDistributionView(APIView):
    """Get protocol distribution."""
    
    def get(self, request):
        hours = int(request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        
        total_flows = NetworkFlow.objects.filter(timestamp__gte=since).count()
        
        protocols = NetworkFlow.objects.filter(
            timestamp__gte=since
        ).values('protocol', 'protocol_name').annotate(
            flows_count=Count('id'),
            packets_count=Sum('packets'),
            bytes_count=Sum('bytes')
        ).order_by('-bytes_count')
        
        data = []
        for protocol in protocols:
            percentage = (protocol['flows_count'] / total_flows * 100) if total_flows > 0 else 0
            data.append({
                'protocol': protocol['protocol'],
                'protocol_name': protocol['protocol_name'],
                'flows_count': protocol['flows_count'],
                'packets_count': protocol['packets_count'],
                'bytes_count': protocol['bytes_count'],
                'percentage': round(percentage, 2)
            })
        
        return Response(data)


class BandwidthView(APIView):
    """Get bandwidth data over time."""
    
    def get(self, request):
        hours = int(request.query_params.get('hours', 1))
        interval = request.query_params.get('interval', '1m')  # 1m, 5m, 15m, 1h
        
        since = timezone.now() - timedelta(hours=hours)
        
        if interval == '1m':
            trunc_func = TruncMinute
        elif interval == '1h':
            trunc_func = TruncHour
        else:
            trunc_func = TruncMinute
        
        bandwidth_data = NetworkFlow.objects.filter(
            timestamp__gte=since
        ).annotate(
            time_bucket=trunc_func('timestamp')
        ).values('time_bucket').annotate(
            bandwidth_mbps=Sum('bandwidth_mbps'),
            packets_per_second=Sum('packets') / 60.0  # Assuming 1-minute buckets
        ).order_by('time_bucket')
        
        data = []
        for item in bandwidth_data:
            data.append({
                'timestamp': item['time_bucket'],
                'bandwidth_mbps': item['bandwidth_mbps'] or 0,
                'packets_per_second': item['packets_per_second'] or 0
            })
        
        return Response(data)


class GeographicDistributionView(APIView):
    """Get geographic distribution of flows."""
    
    def get(self, request):
        hours = int(request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        
        total_flows = NetworkFlow.objects.filter(timestamp__gte=since).count()
        
        # Source countries
        src_countries = NetworkFlow.objects.filter(
            timestamp__gte=since,
            src_country__isnull=False
        ).exclude(src_country='').values('src_country').annotate(
            flows_count=Count('id'),
            packets_count=Sum('packets'),
            bytes_count=Sum('bytes')
        ).order_by('-bytes_count')
        
        # Destination countries
        dst_countries = NetworkFlow.objects.filter(
            timestamp__gte=since,
            dst_country__isnull=False
        ).exclude(dst_country='').values('dst_country').annotate(
            flows_count=Count('id'),
            packets_count=Sum('packets'),
            bytes_count=Sum('bytes')
        ).order_by('-bytes_count')
        
        src_data = []
        for country in src_countries:
            percentage = (country['flows_count'] / total_flows * 100) if total_flows > 0 else 0
            src_data.append({
                'country': country['src_country'],
                'city': '',
                'flows_count': country['flows_count'],
                'packets_count': country['packets_count'],
                'bytes_count': country['bytes_count'],
                'percentage': round(percentage, 2),
                'type': 'source'
            })
        
        dst_data = []
        for country in dst_countries:
            percentage = (country['flows_count'] / total_flows * 100) if total_flows > 0 else 0
            dst_data.append({
                'country': country['dst_country'],
                'city': '',
                'flows_count': country['flows_count'],
                'packets_count': country['packets_count'],
                'bytes_count': country['bytes_count'],
                'percentage': round(percentage, 2),
                'type': 'destination'
            })
        
        return Response({
            'source_countries': src_data,
            'destination_countries': dst_data
        })


class RealtimeFlowsView(APIView):
    """Get real-time flow data."""
    
    def get(self, request):
        minutes = int(request.query_params.get('minutes', 5))
        limit = int(request.query_params.get('limit', 50))
        since = timezone.now() - timedelta(minutes=minutes)
        
        flows = NetworkFlow.objects.filter(
            timestamp__gte=since
        ).order_by('-timestamp')[:limit]
        
        serializer = NetworkFlowSerializer(flows, many=True)
        return Response(serializer.data)