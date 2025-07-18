/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.fields.TimeStamp;
import csi.util.coordinates.Conversion;
import csi.util.coordinates.Converter;
import csi.util.coordinates.Geodetic;
import csi.util.coordinates.Velocity;
import java.time.Duration;
import java.util.Iterator;
import java.util.LinkedList;
import org.gavaghan.geodesy.Ellipsoid;
import org.gavaghan.geodesy.GeodeticCalculator;
import org.gavaghan.geodesy.GeodeticCurve;
import org.gavaghan.geodesy.GlobalCoordinates;

/**
 *
 * @author mike
 */
public class PositionCalculator {
    protected LinkedList<Report> reportList=new LinkedList<>();
    
    public void update(TimeStamp ts, double lat, double lng, int alt, int pq, int aq) {
        Report rep = new Report(ts, lat, lng, alt, 0.001, 100);
        if(reportList.size()>=8) {
            reportList.removeFirst();
        }
        reportList.add(rep);       
    }
    public TimeStamp getTimeStamp() {
        if(reportList.isEmpty()) {
            return null;
        }
        return reportList.getLast().timeStamp;        
    }
    public Double getLatitude() {
        if(reportList.isEmpty()) {
            return null;
        }
        return reportList.getLast().lat;
    }
    public Double getLongitude() {
        if(reportList.isEmpty()) {
            return null;
        }
        return reportList.getLast().lng;
    }
    public Double getAltitude() {
        if(reportList.isEmpty()) {
            return null;
        }
        return reportList.getLast().alt;
    }
    public Double getHeading() {
        if(reportList.size()<2) {
            return null;
        }        
        Iterator<Report> ir = reportList.descendingIterator();
        Report rep_1=ir.next();
        Report rep_0=ir.next();
        Duration dt = rep_1.timeStamp.toDuration().minus(rep_0.timeStamp.toDuration());
        
        GlobalCoordinates gc_0 = new GlobalCoordinates(rep_0.lat, rep_0.lng);
        GlobalCoordinates gc_1 = new GlobalCoordinates(rep_1.lat, rep_1.lng);
        GeodeticCalculator gc = new GeodeticCalculator();
        GeodeticCurve gcur = gc.calculateGeodeticCurve(Ellipsoid.WGS84, gc_0, gc_1);
        return gcur.getAzimuth();
    }
    public Double getSpeed_DM_H() {
        if(reportList.size()<2) {
            return null;
        }        
        Iterator<Report> ir = reportList.descendingIterator();
        Report rep_1=ir.next();
        Report rep_0=ir.next();
        Duration dt = rep_1.timeStamp.toDuration().minus(rep_0.timeStamp.toDuration());
        GlobalCoordinates gc_0 = new GlobalCoordinates(rep_0.lat, rep_0.lng);
        GlobalCoordinates gc_1 = new GlobalCoordinates(rep_1.lat, rep_1.lng);
        GeodeticCalculator gc = new GeodeticCalculator();
        GeodeticCurve gcur = gc.calculateGeodeticCurve(Ellipsoid.WGS84, gc_0, gc_1);
        double dist = gcur.getEllipsoidalDistance();
        double dist_m_ms = dist/dt.toMillis();
        double val = Converter.meterToDm(dist_m_ms*3600000.0);
        return val;        
    }
    public class Report {
        protected TimeStamp timeStamp;
        protected double lat;
        protected double lng;
        protected double alt;
        protected double sigmaPos;
        protected double sigmaAlt;

        public Report(TimeStamp ts, double lat, double lng, int alt, double sigmaPos, double sigmaAlt) {
            this.timeStamp = ts;
            this.lat = lat;
            this.lng = lng;
            this.alt = alt;
            this.sigmaPos = sigmaPos;
            this.sigmaAlt = sigmaAlt;
        }
        
    }
}
