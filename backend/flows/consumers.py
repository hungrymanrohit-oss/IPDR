"""
WebSocket consumers for real-time flow updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import NetworkFlow, FlowStatistics


class FlowConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time network flow updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        
        # Join the flows group
        await self.channel_layer.group_add("flows", self.channel_name)
        
        # Send initial data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the flows group
        await self.channel_layer.group_discard("flows", self.channel_name)
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                # Subscribe to specific flow updates
                flow_id = data.get('flow_id')
                if flow_id:
                    await self.channel_layer.group_add(f"flow_{flow_id}", self.channel_name)
            
            elif message_type == 'unsubscribe':
                # Unsubscribe from specific flow updates
                flow_id = data.get('flow_id')
                if flow_id:
                    await self.channel_layer.group_discard(f"flow_{flow_id}", self.channel_name)
            
            elif message_type == 'get_stats':
                # Send current statistics
                await self.send_statistics()
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def flow_update(self, event):
        """Send flow update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'flow_update',
            'data': event['data']
        }))
    
    async def statistics_update(self, event):
        """Send statistics update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'statistics_update',
            'data': event['data']
        }))
    
    async def alert_update(self, event):
        """Send alert update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'alert_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_recent_flows(self):
        """Get recent network flows."""
        flows = NetworkFlow.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).order_by('-timestamp')[:10]
        
        return [{
            'flow_id': flow.flow_id,
            'src_ip': flow.src_ip,
            'dst_ip': flow.dst_ip,
            'protocol': flow.protocol_name,
            'packets': flow.packets,
            'bytes': flow.bytes,
            'bandwidth_mbps': flow.bandwidth_mbps,
            'timestamp': flow.timestamp.isoformat(),
        } for flow in flows]
    
    @database_sync_to_async
    def get_current_statistics(self):
        """Get current flow statistics."""
        stats = FlowStatistics.objects.filter(
            period='1m',
            timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).order_by('-timestamp').first()
        
        if stats:
            return {
                'total_flows': stats.total_flows,
                'total_packets': stats.total_packets,
                'total_bytes': stats.total_bytes,
                'avg_bandwidth': stats.avg_bandwidth,
                'protocol_distribution': stats.protocol_distribution,
                'top_src_ips': stats.top_src_ips[:5],
                'top_dst_ips': stats.top_dst_ips[:5],
                'timestamp': stats.timestamp.isoformat(),
            }
        return None
    
    async def send_initial_data(self):
        """Send initial data when client connects."""
        flows = await self.get_recent_flows()
        stats = await self.get_current_statistics()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': {
                'recent_flows': flows,
                'statistics': stats,
            }
        }))
    
    async def send_statistics(self):
        """Send current statistics."""
        stats = await self.get_current_statistics()
        
        await self.send(text_data=json.dumps({
            'type': 'statistics',
            'data': stats
        }))


class AlertConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time alert updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        
        # Join the alerts group
        await self.channel_layer.group_add("alerts", self.channel_name)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the alerts group
        await self.channel_layer.group_discard("alerts", self.channel_name)
    
    async def alert_notification(self, event):
        """Send alert notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event['data']
        }))