package _int.nato.ncia.ginslib;

import static _int.nato.ncia.ginslib.GINS_T09.MAX_TIME_TAG;
import java.time.Duration;

/**
 *
 * @author mike
 */
public class GINS_T27 extends GINSMessage {    
    protected int reserved_1;
    protected Duration timeOfValidityOfPosition;
    
    protected boolean insValid;
    protected boolean latLongValid;
    protected boolean altitudeValid;
    protected boolean horizontalVelocityValid;    
    protected boolean headingValid;
    protected boolean pitchRollValid;
    protected boolean wanderAngleValid;
    protected boolean verticalVelocityValid;
    
    protected boolean alignComplete;
    protected boolean egi;
    
    protected double latitude;
    protected double longitude;
    protected double altitude; //ft
  
    protected int estimatedHorizontalError; //ft
    protected int estimatedVerticalError; //ft
  
    protected Duration timeOfTransmission;
    protected Duration timeOfValidity;

    protected Duration velocityTimeTag;
    
    protected double alignmentQuality; //DM/hr
    
    protected double eastVelocity; // ft/sec
    protected double northVelocity; // ft/sec
    protected double upVelocity; // ft/sec
    
    protected int reserved_2;
    protected int reserved_3;
    
    protected double trueHeading;
    protected double pitch;
    protected double roll;
        
    volatile Duration positionAge;
    volatile Duration velocityAge;
    volatile Duration age;

    private GINS_T27(short[] wd) {
        super("T-27");
        reserved_1=wd[0];
        
        timeOfValidityOfPosition = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[1])*64*1000L);
        
        insValid = ((wd[2] >> 15) & 0x1) != 0;
        latLongValid = ((wd[2] >> 14) & 0x1) != 0;
        altitudeValid = ((wd[2] >> 13) & 0x1) != 0;
        horizontalVelocityValid = ((wd[2] >> 12) & 0x1) != 0;
        headingValid = ((wd[2] >> 11) & 0x1) != 0;
        pitchRollValid = ((wd[2] >> 10) & 0x1) != 0;
        wanderAngleValid = ((wd[2] >> 9) & 0x1) != 0;
        verticalVelocityValid = ((wd[2] >> 8) & 0x1) != 0;
        
        alignComplete=((wd[3] >> 14) & 0x1) != 0;
        egi=((wd[3] >> 12) & 0x1) != 0;
      
        latitude = GINSDecoder.toSigned32(wd[4], wd[5]) * Math.pow(2.0, -31.0) * 180.0;        
        longitude = GINSDecoder.toSigned32(wd[6], wd[7]) * Math.pow(2.0, -31.0) * 180.0;        
