# Standard library imports
from datetime import datetime, timedelta

# Third-party imports
from flask import Flask, jsonify, request, url_for
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.automap import automap_base

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Flask Setup
app = Flask(__name__)

def get_date_query_results(start_date, end_date=None):
    """Query temperature data from the database between given date ranges."""
    session = Session()
    try:
        query = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date)
        if end_date:
            query = query.filter(Measurement.date <= end_date)
        tmin, tavg, tmax = query.one()
        return tmin, tavg, tmax
    finally:
        session.close()

#set the main route
@app.route("/")
def home():
    """Render home page with links to API endpoints."""
    return '''
        <html><head><title>Climate API</title><style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
        a { color: #0077cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        </style></head><body>
        <h1>Welcome to the Climate API</h1><p>Explore the API endpoints:</p><ul>
        <li><a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a> - Get last year's precipitation data</li>
        <li><a href="/api/v1.0/stations">/api/v1.0/stations</a> - List all stations</li>
        <li><a href="/api/v1.0/tobs">/api/v1.0/tobs</a> - Get temperature observations for the most active station last year</li>
        <li><a href="/api/v1.0/2016-01-01">/api/v1.0/YYYY-MM-DD</a> - Get temperature stats from a start date</li>
        <li><a href="/api/v1.0/2016-01-01/2016-12-31">/api/v1.0/YYYY-MM-DD/YYYY-MM-DD</a> - Get temperature stats between two dates</li>
        </ul></body></html>
    '''

#set the precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return precipitation data for the last year from the database."""
    session = Session()
    try:
        max_date = session.query(func.max(Measurement.date)).scalar()
        one_year_ago = datetime.strptime(max_date, '%Y-%m-%d') - timedelta(days=365)
        results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()
        precipitation = {date: prcp for date, prcp in results if prcp is not None}
        return jsonify(precipitation)
    finally:
        session.close()

#set the stations route
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all station identifiers."""
    session = Session()
    try:
        stations = [station[0] for station in session.query(Station.station).all()]
        return jsonify(stations=stations)
    finally:
        session.close()

#set the tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station over the last year."""
    session = Session()
    try:
        active_station = 'USC00519281'
        max_date = session.query(func.max(Measurement.date)).filter(Measurement.station == active_station).scalar()
        one_year_ago = datetime.strptime(max_date, '%Y-%m-%d') - timedelta(days=365)
        tobs_data = [{"date": date, "temperature": tobs} for date, tobs in session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= one_year_ago, Measurement.station == active_station).all()]
        return jsonify(tobs_data)
    finally:
        session.close()

#set the start route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    """Return temperature statistics from a start date or between start and end dates."""
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None
    tmin, tavg, tmax = get_date_query_results(start_date, end_date)
    response = {
        "Start Date": start,
        "End Date": end,
        "Minimum Temperature": tmin,
        "Average Temperature": round(tavg, 1),
        "Maximum Temperature": tmax
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)
