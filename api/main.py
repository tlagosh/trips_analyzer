# Esto es una api en flask para almacenar datos y hacer consultas sobre viajes
# Autor: Tomás Lagos

from flask import request, jsonify
from clases import Viaje, Health
from database import db
from sqlalchemy.sql import func
from clustering import cluster_por_region, añadir_viaje_a_cluster
import threading
from app import app
from datetime import datetime
import math

@app.route('/')
def index():
    return 'Hello world'

### FUNCIONES AUXILIARES ###
def añadir_viaje_a_cluster(nuevo_viaje):
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

### CRUD VIAJES ###

@app.route('/viajes', methods=['GET'])
def get_viajes():
    viajes = Viaje.query.all()
    viajes = list(map(lambda viaje: viaje.serialize(), viajes))
    return jsonify(viajes)

@app.route('/viajes/<id>', methods=['GET'])
def get_viaje(id):
    viaje = Viaje.query.get(id)
    return jsonify(viaje.serialize())

# post para crear un viaje (Se le asigna automáticamente un id y se le asignan clusters según los viajes que ya existen)
@app.route('/viajes', methods=['POST'])
def create_viaje():
    try:
        nuevo_viaje = Viaje(
            region=request.json['region'],
            origin_lat=request.json['origin_lat'],
            origin_lon=request.json['origin_lon'],
            destination_lat=request.json['destination_lat'],
            destination_lon=request.json['destination_lon'],
            datetime=request.json['datetime'],
            datasource=request.json['datasource'],
            origin_cluster_id=-1,
            destination_cluster_id=-1,
            hour_cluster_id=-1
        )

        db.session.add(nuevo_viaje)
        db.session.commit()

        # clusterizamos el viaje
        añadir_viaje_a_cluster(nuevo_viaje)

    except Exception as e:
        # Si este servicio falla por algún motivo, tenemos que actualizar el healthcheck
        health = Health.query.filter_by(service='data_ingestion').first()
        health.status = 'ERROR'
        db.session.commit()
        return jsonify({'message': 'Error al crear el viaje'}), 500
    
    # Si el servicio funciona correctamente, actualizamos el healthcheck
    health = Health.query.filter_by(service='data_ingestion').first()
    health.status = 'OK'
    db.session.commit()

    return jsonify(nuevo_viaje.serialize())

# post para crear varios viajes a la vez (después de crearlos es necesario usar el endpoint /clusterize para clusterizarlos)
@app.route('/viajes/bulk', methods=['POST'])
def create_viajes():

    viajes = request.json['viajes']
    for viaje in viajes:
        nuevo_viaje = Viaje(
            region=viaje['region'],
            origin_lat=viaje['origin_lat'],
            origin_lon=viaje['origin_lon'],
            destination_lat=viaje['destination_lat'],
            destination_lon=viaje['destination_lon'],
            datetime=viaje['datetime'],
            datasource=viaje['datasource'],
            origin_cluster_id=-1,
            destination_cluster_id=-1,
            hour_cluster_id=-1
        )
        db.session.add(nuevo_viaje)
    db.session.commit()
    return jsonify({'message': 'Viajes creados exitosamente'})


@app.route('/viajes/<id>', methods=['PUT'])
def update_viaje(id):
    viaje = Viaje.query.get(id)
    viaje.region = request.json['region']
    viaje.origin_lat = request.json['origin_lat']
    viaje.origin_lon = request.json['origin_lon']
    viaje.destination_lat = request.json['destination_lat']
    viaje.destination_lon = request.json['destination_lon']
    datetime = request.json['datetime']
    viaje.datetime = datetime
    viaje.datasource = request.json['datasource']
    db.session.commit()
    return jsonify(viaje.serialize())


@app.route('/viajes/<id>', methods=['DELETE']) 
def delete_viaje(id):
    viaje = Viaje.query.get(id)
    db.session.delete(viaje)
    db.session.commit()
    return jsonify(viaje.serialize())

### SERVICIOS ###

