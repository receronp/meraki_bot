import settings
from chatbot import *

def get_people_live_count(camera):
    cam_analytics = settings.dashboard.camera.getDeviceCameraAnalyticsLive(
        camera["serial"]
    )
    # print(json.dumps(cam_analytics, indent=2))
    return cam_analytics["zones"]["0"]["person"]


def get_people_timespan_count(camera, timespan=None):
    timespan = timespan * 3600 if timespan != None else 3600
    cam_analytics = settings.dashboard.camera.getDeviceCameraAnalyticsOverview(
        camera["serial"], timespan=timespan
    )
    # print(json.dumps(cam_analytics, indent=2))
    for stat in cam_analytics:
        if stat["zoneId"] == 0:
            return stat["entrances"]

def get_camera(dashboard, network_id, kind, message = None):
    my_devices = dashboard.networks.getNetworkDevices(network_id)
    my_cameras = {}

    if message_contains(kind, ['people']):
        my_cameras = {"people": []}
        for device in my_devices:
            if device["name"] == "Garage Front" or device["name"] == "PasilloEntrada":
                my_cameras["people"].append(device)
    elif message_contains(kind, ['plate']):
        my_cameras = {"plate": []}
        for device in my_devices:
            if device["name"] == "Garage Rear":
                my_cameras["plate"].append(device)
    else:
        my_cameras = {"people": [], "plate": []}
        for device in my_devices:
            if device["name"] == "Garage Front" or device["name"] == "PasilloEntrada":
                my_cameras["people"].append(device)
            elif device["name"] == "Garage Rear":
                my_cameras["plate"].append(device)
    

    return my_cameras
