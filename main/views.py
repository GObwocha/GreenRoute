from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
import secrets
#Libraries for the routing engine
from django.http import JsonResponse
from .apps import MainConfig
import networkx as nx
import osmnx as ox

# Create your views here.
def index(request):
    return render(request, 'index.html')

def client_dashboard(request):
    # This view serves the public interactive Eco-Planner dashboard
    return render(request, 'client_dashboard.html')

def calculate_route(request):
    #1. Safely grab data from URL
    start_lat_raw = request.GET.get('start_lat')
    start_lng_raw = request.GET.get('start_lng')
    end_lat_raw = request.GET.get('end_lat')
    end_lng_raw = request.GET.get('end_lng')

    #ERROR CHECK 1:Did frontend forget a parameter?
    if not all([start_lat_raw, start_lng_raw, end_lat_raw, end_lng_raw]):
        return JsonResponse({
            "status": "error",
            "message": "Missing parameters. Please provide start_lat, start_lng, end_lat and end_lng."
        }, status=400)
    
    #ERROR CHECK 2: Are the corrdinates actual numbers?
    try:
        start_lat = float(start_lat_raw)
        start_lng = float(start_lng_raw)
        end_lat = float(end_lat_raw)
        end_lng = float(end_lng_raw)
    except ValueError:
        return JsonResponse({
            "status": "error",
            "message": "Invlaid coordinates. All parameters must be valid decimal numbers."
        }, status=400)
    
    #Make sure the map is successfully laoded during server boot
    graph = MainConfig.nairobi_graph
    if graph is None:
        return JsonResponse({
            "status": "error",
            "message": "The routing engine is offline or still booting up."
        }, status=503)
    
    #3. Math Engine
    try:
        orig_node = ox.distance.nearest_nodes(graph, start_lng,start_lat)
        dest_node = ox.distance.nearest_nodes(graph, end_lng,end_lat)

        route = nx.shortest_path(graph, orig_node, dest_node, weight='eco_weight')
        route_coords = [{"lat": graph.nodes[node]['y'], "lng": graph.nodes[node]['x']} for node in route]

        return JsonResponse({
            "status": "success",
            "path": route_coords
        })
    
    #ERROR CHECK 3: No physical road connects these points
    except nx.NetworkXNoPath:
        return JsonResponse({
            "status": "error",
            "message": "No drivable route exists between these two points on the current map"
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"An internal routing error occorred: {str(e)}"
            }, status=500)

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_panel(request):
    return render(request, 'admin_panel.html')

def admin_login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Successfully authenticated as {user.username}.")
                return redirect('admin_panel')
            else:
                return render(request, 'admin_login.html', {"error_message": "Account does not have administrator access."})
        else:
            return render(request, 'admin_login.html', {"error_message": "Invalid username or password credentials."})
    return render(request, 'admin_login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_register_user(request):
    if request.method == 'POST':
        new_u = request.POST.get('new_username')
        new_e = request.POST.get('new_email')
        
        if not new_u or not new_e:
            messages.error(request, "Missing username or email parameters.")
            return redirect('admin_panel')
            
        if User.objects.filter(username=new_u).exists():
            messages.error(request, f"Username '{new_u}' is already taken.")
            return redirect('admin_panel')
            
        # Automatically generate a cryptographically secure random password
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        secure_password = "".join(secrets.choice(alphabet) for _ in range(16))
        
        try:
            user = User.objects.create_user(username=new_u, email=new_e, password=secure_password)
            messages.success(request, f"Successfully provisioned account '{new_u}'. Auto-generated Password: {secure_password}")
        except Exception as e:
            messages.error(request, f"Failed to provision user account: {str(e)}")
            
    return redirect('admin_panel')