/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import java.time.Duration;

/**
 *
 * @author mike
 */
public class GINS_T09 extends GINSMessage {

    boolean navValid;
    boolean utcValid;
    int cr;
    int gps_filter_mode;
    Duration timeOfTransmission; //[0s..[2.x s
    Duration timeOfValidity; //[0s..[2.x s
    double latitude; //deg
    double longitude; //deg
    int gpsAltitude; //ft
    int altitudeDifference; //ft
/*
geoid
[geodesy] A hypothetical surface representing the form the earth’s oceans would take if there were no land and the water were free to respond to the earth’s gravitational and centrifugal forces. The resulting geoid is irregular and varies from a perfect sphere by as much as 75 meters above and 100 meters below its surface.    geoid-ellipsoid separation

geoid-ellipsoid separation
[geodesy] The distance from the surface of an ellipsoid to the surface of the geoid, measured along a line perpendicular to the ellipsoid. The separation is positive if the geoid lies above the ellipsoid, negative if it lies below.
*/
    double gpsEastVelocity; //ft/sec
    double gpsNorthVelocity; //ft/sec
    double gpsVerticalVelocity; //ft/sec
    int gpsFOM; //coded
    int estimatedHorizontalError; //ft
    int estimatedVerticalError; //ft
    double utcSecondsOfDay;
    Duration utcTimeOfDay;
    
    volatile Duration age;
    
    public static GINS_T09 decode(short[] words) {
        if(words.length>=27) {
            return new GINS_T09(words);
        }else{
            return null;
        }
    }
    protected static final int MAX_TIME_TAG=0x7fff;
    
    private GINS_T09(short[] wd) {
        super("T-09");
        navValid = ((wd[0] >> 15) & 0x1) != 0;
        cr = (wd[0] >> 14) & 0x3;
        utcValid = ((wd[0] >> 7) & 0x1) != 0;
        gps_filter_mode = (wd[0] >> 1) & 0x3;
        timeOfTransmission = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[1])*64*1000L);
        timeOfValidity = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[2])*64*1000L);
        latitude = GINSDecoder.toSigned32(wd[4], wd[5]) * Math.pow(2.0, -31.0) * 180.0;
        longitude = GINSDecoder.toSigned32(wd[6], wd[7]) * Math.pow(2.0, -31.0) * 180.0;
        gpsAltitude = GINSDecoder.toSigned32(wd[8]) * 4;
        altitudeDifference = GINSDecoder.toSigned32(wd[9]);
        gpsEastVelocity = GINSDecoder.toSigned32(wd[10], wd[11]) * Math.pow(2.0, -20.0);
        gpsNorthVelocity = GINSDecoder.toSigned32(wd[12], wd[13]) * Math.pow(2.0, -20.0);
        gpsVerticalVelocity = GINSDecoder.toSigned32(wd[14], wd[15]) * Math.pow(2.0, -20.0);
        gpsFOM = wd[16] & 0xf;
                
        estimatedHorizontalError = GINSDecoder.toSigned32(wd[17]);
        estimatedVerticalError = GINSDecoder.toSigned32(wd[18]);
        utcSecondsOfDay = GINSDecoder.toSigned32(wd[20], wd[21]) * (Math.pow(2.0, -14.0));
        utcTimeOfDay = Duration.ofNanos((long)(utcSecondsOfDay*1_000_000_000.0));
        
        int itot=GINSDecoder.toUnsigned32(wd[1]);
        int itov=GINSDecoder.toUnsigned32(wd[2]);
        if(itov<=itot) {
            age=Duration.ofNanos((itot-itov)*64L*1000L);            
        }else{ //ROLLOVER
            age=Duration.ofNanos((MAX_TIME_TAG-itov+itot)*64L*1000L);                        
        }
        
    }

    public Duration getTimeOfTransmission() {
        return timeOfTransmission;
    }

    public Duration getTimeOfValidity() {
        return timeOfValidity;
    }
    
    public String toText() {
        return utcTimeOfDay + ";" + timeOfValidity + ";" + timeOfTransmission + ";lat=" + latitude + ",lng=" + longitude + ";" + gpsAltitude;
    }

    public boolean isNavValid() {
        return navValid;
    }

    public boolean isUTCValid() {
        return utcValid;
    }

    public Duration getUTCTimeOfDay() {
        return utcTimeOfDay;
    }

    public Duration getAge() {
        return age;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public int getGpsAltitude() {
        return gpsAltitude;
    }

    public int getGpsFOM() {
        return gpsFOM;
    }

    public int getEstimatedHorizontalError() {
        return estimatedHorizontalError;
    }

    public int getEstimatedVerticalError() {
        return estimatedVerticalError;
    }
    
    @Override
    public String toString() {
        return "GINS_T09{" + "navValid=" + navValid + ", utcValid=" + utcValid + ", cr=" + cr + ", gps_filter_mode=" + gps_filter_mode + ", timeOfTransmission=" + timeOfTransmission + ", timeOfValidity=" + timeOfValidity + ", age=" +age +", latitude=" + latitude + ", longitude=" + longitude + ", gpsAltitude=" + gpsAltitude + ", altitudeDifference=" + altitudeDifference + ", gpsEastVelocity=" + gpsEastVelocity + ", gpsNorthVelocity=" + gpsNorthVelocity + ", gpsVerticalVelocity=" + gpsVerticalVelocity + ", gpsFOM=" + gpsFOM + ", estimatedHorizontalError=" + estimatedHorizontalError + ", estimatedVerticalError=" + estimatedVerticalError + ", utcSecondsOfDay=" + utcSecondsOfDay + ", utcTimeOfDay=" + utcTimeOfDay + '}';
    }
    
}
