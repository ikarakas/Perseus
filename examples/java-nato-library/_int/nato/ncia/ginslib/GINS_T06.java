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
public class GINS_T06 extends GINSMessage {

    protected Duration timeOfTransmission;
    protected Duration timeOfValidity;
    protected boolean insAttitudeValid;
    protected boolean platformHeadingValid;
    protected boolean verticalAccelerationValid;
    protected boolean trueHeadingValid;
    protected boolean baroInertialAltitudeValid;
    protected boolean bodyAccelerationValid;
    protected boolean bodyRatesValid;
    protected boolean horizontalVelocityValid;
    protected boolean verticalVelocityValid;
    protected boolean horizontalAccelerationValid;
    protected boolean presentPositionValid;
    protected boolean magneticHeadingValid;

    protected double baroInertialAltitude;
    protected double alignmentQuality; //NM/h
    protected int estimatedHorizontalError; //ft
    protected int estimatedVerticalError; //ft
    protected int navigationTime; //minutes (positive)
    
    public GINS_T06(short[] wd) {
        super("T-06");
        timeOfTransmission = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[0]) * 64 * 1000);
        timeOfValidity = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[1]) * 64 * 1000);
        insAttitudeValid = ((wd[2] >> 15) & 0x1) != 0;
        platformHeadingValid = ((wd[2] >> 13) & 0x1) != 0;
        verticalAccelerationValid = ((wd[2] >> 12) & 0x1) != 0;
        trueHeadingValid = ((wd[2] >> 11) & 0x1) != 0;
        baroInertialAltitudeValid = ((wd[2] >> 10) & 0x1) != 0;
        bodyAccelerationValid = ((wd[2] >> 9) & 0x1) != 0;
        bodyRatesValid = ((wd[2] >> 8) & 0x1) != 0;
        horizontalVelocityValid = ((wd[2] >> 7) & 0x1) != 0;
        verticalVelocityValid = ((wd[2] >> 6) & 0x1) != 0;
        horizontalAccelerationValid = ((wd[2] >> 5) & 0x1) != 0;
        presentPositionValid = ((wd[2] >> 4) & 0x1) != 0;
        magneticHeadingValid = ((wd[2] >> 2) & 0x1) != 0;
        
        baroInertialAltitude = GINSDecoder.toSigned32(wd[11], wd[12]) * (Math.pow(2.0, -14.0));
        
        alignmentQuality = GINSDecoder.toSigned32(wd[21]) * (Math.pow(2.0, -8.0));
        navigationTime=GINSDecoder.toUnsigned32(wd[22]);
        estimatedHorizontalError = GINSDecoder.toSigned32(wd[23]);
        estimatedVerticalError = GINSDecoder.toSigned32(wd[24]);
    }

    public Duration getTimeOfTransmission() {
        return timeOfTransmission;
    }

    public Duration getTimeOfValidity() {
        return timeOfValidity;
    }

    public boolean isInsAttitudeValid() {
        return insAttitudeValid;
    }

    public boolean isPlatformHeadingValid() {
        return platformHeadingValid;
    }

    public boolean isVerticalAccelerationValid() {
        return verticalAccelerationValid;
    }

    public boolean isTrueHeadingValid() {
        return trueHeadingValid;
    }

    public boolean isBaroInertialAltitudeValid() {
        return baroInertialAltitudeValid;
    }

    public boolean isBodyAccelerationValid() {
        return bodyAccelerationValid;
    }

    public boolean isBodyRatesValid() {
        return bodyRatesValid;
    }

    public boolean isHorizontalVelocityValid() {
        return horizontalVelocityValid;
    }

    public boolean isVerticalVelocityValid() {
        return verticalVelocityValid;
    }

    public boolean isHorizontalAccelerationValid() {
        return horizontalAccelerationValid;
    }

    public boolean isPresentPositionValid() {
        return presentPositionValid;
    }

    public boolean isMagneticHeadingValid() {
        return magneticHeadingValid;
    }

    public double getBaroInertialAltitude() {
        return baroInertialAltitude;
    }

    public double getAlignmentQuality() {
        return alignmentQuality;
    }

    public int getEstimatedHorizontalError() {
        return estimatedHorizontalError;
    }

    public int getEstimatedVerticalError() {
        return estimatedVerticalError;
    }

    public int getNavigationTime() {
        return navigationTime;
    }

    
    public static GINS_T06 decode(short[] swords) {
        if(swords.length==32) {
            return new GINS_T06(swords);
        }else{
            return null;
        }
    }

}
