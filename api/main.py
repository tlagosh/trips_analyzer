# Esto es una api en flask para almacenar datos y hacer consultas sobre viajes
# Autor: Tomás Lagos

from flask import Flask, request, jsonify
from clases import Viaje
from database import db, db_uri
from sqlalchemy.sql import func
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return 'Hello world'

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

@app.route('/viajes', methods=['POST'])
def create_viaje():
    nuevo_viaje = Viaje(
        region=request.json['region'],
        origin_lat=request.json['origin_lat'],
        origin_lon=request.json['origin_lon'],
        destination_lat=request.json['destination_lat'],
        destination_lon=request.json['destination_lon'],
        datetime=request.json['datetime'],
        datasource=request.json['datasource']
    )

    viajes = Viaje.query.all()

    existing_features = [[viaje.origin_lat, viaje.origin_lon, viaje.destination_lat, viaje.destination_lon, viaje.datetime.timestamp()] for viaje in viajes]
    existing_features.append([nuevo_viaje.origin_lat, nuevo_viaje.origin_lon, nuevo_viaje.destination_lat, nuevo_viaje.destination_lon, nuevo_viaje.datetime.timestamp()])

    # Scale the existing_features
    scaler = StandardScaler()
    existing_features = scaler.fit_transform(existing_features)

    # Compute DBSCAN
    dbscan = DBSCAN(eps=0.3, min_samples=10)
    cluster_labels = dbscan.fit_predict(existing_features)

    nuevo_viaje.cluster_id = cluster_labels[-1]

    db.session.add(nuevo_viaje)
    db.session.commit()
    return jsonify(nuevo_viaje.serialize())

# post para crear varios viajes a la vez
@app.route('/viajes/bulk', methods=['POST'])
def create_viajes():
    viajes = request.json['viajes']

    existing_features = [[viaje.origin_lat, viaje.origin_lon, viaje.destination_lat, viaje.destination_lon, viaje.datetime.timestamp()] for viaje in viajes]

    # Scale the existing_features
    scaler = StandardScaler()
    existing_features = scaler.fit_transform(existing_features)

    # Compute DBSCAN
    dbscan = DBSCAN(eps=0.3, min_samples=10)
    cluster_labels = dbscan.fit_predict(existing_features)
    
    for i in range(len(viajes)):
        viajes[i]['cluster_id'] = cluster_labels[i]

    for viaje in viajes:
        nuevo_viaje = Viaje(
            region=viaje['region'],
            origin_lat=viaje['origin_lat'],
            origin_lon=viaje['origin_lon'],
            destination_lat=viaje['destination_lat'],
            destination_lon=viaje['destination_lon'],
            datetime=viaje['datetime'],
            datasource=viaje['datasource'],
            cluster_id=viaje['cluster_id']
        )
        db.session.add(nuevo_viaje)
    db.session.commit()
    return jsonify(viajes)

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
# TODO: agregar filtro por fecha
@app.route('/weekmean', methods=['GET'])
def get_week_mean():
    max_lat = request.json['max_lat']
    min_lat = request.json['min_lat']
    max_lon = request.json['max_lon']
    min_lon = request.json['min_lon']
    region = request.json['region']

    query = Viaje.query
    
    if region:
        query = query.filter(Viaje.region == region)  # Aplica el filtro por región si se proporciona
    
    if max_lat and min_lat and max_lon and min_lon:
        query = query.filter(Viaje.origin_lat >= min_lat) \
            .filter(Viaje.origin_lat <= max_lat) \
            .filter(Viaje.origin_lon >= min_lon) \
            .filter(Viaje.origin_lon <= max_lon)
        
        query = query.filter(Viaje.destination_lat >= min_lat) \
            .filter(Viaje.destination_lat <= max_lat) \
            .filter(Viaje.destination_lon >= min_lon) \
            .filter(Viaje.destination_lon <= max_lon)
        
    query = query.with_entities(func.date_trunc('week', Viaje.datetime).label('week'), func.count(Viaje.id).label('count')) \
        .group_by('week') \
        .order_by('week')
    
    return jsonify(list(map(lambda row: {'week': row.week, 'count': row.count}, query.all())))

if __name__ == '__main__':
    app.run(debug=True)
