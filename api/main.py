# Esto es una api en flask para almacenar datos y hacer consultas sobre viajes
# Autor: Tomás Lagos

from flask import Flask, request, jsonify
from clases import Viaje
from database import db, db_uri
from sqlalchemy.sql import func

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
    viaje = Viaje(
        region=request.json['region'],
        origin_lat=request.json['origin_lat'],
        origin_lon=request.json['origin_lon'],
        destination_lat=request.json['destination_lat'],
        destination_lon=request.json['destination_lon'],
        datetime=request.json['datetime'],
        datasource=request.json['datasource']
    )
    db.session.add(viaje)
    db.session.commit()
    return jsonify(viaje.serialize())

# post para crear varios viajes a la vez
@app.route('/viajes/bulk', methods=['POST'])
def create_viajes():
    viajes = request.json['viajes']
    for viaje in viajes:
        viaje = Viaje(
            region=viaje['region'],
            origin_lat=viaje['origin_lat'],
            origin_lon=viaje['origin_lon'],
            destination_lat=viaje['destination_lat'],
            destination_lon=viaje['destination_lon'],
            datetime=viaje['datetime'],
            datasource=viaje['datasource']
        )
        db.session.add(viaje)
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
    max_lat = request.json.get('max_lat')
    min_lat = request.json.get('min_lat')
    max_lon = request.json.get('max_lon')
    min_lon = request.json.get('min_lon')
    region = request.json.get('region')

    query = db.session.query(Viaje, func.date_trunc('week', Viaje.datetime).label('week_start'))
    
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

    result = query.group_by('week_start').all()
    viajes_por_semana = []

    for viaje, week_start in result:
        viajes_por_semana.append({
            'week_start': week_start,
            'viajes_count': len(viaje)
        })

    return jsonify(viajes_por_semana)

if __name__ == '__main__':
    app.run(debug=True)
