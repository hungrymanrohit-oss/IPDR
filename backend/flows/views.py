"""
Views for flows app.
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import NetworkFlow, FlowStatistics, FlowAlert, NetworkInterface


def flow_list(request):
    """Display a list of network flows."""
    flows = NetworkFlow.objects.all()
    
    # Filtering
    src_ip = request.GET.get('src_ip')
    dst_ip = request.GET.get('dst_ip')
    protocol = request.GET.get('protocol')
    
    if src_ip:
        flows = flows.filter(src_ip__icontains=src_ip)
    if dst_ip:
        flows = flows.filter(dst_ip__icontains=dst_ip)
    if protocol:
        flows = flows.filter(protocol_name__icontains=protocol)
    
    # Pagination
    paginator = Paginator(flows, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'flows': page_obj,
        'total_flows': flows.count(),
    }
    return render(request, 'flows/flow_list.html', context)


def flow_detail(request, flow_id):
    """Display details of a specific network flow."""
    flow = get_object_or_404(NetworkFlow, flow_id=flow_id)
    
    context = {
        'flow': flow,
    }
    return render(request, 'flows/flow_detail.html', context)


def flow_statistics(request):
    """Display flow statistics."""
    # Get latest statistics for different periods
    stats_1m = FlowStatistics.objects.filter(period='1m').order_by('-timestamp').first()
    stats_5m = FlowStatistics.objects.filter(period='5m').order_by('-timestamp').first()
    stats_1h = FlowStatistics.objects.filter(period='1h').order_by('-timestamp').first()
    
    context = {
        'stats_1m': stats_1m,
        'stats_5m': stats_5m,
        'stats_1h': stats_1h,
    }
    return render(request, 'flows/flow_statistics.html', context)


def flow_alerts(request):
    """Display flow alerts."""
    alerts = FlowAlert.objects.all()
    
    # Filter by severity
    severity = request.GET.get('severity')
    if severity:
        alerts = alerts.filter(severity=severity)
    
    # Filter by acknowledged status
    acknowledged = request.GET.get('acknowledged')
    if acknowledged is not None:
        alerts = alerts.filter(acknowledged=acknowledged == 'true')
    
    context = {
        'alerts': alerts,
    }
    return render(request, 'flows/flow_alerts.html', context)


def network_interfaces(request):
    """Display network interfaces."""
    interfaces = NetworkInterface.objects.all()
    
    context = {
        'interfaces': interfaces,
    }
    return render(request, 'flows/network_interfaces.html', context)