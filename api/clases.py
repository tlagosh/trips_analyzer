from sqlalchemy import Column, Integer, String, Float, DateTime
from database import db

# Viaje: region,origin_coord,destination_coord,datetime,datasource

class Viaje(db.Model):

    __tablename__ = 'viajes'

    id = Column(Integer, primary_key=True)
    region = Column(String)
    origin_lat = Column(Float)
    origin_lon = Column(Float)
    destination_lat = Column(Float)
    destination_lon = Column(Float)
    datetime = Column(DateTime)
    datasource = Column(String)
    origin_cluster_id = Column(Integer)
    destination_cluster_id = Column(Integer)
    hour_cluster_id = Column(Integer)

    def __init__(self, region, origin_lat, origin_lon, destination_lat, destination_lon, datetime, datasource, origin_cluster_id, destination_cluster_id, hour_cluster_id):
        self.region = region
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.destination_lat = destination_lat
        self.destination_lon = destination_lon
        self.datetime = datetime
        self.datasource = datasource
        self.origin_cluster_id = origin_cluster_id
        self.destination_cluster_id = destination_cluster_id
        self.hour_cluster_id = hour_cluster_id


    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'id': self.id,
            'region': self.region,
            'origin_lat': self.origin_lat,
            'origin_lon': self.origin_lon,
            'destination_lat': self.destination_lat,
            'destination_lon': self.destination_lon,
            'datetime': self.datetime,
            'datasource': self.datasource,
            'origin_cluster_id': self.origin_cluster_id,
            'destination_cluster_id': self.destination_cluster_id,
            'hour_cluster_id': self.hour_cluster_id
        }

# Implementamos la clase Health para verificar el estado de la API y sus servicios
class Health(db.Model):

    __tablename__ = 'health'

    id = Column(Integer, primary_key=True)
    service = Column(String)
    status = Column(String)

    def __init__(self, service, status):
        self.status = status
        self.service = service

    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'id': self.id,
            'service': self.service,
            'status': self.status
        }