//        altitude = GINSDecoder.toSigned32(wd[8], wd[9]) * (Math.pow(2.0, -15.0)); // seems more correct
        altitude = GINSDecoder.toSigned32(wd[8], wd[9]) * (Math.pow(2.0, -14.0)); //from ICD
        
        estimatedHorizontalError = GINSDecoder.toSigned32(wd[10]);
        estimatedVerticalError = GINSDecoder.toSigned32(wd[11]);
        
        timeOfTransmission = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[12])*64*1000L);
        timeOfValidity = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[13])*64*1000L);
        velocityTimeTag = Duration.ofNanos(GINSDecoder.toUnsigned32(wd[14])*64*1000L);

        alignmentQuality = GINSDecoder.toSigned32(wd[15]) * (Math.pow(2.0, -8.0));
        eastVelocity = GINSDecoder.toSigned32(wd[16], wd[17]) * Math.pow(2.0, -20.0) * 180.0;        
        northVelocity = GINSDecoder.toSigned32(wd[18], wd[19]) * Math.pow(2.0, -20.0) * 180.0;        
        upVelocity = GINSDecoder.toSigned32(wd[20], wd[21]) * Math.pow(2.0, -20.0) * 180.0;        

        reserved_2=wd[22];
        reserved_3=wd[23];
        
        trueHeading = GINSDecoder.toSigned32(wd[24], wd[25]) * Math.pow(2.0, -31.0) * 180.0;
        pitch = GINSDecoder.toSigned32(wd[26], wd[27]) * Math.pow(2.0, -32.0) * 180.0;
        roll = GINSDecoder.toSigned32(wd[28], wd[29]) * Math.pow(2.0, -31.0) * 180.0;
        
        int itot=GINSDecoder.toUnsigned32(wd[12]);
        int itopv=GINSDecoder.toUnsigned32(wd[1]);
        if(itopv<=itot) {
            positionAge=Duration.ofNanos((itot-itopv)*64L*1000L);            
        }else{ //ROLLOVER
            positionAge=Duration.ofNanos((MAX_TIME_TAG-itopv+itot)*64L*1000L);                        
        }
        int itovv=GINSDecoder.toUnsigned32(wd[14]);
        if(itovv<=itot) {
            velocityAge=Duration.ofNanos((itot-itovv)*64L*1000L);            
        }else{ //ROLLOVER
            velocityAge=Duration.ofNanos((MAX_TIME_TAG-itovv+itot)*64L*1000L);                        
        }
        int itov=GINSDecoder.toUnsigned32(wd[13]);
        if(itov<=itot) {
            age=Duration.ofNanos((itot-itov)*64L*1000L);            
        }else{ //ROLLOVER
            age=Duration.ofNanos((MAX_TIME_TAG-itov+itot)*64L*1000L);                        
        }
    }
    public static GINS_T27 decode(short[] wd) {
        if(wd.length<30) {
            return null;
        }
        return new GINS_T27(wd);
    }

    @Override
    public String toString() {
        return "GINS_T27{" + "timeOfValidityOfPosition=" + timeOfValidityOfPosition + ", timeOfTransmission=" + timeOfTransmission + ", timeOfValidity=" + timeOfValidity + ", insValid=" + insValid + ", latLongValid=" + latLongValid + ", altitudeValid=" + altitudeValid + ", horizontalVelocityValid=" + horizontalVelocityValid + ", headingValid=" + headingValid + ", pitchRollValid=" + pitchRollValid + ", wanderAngleValid=" + wanderAngleValid + ", verticalVelocityValid=" + verticalVelocityValid + ", alignComplete=" + alignComplete + ", egi=" + egi + ", latitude=" + latitude + ", longitude=" + longitude + ", altitude=" + altitude + ", estimatedHorizontalError=" + estimatedHorizontalError + ", estimatedVerticalError=" + estimatedVerticalError +  ", velocityTimeTag=" + velocityTimeTag + ", alignmentQuality=" + alignmentQuality + ", eastVelocity=" + eastVelocity + ", northVelocity=" + northVelocity + ", upVelocity=" + upVelocity + ", trueHeading=" + trueHeading + ", pitch=" + pitch + ", roll=" + roll + '}';
    }

    public Duration getTimeOfValidityOfPosition() {
        return timeOfValidityOfPosition;
    }

    public boolean isInsValid() {
        return insValid;
    }

    public boolean isLatLongValid() {
        return latLongValid;
    }

    public boolean isAltitudeValid() {
        return altitudeValid;
    }

    public boolean isHorizontalVelocityValid() {
        return horizontalVelocityValid;
    }

    public boolean isHeadingValid() {
        return headingValid;
    }

    public boolean isPitchRollValid() {
        return pitchRollValid;
    }

    public boolean isWanderAngleValid() {
        return wanderAngleValid;
    }

    public boolean isVerticalVelocityValid() {
        return verticalVelocityValid;
    }

    public boolean isAlignComplete() {
        return alignComplete;
    }

    public boolean isEgi() {
        return egi;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public double getAltitude() {
        return altitude;
    }

    public int getEstimatedHorizontalError() {
        return estimatedHorizontalError;
    }

    public int getEstimatedVerticalError() {
        return estimatedVerticalError;
    }

    public Duration getTimeOfTransmission() {
        return timeOfTransmission;
    }

    public Duration getTimeOfValidity() {
        return timeOfValidity;
    }

    public Duration getVelocityTimeTag() {
        return velocityTimeTag;
    }

    public double getAlignmentQuality() {
        return alignmentQuality;
    }

    public double getEastVelocity() {
        return eastVelocity;
    }

    public double getNorthVelocity() {
        return northVelocity;
    }

    public double getUpVelocity() {
        return upVelocity;
    }

    public double getTrueHeading() {
        return trueHeading;
    }

    public double getPitch() {
        return pitch;
    }

    public double getRoll() {
        return roll;
    }

    public Duration getPositionAge() {
        return positionAge;
    }

    public Duration getVelocityAge() {
        return velocityAge;
    }

    public Duration getAge() {
        return age;
    }
      
}
