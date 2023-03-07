import numpy as np
import re
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists  

from flask import Flask, jsonify

#Setup DB
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

#use Base to reflect DB and reflect tables
Base = automap_base()
Base.prepare(engine, reflect=True)

#Save references
Measurement = Base.classes.measurement
Station = Base.classes.station

#Set up Flask

app = Flask(__name__)

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start (enter as YYYY-MM-DD)<br/>"
        f"/api/v1.0/start/end (enter as YYYY-MM-DD/YYYY-MM-DD)"

    )
#Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    session=Session(engine)
    results=(session.query(Measurement.date, Measurement.tobs)
             .order_by(Measurement.date))
    #Create a dictionary
    prec_tobs= []
    for each_row in results:
        dt_dict = {}
        dt_dict["date"] = each_row.date
        dt_dict["tobs"] = each_row.tobs
        prec_tobs.append(dt_dict)
    
    return jsonify(prec_tobs)

#Return the JSON representation of your dictionary.
@app.route("/api/v1.0/stations")
def stations():
    session=Session(engine)
    #Query the stations
    results=session.query(Station.name).all()
    #make into normal list
    details=list(np.ravel(results))
    
    return jsonify(details)

#Query the dates and temperature observations of the most-active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    session=Session(engine)
    #Query measurements from latest date and calculate start date
    earliest_date=(session.query(Measurement.date)
                          .order_by(Measurement.date
                          .desc())
                          .first())
    earliest_date_str= str(earliest_date)
    earliest_date_str=re.sub("'|,","",earliest_date_str)
    earliest_date_obj=dt.datetime.strptime(earliest_date_str, '(%Y-%m-%d)')
    query_start=dt.date(earliest_date_obj.year, earliest_date_obj.month, earliest_date_obj.day) - dt.timedelta(days=366)
    #Query the list of the names of the stations
    list_station=(session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    station=list_station[0][0]
    print(station)
    
     # Return a list of tobs for the year before the final date
    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
                      .filter(Measurement.date >= earliest_date)
                      .filter(Measurement.station == station)
                      .all())
    tobs_list = []
    for result in results:
        line = {}
        line["Date"] = result[1]
        line["Station"] = result[0]
        line["Temperature"] = int(result[2])
        tobs_list.append(line)
    return jsonify(tobs_list)
        
  # Calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date
@app.route("/api/v1.0/<start>")
def start_only(start):
    session = Session(engine)

    # Date Range (only for help to user in case date gets entered wrong)
    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)
    
    valid_entry = session.query(exists().where(Measurement.date == start)).scalar()
    if valid_entry:
            results = (session.query(func.min(Measurement.tobs)
                                     ,func.avg(Measurement.tobs)
                                     ,func.max(Measurement.tobs))
                       .filter(Measurement.date >= start).all())
    tmin =results[0][0]
    tavg ='{0:.4}'.format(results[0][1])
    tmax =results[0][2]
    
    result_printout =( ['Entered Start Date: ' + start,
                    'The lowest Temperature was: '  + str(tmin) + ' F',
                    'The average Temperature was: ' + str(tavg) + ' F',
                    'The highest Temperature was: ' + str(tmax) + ' F'])
    return jsonify(result_printout)

    return jsonify({"error": f"Input Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

#calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
    @api.route("/api/v1.0/<start>/<end>")
    def start_end(start, end):
        session = Session(engine)
    
    # Date Range (only for help to user in case date gets entered wrong)
    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)

# Check for valid entry of start date
    entry_start = session.query(exists().where(Measurement.date == start)).scalar()
# Check for valid entry of end date
    entry_end = session.query(exists().where(Measurement.date == end)).scalar()

    if entry_start and entry_end:
        results = (session.query(func.min(Measurement.tobs)
                                 ,func.avg(Measurement.tobs)
                                 ,func.max(Measurement.tobs))
                   .filter(Measurement.date >= start)
                   .filter(Measurement.date <= end).all())

    tmin =results[0][0]
    tavg ='{0:.4}'.format(results[0][1])
    tmax =results[0][2]
    
    result_printout =( ['Entered Start Date: ' + start,
                    'Entered End Date: ' + end,
                    'The lowest Temperature was: '  + str(tmin) + ' F',
                    'The average Temperature was: ' + str(tavg) + ' F',
                    'The highest Temperature was: ' + str(tmax) + ' F'])
    return jsonify(result_printout)

    if not valid_entry_start and not valid_entry_end:
        return jsonify({"error": f"Input Start {start} and End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_start:
        return jsonify({"error": f"Input Start Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_end:
        return jsonify({"error": f"Input End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404


if __name__ == '__main__':
    app.run(debug=True)
