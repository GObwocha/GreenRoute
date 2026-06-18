from django.db import models
from django.contrib.auth.models import User

class RouteHistory(models.Model):
    """
    Stores every calculated eco-route for analytics and admin dashboard.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="The client who generated this route (if authenticated)")
    # Start location
    start_location_name = models.CharField(max_length=255, null=True, blank=True)
    start_lat = models.FloatField()
    start_lng = models.FloatField()
    
    # End location
    end_location_name = models.CharField(max_length=255, null=True, blank=True)
    end_lat = models.FloatField()
    end_lng = models.FloatField()
    
    # Route metrics
    distance_km = models.FloatField(default=0.0)
    nodes_traversed = models.IntegerField(default=0)
    
    # Eco metrics (estimated)
    fuel_saved_liters = models.FloatField(default=0.0)  # vs standard route
    co2_prevented_kg = models.FloatField(default=0.0)   # vs standard route
    
    # Metadata
    traffic_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Route Histories"
    
    def __str__(self):
        return f"{self.start_location_name or f'({self.start_lat}, {self.start_lng})'} → {self.end_location_name or f'({self.end_lat}, {self.end_lng})'}"

class SystemSettings(models.Model):
    """
    Singleton model to hold global routing engine configurations.
    """
    traffic_multiplier = models.FloatField(default=10.0, help_text="Penalty applied to road segments with live traffic jams")
    surface_multiplier = models.FloatField(default=5.0, help_text="Penalty applied to unpaved roads")
    restricted_multiplier = models.FloatField(default=100.0, help_text="Penalty applied to restricted access roads")
    base_fuel_consumption = models.FloatField(default=8.0, help_text="Base fuel consumption in Liters per 100km")
    eco_efficiency_gain = models.FloatField(default=20.0, help_text="Percentage of fuel saved on eco routes (%)")
    
    class Meta:
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "Global System Settings"

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class DirectMessage(models.Model):
    """
    Messages between Clients (Partner Organizations) and Admins.
    """
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"

class RoadModifier(models.Model):
    MODIFIER_TYPES = (
        ('closure', 'Road Closed'),
        ('traffic', 'High Traffic'),
    )
    modifier_type = models.CharField(max_length=20, choices=MODIFIER_TYPES)
    lat = models.FloatField()
    lng = models.FloatField()
    radius_meters = models.FloatField(default=50.0) # Area of effect
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_modifier_type_display()} at {self.lat},{self.lng}"
