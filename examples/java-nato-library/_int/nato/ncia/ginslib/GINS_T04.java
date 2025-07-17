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
public class GINS_T04 extends GINSMessage {
    protected Duration timeOfTransmission;
    protected Duration timeOfValidity;
    
    protected boolean platformHeadingValid;
    protected boolean verticalAccelerationValid;
    protected boolean horizontalAccelerationValid;
    protected boolean trueHeadingValid;
    protected boolean verticalVelocityValid;
    protected boolean horizontalVelocityValid;
    protected boolean presentPositionValid;
    protected boolean magneticHeadingValid;
    protected boolean geoidAltitudeValid;
    protected boolean insAltitudeValid;
    protected boolean bodyAccelerationValid;
    protected boolean bodyRatesValid;
    
    protected double trueHeading_deg;
    protected double platformHeading_deg;
    protected double pitch_deg;
    protected double roll_deg;
    protected int hybridFOM;
    
    protected double eastWestVelocity; //ft/sec
    protected double northSouthVelocity; //ft/sec
    protected double hybridVerticalVelocity; //ft/sec
    protected double hybridAltitude; //ft above mean (=geoid) level
    
    protected double ppLongitude;
    protected double ppLatitude;
    protected double eastWestAcceleration; //ft/sec²
    protected double northSouthAcceleration; //ft/sec²
    protected double verticalAcceleration; //ft/sec²
    protected double alignmentQuality; //NM/hr
    
    protected Duration navigationTime;
    
    protected double estimatedHorizontalError; //feet
    protected double estimatedVerticalError; //feet
    
    protected double rateOfTurn; //deg/sec
    protected double rollRate; //deg/sec
    protected double pitchRate; //deg/sec
    protected double yawRate; //deg/sec

    protected Duration velocityTimeTag;
    protected double magneticHeading_deg;
    
