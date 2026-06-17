from django.db import models

class RouteHistory(models.Model):
    """
    Stores every calculated eco-route for analytics and admin dashboard.
    """
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
