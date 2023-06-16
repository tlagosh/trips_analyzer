from flask import Flask
from database import db, db_uri
from clases import Health

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db.init_app(app)

with app.app_context():
    db.create_all()

    # Creamos el healthcheck si no existe
    healthcheck_data_ingestion = Health('data_ingestion', 'OK')
    healthcheck_weekmean = Health('weekmean', 'OK')
    healthcheck_clusterize = Health('clusterize', 'OK')

    if not Health.query.filter_by(service='data_ingestion').first():
        db.session.add(healthcheck_data_ingestion)
    if not Health.query.filter_by(service='weekmean').first():
        db.session.add(healthcheck_weekmean)
    if not Health.query.filter_by(service='clusterize').first():
        db.session.add(healthcheck_clusterize)

    db.session.commit()