    public GINS_T04(short[] wd)  {
        super("T-04");
       timeOfTransmission = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[0])*64*1000);
       timeOfValidity = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[1])*64*1000);
       insAltitudeValid = ((wd[2]>>15) & 0x1) != 0;
       platformHeadingValid = ((wd[2]>>13) & 0x1) != 0;
       verticalAccelerationValid = ((wd[2]>>12) & 0x1) != 0;
       trueHeadingValid = ((wd[2]>>11) & 0x1) != 0;
       geoidAltitudeValid = ((wd[2]>>10) & 0x1) != 0;
       bodyAccelerationValid = ((wd[2]>>9) & 0x1) != 0;
       bodyRatesValid = ((wd[2]>>8) & 0x1) != 0;
       horizontalVelocityValid = ((wd[2]>>7) & 0x1) != 0;
       verticalVelocityValid = ((wd[2]>>6) & 0x1) != 0;
       horizontalAccelerationValid = toBoolean(wd[2], 5);
       presentPositionValid = toBoolean(wd[2],4);
       magneticHeadingValid= toBoolean(wd[2],2);
       
       trueHeading_deg=toSignedInt(wd[3])*Math.pow(2.0, -15.0)*180.0;
       platformHeading_deg=toSignedInt(wd[4])*Math.pow(2.0, -15.0)*180.0;
       pitch_deg=toSignedInt(wd[5])*Math.pow(2.0, -15.0)*180.0;
       roll_deg=toSignedInt(wd[6])*Math.pow(2.0, -15.0)*180.0;
       
       hybridFOM=toSignedInt(wd[7]);
       eastWestVelocity=toSignedInt(wd[8])*Math.pow(2.0, -3.0);
       northSouthVelocity=toSignedInt(wd[9])*Math.pow(2.0, -3.0);
       hybridVerticalVelocity=toSignedInt(wd[10])*Math.pow(2.0, -3.0);
       hybridAltitude=GINSDecoder.toSigned32(wd[11], wd[12])*Math.pow(2.0, -14.0);
       ppLatitude=GINSDecoder.toSigned32(wd[13], wd[14])*Math.pow(2.0, -31.0)*180.0;
       ppLongitude=GINSDecoder.toSigned32(wd[15], wd[16])*Math.pow(2.0, -31.0)*180.0;
       eastWestAcceleration=GINSDecoder.toSigned32(wd[18])*Math.pow(2.0, -6.0);
       northSouthAcceleration=GINSDecoder.toSigned32(wd[19])*Math.pow(2.0, -6.0);
       verticalAcceleration=GINSDecoder.toSigned32(wd[20])*Math.pow(2.0, -6.0);
       alignmentQuality=GINSDecoder.toSigned32(wd[21])*Math.pow(2.0, -6.0);
       navigationTime=Duration.ofSeconds(GINSDecoder.toUnsigned32(wd[22])*6);
       estimatedHorizontalError=GINSDecoder.toSigned32(wd[23]);
       estimatedVerticalError=GINSDecoder.toSigned32(wd[24]);
       rateOfTurn=GINSDecoder.toSigned32(wd[25])*Math.pow(2.0,-6.0);
       rollRate=GINSDecoder.toSigned32(wd[26])*Math.pow(2.0,-6.0);
       pitchRate=GINSDecoder.toSigned32(wd[27])*Math.pow(2.0,-6.0);
       yawRate=GINSDecoder.toSigned32(wd[28])*Math.pow(2.0,-6.0);
       velocityTimeTag = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[30])*64*1000);
       magneticHeading_deg=toSignedInt(wd[31])*Math.pow(2.0, -15.0)*180.0;
       int y=10;
    }
    public static GINS_T04 decode(short[] swords) {
        return new GINS_T04(swords);
    }

    public Duration getTimeOfTransmission() {
        return timeOfTransmission;
    }

    public Duration getTimeOfValidity() {
        return timeOfValidity;
    }

    public boolean isPlatformHeadingValid() {
        return platformHeadingValid;
    }

    public boolean isVerticalAccelerationValid() {
        return verticalAccelerationValid;
    }

    public boolean isHorizontalAccelerationValid() {
        return horizontalAccelerationValid;
    }

    public boolean isTrueHeadingValid() {
        return trueHeadingValid;
    }

    public boolean isVerticalVelocityValid() {
        return verticalVelocityValid;
    }

    public boolean isHorizontalVelocityValid() {
        return horizontalVelocityValid;
    }

    public boolean isPresentPositionValid() {
        return presentPositionValid;
    }

    public boolean isMagneticHeadingValid() {
        return magneticHeadingValid;
    }

    public boolean isGeoidAltitudeValid() {
        return geoidAltitudeValid;
    }

    public boolean isInsAltitudeValid() {
        return insAltitudeValid;
    }

    public boolean isBodyAccelerationValid() {
        return bodyAccelerationValid;
    }

    public boolean isBodyRatesValid() {
        return bodyRatesValid;
    }

    public double getTrueHeading_deg() {
        return trueHeading_deg;
    }

    public double getPlatformHeading_deg() {
        return platformHeading_deg;
    }

    public double getPitch_deg() {
        return pitch_deg;
    }

    public double getRoll_deg() {
        return roll_deg;
    }

    public int getHybridFOM() {
        return hybridFOM;
    }

    public double getEastWestVelocity() {
        return eastWestVelocity;
    }

    public double getNorthSouthVelocity() {
        return northSouthVelocity;
    }

    public double getHybridVerticalVelocity() {
        return hybridVerticalVelocity;
    }

    public double getHybridAltitude() {
        return hybridAltitude;
    }

    public double getLongitude() {
        return ppLongitude;
    }

    public double getLatitude() {
        return ppLatitude;
    }

    public double getEastWestAcceleration() {
        return eastWestAcceleration;
    }

    public double getNorthSouthAcceleration() {
        return northSouthAcceleration;
    }

    public double getVerticalAcceleration() {
        return verticalAcceleration;
    }

    public double getAlignmentQuality() {
        return alignmentQuality;
    }

    public Duration getNavigationTime() {
        return navigationTime;
    }

    public double getEstimatedHorizontalError() {
        return estimatedHorizontalError;
    }

    public double getEstimatedVerticalError() {
        return estimatedVerticalError;
    }

    public double getRateOfTurn() {
        return rateOfTurn;
    }

    public double getRollRate() {
        return rollRate;
    }

    public double getPitchRate() {
        return pitchRate;
    }

    public double getYawRate() {
        return yawRate;
    }

    public Duration getVelocityTimeTag() {
        return velocityTimeTag;
    }

    public double getMagneticHeading_deg() {
        return magneticHeading_deg;
    }
    
}
