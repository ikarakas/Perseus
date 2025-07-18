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
public class GINS_T02 extends GINSMessage {
    protected Duration timeOfTransmission;
    protected Duration timeOfValidity;
    
    protected boolean verticalAccelerationValid;
    protected boolean horizontalVelocityValid;
    protected boolean verticalVelocityValid;
    protected boolean horizontalAccelerationValid;
    protected boolean digitalAltitudeValid;
    
    protected double xVelocity; //ft/sec
    protected double yVelocity; //ft/sec
    protected double verticalVelocity; //ft/sec
    protected double xAcceleration; //ft/sec²
    protected double yAcceleration; //ft/sec²
    protected double verticalAcceleration; //ft/sec²
    protected double rollRate; //deg/sec
    protected double pitchRate; //deg/sec
    protected double yawRate; //deg/sec

    protected double hybridLateralAcceleration; //ft/sec²
    protected double hybridLongitudinalAcceleration; //ft/sec²
    protected double hybridNormalAcceleration; //ft/sec²
    
    protected double lateralAcceleration; //ft/sec²
    protected double longitudinalAcceleration; //ft/sec²
    protected double normalAcceleration; //ft/sec²
    
    protected Duration velocityTimeTag;

    public GINS_T02(short[] wd)  {
       super("T-02");

       timeOfTransmission = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[0])*64*1000);
       timeOfValidity = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[1])*64*1000);
       verticalAccelerationValid=((wd[2]>>>12)&0x1)!=0;
       horizontalVelocityValid=((wd[2]>>>7)&0x1)!=0;
       verticalVelocityValid=((wd[2]>>>6)&0x1)!=0;
       horizontalAccelerationValid=((wd[2]>>>5)&0x1)!=0;
       digitalAltitudeValid=((wd[2]>>>1)&0x1)!=0;
       xVelocity=GINSDecoder.toSigned32(wd[4], wd[5])*Math.pow(2.0, -19);
       yVelocity=GINSDecoder.toSigned32(wd[6], wd[7])*Math.pow(2.0, -19);
       verticalVelocity=GINSDecoder.toSigned32(wd[8])*Math.pow(2.0, -19);
       xAcceleration=GINSDecoder.toSigned32(wd[9])*Math.pow(2.0, -6);
       yAcceleration=GINSDecoder.toSigned32(wd[10])*Math.pow(2.0, -6);
       verticalAcceleration=GINSDecoder.toSigned32(wd[11])*Math.pow(2.0, -6);       
       rollRate=GINSDecoder.toSigned32(wd[12])*Math.pow(2.0, -6);
       pitchRate=GINSDecoder.toSigned32(wd[13])*Math.pow(2.0, -6);
       yawRate=GINSDecoder.toSigned32(wd[14])*Math.pow(2.0, -6);
       velocityTimeTag = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[15])*64*1000);
       hybridLateralAcceleration=GINSDecoder.toSigned32(wd[21])*Math.pow(2.0, -6);
       hybridLongitudinalAcceleration=GINSDecoder.toSigned32(wd[22])*Math.pow(2.0, -6);
       hybridNormalAcceleration=GINSDecoder.toSigned32(wd[23])*Math.pow(2.0, -6);
       lateralAcceleration=GINSDecoder.toSigned32(wd[24])*Math.pow(2.0, -6);
       longitudinalAcceleration=GINSDecoder.toSigned32(wd[25])*Math.pow(2.0, -6);
       normalAcceleration=GINSDecoder.toSigned32(wd[26])*Math.pow(2.0, -6);
       
       int y=10;

    }
    public static GINS_T02 decode(short[] swords) {
        return new GINS_T02(swords);
    }

    public Duration getTimeOfTransmission() {
        return timeOfTransmission;
    }

    public Duration getTimeOfValidity() {
        return timeOfValidity;
    }

    public boolean isVerticalAccelerationValid() {
        return verticalAccelerationValid;
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

    public boolean isDigitalAltitudeValid() {
        return digitalAltitudeValid;
    }

    public double getxVelocity() {
        return xVelocity;
    }

    public double getyVelocity() {
        return yVelocity;
    }

    public double getVerticalVelocity() {
        return verticalVelocity;
    }

    public double getxAcceleration() {
        return xAcceleration;
    }

    public double getyAcceleration() {
        return yAcceleration;
    }

    public double getVerticalAcceleration() {
        return verticalAcceleration;
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

    public double getHybridLateralAcceleration() {
        return hybridLateralAcceleration;
    }

    public double getHybridLongitudinalAcceleration() {
        return hybridLongitudinalAcceleration;
    }

    public double getHybridNormalAcceleration() {
        return hybridNormalAcceleration;
    }

    public double getLateralAcceleration() {
        return lateralAcceleration;
    }

    public double getLongitudinalAcceleration() {
        return longitudinalAcceleration;
    }

    public double getNormalAcceleration() {
        return normalAcceleration;
    }

    public Duration getVelocityTimeTag() {
        return velocityTimeTag;
    }
    
}