# servicio que devuelve el promedio semanal de la cantidad de viajes para un área definida por un bounding box y la región
@app.route('/weekmean', methods=['GET'])
def get_week_mean():

    try:
        max_lat = request.json['max_lat']
        min_lat = request.json['min_lat']
        max_lon = request.json['max_lon']
        min_lon = request.json['min_lon']
        region = request.json['region']
        min_date = request.json['min_date']
        max_date = request.json['max_date']

        query = Viaje.query
        
        if region:
            query = query.filter(Viaje.region == region) # Aplica el filtro por región si se proporciona
        
        if max_lat and min_lat and max_lon and min_lon: # Aplica el filtro por bounding box si se proporciona
            query = query.filter(Viaje.origin_lat >= min_lat) \
                .filter(Viaje.origin_lat <= max_lat) \
                .filter(Viaje.origin_lon >= min_lon) \
                .filter(Viaje.origin_lon <= max_lon)
            
            query = query.filter(Viaje.destination_lat >= min_lat) \
                .filter(Viaje.destination_lat <= max_lat) \
                .filter(Viaje.destination_lon >= min_lon) \
                .filter(Viaje.destination_lon <= max_lon)
            
        cantidad_viajes = len(query.all())

        # Calculamos la cantidad de semanas entre las fechas
        cantidad_semanas = (datetime.strptime(max_date, '%Y-%m-%d %H:%M:%S') - datetime.strptime(min_date, '%Y-%m-%d %H:%M:%S')).days / 7

        # Calculamos el promedio semanal
        promedio_semanal = cantidad_viajes / cantidad_semanas
        
    except Exception as e:
        # Si este servicio falla por algún motivo, tenemos que actualizar el healthcheck
        health = Health.query.filter_by(service='data_ingestion').first()
        health.status = 'ERROR'
        db.session.commit()
        return jsonify({'message': 'Error al calcular el promedio semanal'}), 500
    
    # Si el servicio funciona correctamente, actualizamos el healthcheck
    health = Health.query.filter_by(service='data_ingestion').first()
    health.status = 'OK'
    db.session.commit()
    
    return jsonify({'week_mean': promedio_semanal})

# Endpoint actualizar los clusters de los viajes
@app.route('/clusterize', methods=['PUT'])
def clustering():

    try:
        viajes = db.session.query(Viaje).all()

        ## CLUSTERING ##
        # El clustering será por origen, destino y hora del día en cada región.
        # El objetivo es generar grupos de viajes que tengan características similares para cada región.
        # Para el clustering usaremos DBSCAN, que es un algoritmo de clustering que no requiere que se le especifique la cantidad de clusters.
        # https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html

        regiones_unicas = set([viaje.region for viaje in viajes])

        clusters_usados_origen = 0
        clusters_usados_destino = 0
        clusters_usados_hora = 0

        for region in regiones_unicas:

            viajes_region = [viaje for viaje in viajes if viaje.region == region]

            # Usamos threads para que el clustering sea más rápido
            cluster_por_region(clusters_usados_origen, clusters_usados_destino, clusters_usados_hora, region, viajes_region)

            clusters_usados_origen += 10000000
            clusters_usados_destino += 10000000
            clusters_usados_hora += 10000000
        
        print('Clustering terminado para todas las regiones')
        db.session.commit()

    except Exception as e:
        # Si este servicio falla por algún motivo, tenemos que actualizar el healthcheck
        health = Health.query.filter_by(service='clusterize').first()
        health.status = 'ERROR'
        db.session.commit()
        return jsonify({'message': 'Error al realizar el clustering'}), 500
    
    # Si el servicio funciona correctamente, actualizamos el healthcheck
    health = Health.query.filter_by(service='clusterize').first()
    health.status = 'OK'
    db.session.commit()

    return jsonify({'message': 'Clustering realizado exitosamente'})

# Endpoint para obtener el estado de la ingesta de datos
@app.route('/health', methods=['GET'])
def health():

    service = request.json['servicio']

    if service in ['data_ingestion', 'clusterize', 'weekmean']:
        health = db.session.query(Health).filter(Health.service == service).first()
        return jsonify(health.serialize())
    else:
        return jsonify({'message': 'Servicio no encontrado'}), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
