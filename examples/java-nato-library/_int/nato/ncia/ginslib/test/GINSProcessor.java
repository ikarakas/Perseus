/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.test;

import _int.nato.ncia.ginslib.GINSMessage;
import _int.nato.ncia.ginslib.GINS_T09;
import _int.nato.ncia.ginslib.GINS_T16;
import _int.nato.ncia.ginslib.GINS_T20;
import _int.nato.ncia.ginslib.GINS_T27;
import _int.nato.ncia.natxmlib.clock.SimpleClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import static _int.nato.ncia.natxmlib.clock.SystemClock.UTC;
import fxmlib.fields.AltitudeRef;
import fxmlib.fields.InsAlignmentStatus;
import fxmlib.fields.InsAlignmentType;
import fxmlib.fields.InsType;
import fxmlib.fields.NavMechanization;
import fxmlib.fields.NavSystemInUse;
import fxmlib.fields.TimeTag;
import fxmlib.fields.common.DampingModeEnum;
import fxmlib.fxm.FIM;
import fxmlib.fxm.FIM04;
import fxmlib.fxm.FIM11;
import fxmlib.fxm.FIM30;
import fxmlib.fxm.FIM31;
import java.time.Duration;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public class GINSProcessor {
    protected Instant systemTimeOfLast_T09=null;
    protected Instant utcTimeOfLast_T09=null;
    protected GINS_T09 lastValid_T09=null;
    
    protected Instant timeOfLast_T16=null;
    protected GINS_T16 lastT16;
    
    protected Instant timeOfLast_T20=null;
    protected GINS_T20 lastT20=null;
    
    protected GINS_T27 lastT27=null;
    protected Instant systemTimeOfLast_T27=null;
    
    protected Instant timeOfLastMessage=null;
    protected int gpsTimeFOM = 0;
        
    protected UTCTimeFilter utcTimeFilter = new UTCTimeFilter();
    
    protected Instant now() {
        //return Instant.ofEpochMilli(0).plus(Duration.ofNanos(System.nanoTime()));
        return SystemClock.getInstance().now();
    }
   
    
    protected void onT16(GINS_T16 t16) {
        timeOfLast_T16=now();
        lastT16=t16;
        gpsTimeFOM=t16.getTimeFOM();
    }
    protected void transmitFIM(Instant systemTime, Instant utcTime, FIM fim) {
        System.out.println("#TXFIM;"+systemTime+";"+fim.toString());
    }
    protected void updateINSPosition(Instant systemTime, Instant posTimeUTC, Instant velTimeUTC, GINS_T27 t27) {
        FIM30 fim=new FIM30();
        fim.getAngularMisalignmentCorrectionsValid().setValue(Boolean.FALSE);
        fim.getVelocityCorrectionsValid().setValue(Boolean.FALSE);
        fim.getReportDataType().setValue(Boolean.FALSE);
        fim.getAltitudeValidity().setValue(t27.isAltitudeValid());
        fim.getHorizontalVelocityValid().setValue(t27.isHorizontalVelocityValid());
        fim.getVerticalVelocityValid().setValue(t27.isVerticalVelocityValid());
        fim.getPlatformAzimuthValid().setValue(t27.isHeadingValid());//???
        fim.getRollAndPitchValid().setValue(t27.isPitchRollValid());
        fim.getHeadingValid().setValue(t27.isHeadingValid());
        fim.getLatLonValid().setValue(t27.isLatLongValid());
        fim.getAltitudeRef().setValue(AltitudeRef.BARO_ALTITUDE);
        fim.getInsAlignmentStatus().setValue(t27.isAlignComplete()?InsAlignmentStatus.ALIGNMENT_COMPLETE:InsAlignmentStatus.ALIGNMENT_INCOMPLETE);
        fim.getInsAlignmentType().setValue(InsAlignmentType.GOOD);
        fim.getNavMechanization().setValue(NavMechanization.NORTH_RELATED);
        fim.getInsType().setValue(InsType.GOOD);        
        fim.getNavSystemInUse().setValue(NavSystemInUse.AIDED_INERTIAL);
        fim.getVelocityTimeOfValidity().setCode(toTimeTag(velTimeUTC).getCode());
        fim.getHorizontalPositionUncertainty().setValue(t27.getEstimatedHorizontalError());
        fim.getDrLatitude().setValue(t27.getLatitude());                
        fim.getAltitudeUncertainty().setValue(t27.getEstimatedVerticalError());
        fim.getDrLongitude().setValue(t27.getLongitude());        
        fim.getDrAltitude().setValue(t27.getAltitude());
        fim.getzVelocity().setValue(t27.getUpVelocity());
        fim.getHorizontalVelocityUncertainty().setValue(10.0);
        fim.getxVelocity().setValue(t27.getEastVelocity());
        fim.getVerticalVelocityUncertainty().setValue(10.0);        
        fim.getyVelocity().setValue(t27.getNorthVelocity());
        fim.getDampingMode().setValue(DampingModeEnum.NO_DAMPING);
        fim.getShipNavigation().setValue(Boolean.FALSE);
        fim.getHeading().setValue(t27.getTrueHeading());
        fim.getPitch().setValue(t27.getPitch());
        fim.getRoll().setValue(t27.getRoll());
        transmitFIM(systemTime, posTimeUTC, fim);
    }
    protected void onT27(GINS_T27 t27) {
        systemTimeOfLast_T27=now();
        if(!t27.isInsValid()) {
            lastT27=t27;
            return;
        }
        if (lastT27 != null) {
            if (lastT27.getTimeOfValidity().compareTo(t27.getTimeOfValidity()) != 0) {
                Instant utc = calculateUTC(systemTimeOfLast_T27);
                if (utc != null) {
                    Instant posTime = utc.minus(t27.getPositionAge());
                    Instant velTime = utc.minus(t27.getVelocityAge());
                    updateINSPosition(systemTimeOfLast_T27, posTime, velTime, t27);
                }
            }
        }
        lastT27 = t27;
    }
    protected void onT20(GINS_T20 t20) {
        timeOfLast_T20=now();
        if(lastT20!=null) {
            if(lastT20.getTimeOfYear().compareTo(t20.getTimeOfYear())==0) {
                return;
            }
        }
        lastT20=t20;
        if(lastT16==null) {
            return;
        }       
        Instant utc = lastT16.toStartOfDay().plus(t20.getTimeOfDay());
        
        ZonedDateTime zdt = ZonedDateTime.ofInstant(utc, t20.UTC);        
        FIM04 fim04=new FIM04(t20.getHour(),t20.getMinute(), t20.getSecond(), t20.getDayOfYear(), zdt.getYear(), t20.getTFOM());        
        transmitFIM(timeOfLast_T20, calculateUTC(timeOfLast_T20), fim04);
    }
    public Instant calculateUTC(Instant systemTime) {
        return bestTimeFilter.calculateUTC(systemTime);
    }
    public Duration getUTCOffset() {
        return bestTimeFilter.getOffset();
    }
    protected Map<Integer, Instant> mapLastUTC=new TreeMap<>();
    protected Map<Integer, UTCTimeFilter> mapUTCTimeFilter=new TreeMap<>();
    protected Map<Integer, GINS_T09> mapT09=new TreeMap<>();
    
    protected Instant latestUTC=null;
    protected Instant latestUTC_corrected=null;
    protected Instant latesttUTC_ST=null;
    protected UTCTimeFilter latestTimeFilter=null;
    protected UTCTimeFilter bestTimeFilter=UTCTimeFilter.INVALID;
    
    protected void updateUTC(int src, Instant systemTime, Instant utc, Duration age) {
        Instant utc_corrected=utc.plus(age);
        if(latestUTC!=null) {
            if(latestUTC.compareTo(utc)<0) {
                latestUTC=utc;
                latestUTC_corrected=utc_corrected;
                latesttUTC_ST=systemTime;
            }else{
                return;
            }
        }else{
            latestUTC=utc;
            latesttUTC_ST=systemTime;
            latestUTC_corrected=utc_corrected;
        }
        UTCTimeFilter utf=mapUTCTimeFilter.get(src);
        if(utf==null) {
            utf=new UTCTimeFilter();
            mapUTCTimeFilter.put(src, utf);
        }
        utf.update(utc_corrected, systemTime);
        latestTimeFilter=utf;

        boolean egi1Valid=false;
        boolean egi2Valid=false;
        if(mapUTCTimeFilter.containsKey(10309)) {
            egi1Valid=mapUTCTimeFilter.get(10309).isValid(systemTime);
        }
        if(mapUTCTimeFilter.containsKey(10409)) {
            egi2Valid=mapUTCTimeFilter.get(10409).isValid(systemTime);
        }
        if(egi2Valid) {
            bestTimeFilter=mapUTCTimeFilter.get(10409);            
        }else if(egi1Valid) {
            bestTimeFilter=mapUTCTimeFilter.get(10309);                        
        }else {
            bestTimeFilter=UTCTimeFilter.INVALID;
        }
    }
    
    protected int lastPositionSource=0;
    protected Instant lastPositionUTC=null;
    protected Instant lastPositionST=null;
    protected GINS_T09 lastPositionT09=null;
    
    public static TimeTag toTimeTag(Instant time) {
        ZonedDateTime zdt = ZonedDateTime.ofInstant(time, UTC);
        int nanos=zdt.getNano();
        int millis=(nanos/1_000_000)%1000;
        int micros=(nanos/1_000)%1000;
        TimeTag tt = new TimeTag(zdt.getMinute(), zdt.getSecond(),millis,micros );
        return tt;
    }
    protected void updateGPSPosition(Instant systemTime, Instant utc, GINS_T09 t09) {
        FIM31 fim31=new FIM31();
        fim31.getLatitudeOfFix().setValue(t09.getLatitude());
        fim31.getLongitudeOfFix().setValue(t09.getLongitude());
        fim31.getTimeTag().setCode(toTimeTag(utc).getCode());
        fim31.getAltitudeOfFix().setValue((float)t09.getGpsAltitude());
        double hvar=t09.getEstimatedHorizontalError()*t09.getEstimatedHorizontalError()*Math.PI;
        fim31.getPositionVariance().setValue((float)hvar);
        double avar=t09.getEstimatedHorizontalError()*t09.getEstimatedVerticalError()*Math.PI;
        fim31.getAltitudeVariance().setValue((float)avar);

        lastPositionSource=t09.getSource();
        lastPositionST=systemTime;
        lastPositionUTC=utc;
        lastPositionT09=t09;
        transmitFIM(systemTime, utc, fim31);
    }
    protected GINS_T09 lastT09;
    protected GINS_T09 lastT09_UTC;
    protected GINS_T09 lastT09_GPS;
    
    protected void onT09(GINS_T09 t09) {
        mapT09.put(t09.getSource(), t09);
        lastT09 = t09;
        if(!t09.isUTCValid()) {
            return;
        }
        lastT09_UTC = t09;
        if(t09.isNavValid()) {
            lastT09_GPS=t09;
        }
        if (lastT16 == null) {
            return;
        }
        if(t09.getSource()<10000) {
            return;
        }
        Instant systemTime=now();
        Instant utc = lastT16.toStartOfDay().plus(t09.getUTCTimeOfDay());
        Instant lastUTC=mapLastUTC.get(t09.getSource());
        boolean updated=false;
        if(lastUTC==null) {
            mapLastUTC.put(t09.getSource(), utc);
            return;
        }else{
            if(lastUTC.compareTo(utc)!=0) {
                updateUTC(t09.getSource(),systemTime,utc,t09.getAge());
                mapLastUTC.put(t09.getSource(), utc);       
                updated=true;
            }
        }
        if(!t09.isNavValid()) {
            return;
        }
        if(!updated) {
            return;
        }
        if (t09.getSource() == 10409) {
            updateGPSPosition(systemTime, utc, t09);
        } else {
            if (lastPositionSource == t09.getSource()) {
                updateGPSPosition(systemTime, utc, t09);
            } else {
                if (lastPositionST != null) {
                    Duration positionAge = Duration.between(lastPositionST, systemTime);
                    if (positionAge.toMillis() > 3000) {
                        updateGPSPosition(systemTime, utc, t09);
                    }
                } else {
                    updateGPSPosition(systemTime, utc, t09);
                }
            }
        }
    }
    public void update(GINSMessage gm) {
        if(gm instanceof GINS_T16) {
            onT16((GINS_T16)gm);
        }else if(gm instanceof GINS_T09) {       
            onT09((GINS_T09)gm);
        }else if(gm instanceof GINS_T20) {
            onT20((GINS_T20)gm);
        }else if(gm instanceof GINS_T27) {
            onT27((GINS_T27)gm);
        }           
        timeOfLastMessage=now();
    }
    public void finish() {
        int y=10;
    } 
    public SimpleClock getUTCClock() {
        return UTCCLOCK;
    }
    protected final SimpleClock UTCCLOCK = new SimpleClock() {
        protected final SimpleClock systemClock=SystemClock.getInstance();
        
        @Override
        public Instant now() {
            if(bestTimeFilter!=null) {
                Instant st = systemClock.now();
                return bestTimeFilter.calculateUTC(st);
            }else{
                return null;
            }
        }

        @Override
        public boolean isRunning() {
            if(bestTimeFilter!=null) {
                return bestTimeFilter.isValid(systemClock.now());
            }else{
                return false;
            }
        }
    };
}
