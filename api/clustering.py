from database import db
from clases import Viaje
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from app import app
import math

def cluster_por_region(clusters_usados_origen, clusters_usados_destino, clusters_usados_hora, region, viajes_region):

    print('Iniciando clustering para la región ' + region)

    # Clustering por origen
    cluster_origen(clusters_usados_origen, viajes_region)

    # Clustering por destino
    cluster_destino(clusters_usados_destino, viajes_region)

    # Clustering por hora
    cluster_hora(clusters_usados_hora, viajes_region)

    
    return clusters_usados_origen, clusters_usados_destino, clusters_usados_hora

def cluster_origen(clusters_usados_origen, viajes_region):
    # Clustering por origen
    existing_features = [[round(viaje.origin_lat, 4), round(viaje.origin_lon, 4)] for viaje in viajes_region]
    # Scale the existing_features
    scaler = StandardScaler()
    existing_features = scaler.fit_transform(existing_features)
    # Compute DBSCAN
    dbscan = DBSCAN(eps=0.1, min_samples=2, n_jobs=-1)
    cluster_labels = dbscan.fit_predict(existing_features)
    # Asignamos los clusters a los viajes usando threading para que sea más rápido
    for i in range(len(viajes_region)):
        if int(cluster_labels[i]) == -1:
            viajes_region[i].origin_cluster_id = -1
        else:
            viajes_region[i].origin_cluster_id = int(cluster_labels[i]) + clusters_usados_origen
    clusters_usados_origen += len(set(cluster_labels))

    return clusters_usados_origen

def cluster_destino(clusters_usados_destino, viajes_region):
    # Clustering por destino
    existing_features = [[round(viaje.destination_lat, 4), round(viaje.destination_lon, 4)] for viaje in viajes_region]
    # Scale the existing_features
    scaler = StandardScaler()
    existing_features = scaler.fit_transform(existing_features)
    # Compute DBSCAN
    dbscan = DBSCAN(eps=0.1, min_samples=2, n_jobs=-1)
    cluster_labels = dbscan.fit_predict(existing_features)
    # Asignamos los clusters a los viajes usando threading para que sea más rápido
    for i in range(len(viajes_region)):
        if int(cluster_labels[i]) == -1:
            viajes_region[i].destination_cluster_id = -1
        else:
            viajes_region[i].destination_cluster_id = int(cluster_labels[i]) + clusters_usados_destino
    clusters_usados_destino += len(set(cluster_labels))

    return clusters_usados_destino

def cluster_hora(clusters_usados_hora, viajes_region):
    # Clustering por hora
    existing_features = [[viaje.datetime.hour] for viaje in viajes_region]
    # Scale the existing_features
    scaler = StandardScaler()
    existing_features = scaler.fit_transform(existing_features)
    # Compute DBSCAN
    dbscan = DBSCAN(eps=0.1, min_samples=2, n_jobs=-1)
    cluster_labels = dbscan.fit_predict(existing_features)
    # Asignamos los clusters a los viajes usando threading para que sea más rápido
    for i in range(len(viajes_region)):
        if int(cluster_labels[i]) == -1:
            viajes_region[i].hour_cluster_id = -1
        else:
            viajes_region[i].hour_cluster_id = int(cluster_labels[i]) + clusters_usados_hora
    return clusters_usados_hora

def añadir_viaje_a_cluster(nuevo_viaje):

    with app.app_context():

        viajes = db.session.query(Viaje).all()
        viaje = db.session.query(Viaje).filter(Viaje.id == nuevo_viaje.id).first()

        # Recorremos los viajes y comparamos con el nuevo viaje

        distancia_optima_origin = math.inf
        distancia_optima_destination = math.inf
        distancia_optima_hour = math.inf

        origin_cluster = None
        destination_cluster = None
        hour_cluster = None

        for viaje2 in viajes:
            
            distancia_origin = distancia(float(viaje.origin_lat), float(viaje.origin_lon), float(viaje2.origin_lat), float(viaje2.origin_lon))
            distancia_destination = distancia(float(viaje.destination_lat), float(viaje.destination_lon), float(viaje2.destination_lat), float(viaje2.destination_lon))
            distancia_hour = abs(viaje.datetime.hour - viaje2.datetime.hour)

            if distancia_origin < distancia_optima_origin:
                distancia_optima_origin = distancia_origin
                origin_cluster = viaje2.origin_cluster_id

            if distancia_destination < distancia_optima_destination:
                distancia_optima_destination = distancia_destination
                destination_cluster = viaje2.destination_cluster_id

            if distancia_hour < distancia_optima_hour:
                distancia_optima_hour = distancia_hour
                hour_cluster = viaje2.hour_cluster_id

        viaje.origin_cluster_id = origin_cluster
        viaje.destination_cluster_id = destination_cluster
        viaje.hour_cluster_id = hour_cluster

        db.session.add(viaje)
        db.session.commit()

def distancia(lat1, lon1, lat2, lon2):
    return (lat1-lat2)**2 + (lon1-lon2)**2

